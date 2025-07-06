import random
from flask import Blueprint, request, flash, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit
from sqlalchemy.exc import IntegrityError
from ..extensions import socketio, db
from ..models import Playlist

playlists_bp = Blueprint('playlists', __name__)


@playlists_bp.route('/queue_playlist', methods=['POST'])
def queue_playlist():
    data = request.get_json()

    if 'playlist_id' not in data:
        print(f'Error: Missing playlist id')
        flash(f'Missing playlist id', 'error')
        return jsonify({
            'success': False,
            'message': 'Missing playlist id'
        })
    try:
        playlist_id = int(data['playlist_id'])
    except ValueError:
        print('Error: Invalid playlist id')
        return jsonify({
            'success': False,
            'message': 'Invalid playlist id'
        })

    queued_songs = []

    playlist = Playlist.query.get(playlist_id)
    if playlist is None:
        print('Error: Playlist not found')
        return jsonify({
            'success': False,
            'message': 'Playlist not found'
        })

    songs = playlist.songs

    if len(songs) == 0:
        print('Error: Playlist is empty')
        return jsonify({
            'success': False,
            'message': 'Playlist is empty'
        })

    # Check if we just play the playlist from the beginning or if we need to start with a specific song
    if data.get('song_id', None) is not None:
        try:
            song_id = int(data['song_id'])
        except ValueError:
            print('Error: Invalid song id')
            return jsonify({
                'success': False,
                'message': 'Invalid song id'
            })

        # Play this song first, so we remove it from the rest
        first_song = None
        for song in songs:
            if song.id == song_id:
                # Move first song
                first_song = song
                songs.remove(song)
                break

        # Check if the list has changed (i.e., if a song was removed)
        if first_song is None:
            print('Error: Invalid song id')
            flash('Invalid song id', 'error')
            return jsonify({
                'success': False,
                'message': 'Invalid song id'
            })

        # Add it to the top of the queue
        queued_songs.append({
        'name': first_song.name,
        'artist': first_song.artist,
        'id': first_song.id,
        'file_path': first_song.file_path,
    })

    # Shuffle it if needed
    if data.get('shuffle', False):
        random.shuffle(songs)

    # Add all songs to the queue
    queued_songs.extend([{
        'name': song.name,
        'artist': song.artist,
        'id': song.id,
        'file_path': song.file_path,
    } for song in songs])

    # Store it in the user session
    return jsonify({
        'success': True,
        'song_queue': queued_songs,
        'playlist': playlist.name
    })


@socketio.on('get_playlists')
@login_required
def get_playlists():
    if not current_user.is_authenticated:
        return {'success': False, 'playlists': []}
    # Get user playlists
    user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()

    return {'success': True, 'playlists': [{'id': p.id, 'name': p.name} for p in user_playlists]}


@socketio.on('add_playlist')
@login_required
def add_playlist(data):
    playlist_name = data.get('playlist_name')

    if not playlist_name:
        # Send it only to the sender’s socket
        return {
            'success': False,
            'message': 'Playlist name cannot be empty.'
        }

    try:
        # Create and add a new playlist
        new_playlist = Playlist(name=playlist_name, user_id=current_user.id)
        db.session.add(new_playlist)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return {
            'success': False,
            'message': 'A playlist with this name already exists.'
        }

    # Broadcast to everyone that there is a new playlist (including sender)
    emit('new_playlist',
         {
             'id': new_playlist.id,
             'name': playlist_name,
             'songs': []
         },
         broadcast=True)
    return {
        'success': True,
        'message': 'Playlist added!'
    }


@socketio.on('remove_playlist')
@login_required
def remove_playlist(data):
    playlist_id = data.get('playlist_id')

    if not playlist_id:
        return {
            'success': False,
            'message': 'Playlist id cannot be empty.'
        }
    try:
        playlist_id = int(playlist_id)
    except ValueError:
        return {
            'success': False,
            'message': 'Playlist must be an valid integer.'
        }

    # Check if the user is the owner of the playlist
    if Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first() is None:
        # User does not own the playlist
        return {
            'success': False,
            'message': 'User does not own the playlist.'
        }

    # Find the playlist by ID
    playlist = Playlist.query.get(playlist_id)

    if playlist:
        db.session.delete(playlist)
        db.session.commit()

    # Broadcast to everyone that there is a new playlist (including sender)
    emit('playlist_removed',
         {
             'id': playlist_id
         },
         broadcast=True)
    return {
        'success': True,
        'message': 'Playlist removed!'
    }

@socketio.on('update_playlist_name')
@login_required
def update_playlist_name(data):
    playlist_id = data.get('playlist_id')
    new_name = data.get('new_name')

    if not playlist_id or not new_name:
        return {
            'success': False,
            'message': 'Playlist id or new name cannot be empty.'
        }
    try:
        playlist_id = int(playlist_id)
    except ValueError:
        return {
            'success': False,
            'message': 'Playlist must be an valid integer.'
        }

    # Find the playlist by ID and current user id
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()

    if playlist is None:
        return {
            'success': False,
            'message': 'Playlist is not owned by user.'
        }

    original_name = playlist.name
    playlist.name = new_name

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()

        # Use the broadcast method to change the name to its original form only for the current user
        emit('playlist_name_updated',
             {
                 'id': playlist_id,
                 'new_name': original_name
             })

        # Tell the user what went wrong
        return {
            'success': False,
            'message': 'Playlist with this name already exists.',
        }

    # Broadcast to everyone that a playlist name has been updated
    emit('playlist_name_updated',
         {
             'id': playlist_id,
             'new_name': new_name
         },
         broadcast=True)
    return {
        'success': True,
        'message': 'Playlist updated!'
    }