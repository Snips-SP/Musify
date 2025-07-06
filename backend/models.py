from backend.extensions import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

    songs = db.relationship('Song', backref='user', cascade='all, delete-orphan')
    playlists = db.relationship('Playlist', backref='user', cascade='all, delete-orphan')

    def __repr__(self):
        # Change the user representation if necessary
        return f'{self.name}'


class Song(db.Model):
    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    artist = db.Column(db.String, nullable=False)
    # We can insert the file_path later
    file_path = db.Column(db.String, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # many-to-many relation with Playlist
    playlists = db.relationship('Playlist', secondary='playlist_songs', back_populates='songs')


class Playlist(db.Model):
    __tablename__ = 'playlists'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    __table_args__ = (db.UniqueConstraint('name', 'user_id', name='uq_playlist_name_user'),)

    songs = db.relationship('Song', secondary='playlist_songs', back_populates='playlists')


# Association table for many-to-many relationship between Playlists and Songs
playlist_songs = db.Table(
    'playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.id', ondelete='CASCADE'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('songs.id', ondelete='CASCADE'), primary_key=True)
)
