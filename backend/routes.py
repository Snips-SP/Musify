from flask import Blueprint, render_template, send_from_directory, current_app, jsonify
from flask_login import current_user, login_required
from backend.models import Playlist, Song

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    # Fetch all playlists
    playlists = Playlist.query.all()

    user_playlists = []
    if current_user.is_authenticated:
        # Fetch only playlists owned by current_user directly via a query
        user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()

    return render_template('index.html', playlists=playlists, user_playlists=user_playlists)

# Serve all files in uploads and in subfolders of uploads
@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({'success': False, 'message': 'Not allowed'}), 400


@main_bp.route('/library')
@login_required
def library():
    # Get all songs from the current user
    user_songs = Song.query.filter_by(user_id=current_user.id).all()

    # Fetch all playlists the user has and format it usably
    user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()

    return render_template('library.html', user_playlists=user_playlists, user_songs=user_songs)
