from flask import Blueprint, request, current_app, jsonify
from flask_login import login_required, current_user
import os
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from flask_socketio import emit
from backend.models import Song, Playlist
from backend.extensions import db, socketio


songs_bp = Blueprint('songs', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


# File upload is best handled throw a plain old http post reqeust
@songs_bp.route('/create_song', methods=['POST'])
@login_required
def create_song():
    if 'song_name' not in request.form or not request.form['song_name']:
        print('Error: Missing song_name')
        return jsonify({'success': False, 'message': 'Missing song name'}), 400

    if 'artist' not in request.form or not request.form['artist']:
        print('Error: Missing artist')
        return jsonify({'success': False, 'message': 'Missing artist name'}), 400

    if 'song_file' not in request.files or not request.files['song_file'].filename:
        print('Error: Missing song file')
        return jsonify({'success': False, 'message': 'Missing song file'}), 400

    song_name = request.form['song_name']
    artist = request.form['artist']
    file = request.files['song_file']

    filename = secure_filename(file.filename)

    if not allowed_file(filename):
        print('Error: File type not allowed')
        return jsonify({'success': False, 'message': 'File type not allowed'}), 400

    try:
        # Create the song without a file_path first, including user_id as required
        new_song = Song(name=song_name, artist=artist, file_path=None, user_id=current_user.id)
        db.session.add(new_song)
        db.session.commit()

        # Make the user directory if it doesn't exist
        user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)

        # Get the file extension
        extension = os.path.splitext(file.filename)[1]

        # Create the file_path using the song's ID and the user's directory
        file_path = os.path.join(user_dir, f'{new_song.id}{extension}')
        file.save(file_path)

        # Update the song's relative file_path in the database
        new_song.file_path = os.path.join(os.path.basename(current_app.config['UPLOAD_FOLDER']), str(current_user.id), f'{new_song.id}{extension}')
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        print('Error: Song with this name already exists')
        return jsonify({'success': False, 'message': 'Song with this name already exists'}), 400

    return jsonify({'success': True,
                    'message': 'Song uploaded successfully!',
                    'song': {
                        'id': new_song.id,
                        'name': new_song.name,
                        'artist': new_song.artist
                        }
                    }), 200


@socketio.on('delete_song')
@login_required
def delete_song(data):
    song_id = data.get('song_id')

    if not song_id:
        return {
            'success': False,
            'message': 'Song id cannot be empty.'
        }

    try:
        song_id = int(song_id)
    except ValueError:
        return {
            'success': False,
            'message': 'Song id must be a valid integer.'
        }

    # Check if the song exists and is owned by the current user
    song = Song.query.filter_by(id=song_id, user_id=current_user.id).first()
    if not song:
        return {
            'success': False,
            'message': 'Song not found or user does not own it.'
        }

    # Delete file if it exists
    if song.file_path and os.path.exists(song.file_path):
        try:
            os.remove(song.file_path)
        except Exception as e:
            pass  # Optionally handle/log error

    # Remove song from database
    db.session.delete(song)
    db.session.commit()

    # Broadcast song removal to all clients
    emit('song_removed', {'id': song_id}, broadcast=True)

    return {
        'success': True,
        'message': 'Song removed!'
    }


@socketio.on('delete_song_from_playlist')
@login_required
def delete_song_from_playlist(data):
    song_id = data.get('song_id')
    playlist_id = data.get('playlist_id')

    if song_id is None or playlist_id is None:
        return {
            'success': False,
            'message': 'Song id and playlist id cannot be empty.'
        }

    try:
        song_id = int(song_id)
        playlist_id = int(playlist_id)
    except ValueError:
        return {
            'success': False,
            'message': 'Song id and playlist id must be a valid integer.'
        }

    # Check if the song exists
    song = Song.query.get(song_id)
    if not song:
        return {
            'success': False,
            'message': 'Song not found.'
        }

    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
    if not playlist:
        return {
            'success': False,
            'message': 'playlist not found or user does not own it.'
        }

    # Delete the connection between the two
    playlist.songs.remove(song)
    db.session.commit()

    # Broadcast song removal to all clients
    emit('song_removed_from_playlist', {'song_id': song_id, 'playlist_id': playlist_id}, broadcast=True)

    return {
        'success': True,
        'message': 'Song removed from playlist!'
    }


@socketio.on('add_song_to_playlist')
@login_required
def add_song_to_playlist(data):
    song_id = data.get('song_id')
    playlist_id = data.get('playlist_id')
    if not song_id or not playlist_id:
        return {'success': False, 'message': 'Missing song id or playlist id!'}

    try:
        song_id = int(song_id)
        playlist_id = int(playlist_id)
    except ValueError:
        return {'success': False, 'message': 'Invalid song id or playlist id!'}

    playlist = Playlist.query.get(playlist_id)
    song = Song.query.get(song_id)

    if not playlist or not song:
        return {'success': False, 'message': 'Playlist or song not found!'}

    if song in playlist.songs:
        return {'success': False, 'message': 'Song is already in the playlist!'}

    playlist.songs.append(song)
    db.session.commit()

    emit('new_song_in_playlist',
         {
             'song': {
                 'id': song.id,
                 'name': song.name,
                 'artist': song.artist,
             },
             'playlist_id': playlist_id,
         },
         broadcast=True)
    return {
        'success': True,
        'message': 'Song added to playlist.'
    }

@socketio.on('update_song_name')
@login_required
def update_song_name(data):
    song_id = data.get('song_id')
    new_name = data.get('new_name')

    if not song_id or not new_name:
        return {
            'success': False,
            'message': 'Missing song id or new name.'
        }

    song = Song.query.filter_by(id=song_id, user_id=current_user.id).first()

    if song is None:
        return {
            'success': False,
            'message': 'Song is not owned by user.'
        }

    original_name = song.name
    song.name = new_name

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

        # Use the broadcast method to change the name to its original form only for the current user
        emit('song_name_updated',
             {
                 'song_id': song_id,
                 'new_name': original_name
             })

        # Tell the user what went wrong
        return {
            'success': False,
            'message': 'Song with this name already exists.',
        }

        # Broadcast to everyone that a song name has been updated
    emit('song_name_updated',
         {
             'song_id': song_id,
             'new_name': new_name
         },
         broadcast=True)
    return {
        'success': True,
        'message': 'Song updated!'
    }

@socketio.on('update_song_artist')
@login_required
def update_song_artist(data):
    song_id = data.get('song_id')
    new_artist = data.get('new_artist')

    if not song_id or not new_artist:
        return {
            'success': False,
            'message': 'Missing song id or new artist.'
        }

    song = Song.query.filter_by(id=song_id, user_id=current_user.id).first()

    if song is None:
        return {
            'success': False,
            'message': 'Song is not owned by user.'
        }

    original_artist = song.artist
    song.artist = new_artist

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

        # Use the broadcast method to change the name to its original form only for the current user
        emit('song_artist_updated',
             {
                 'song_id': song_id,
                 'new_artist': original_artist
             })

        # Tell the user what went wrong
        return {
            'success': False,
            'message': 'Something went wrong.',
        }

        # Broadcast to everyone that a song name has been updated
    emit('song_artist_updated',
         {
             'song_id': song_id,
             'new_artist': new_artist
         },
         broadcast=True)
    return {
        'success': True,
        'message': 'Song updated!'
    }