from dotenv import load_dotenv
from flask import Flask
import os
from backend.config import DevelopmentConfig
from backend.routes import main_bp
from backend.playlists.routes import playlists_bp
from backend.songs.routes import songs_bp
from backend.users.routes import users_bp
from backend.extensions import login_manager, socketio, db

# Load secret keys into env variables
load_dotenv()


def create_app(config_class=DevelopmentConfig):
    # Check folder structure
    if not (os.path.exists(config_class.TEMPLATE_FOLDER)
            and os.path.exists(config_class.STATIC_FOLDER)
            and os.path.exists(config_class.UPLOAD_FOLDER)):
        raise FileNotFoundError('Folder structure is not set up right.')

    # Create app
    app = Flask(__name__,
                template_folder=config_class.TEMPLATE_FOLDER,
                static_folder=config_class.STATIC_FOLDER
                )
    app.config.from_object(config_class)

    db.init_app(app)
    # Create tables if they dont exist
    with app.app_context():
        db.create_all()

    login_manager.init_app(app)
    login_manager.login_view = 'users.login'

    socketio.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp, url_prefix='')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(playlists_bp, url_prefix='/playlists')
    app.register_blueprint(songs_bp, url_prefix='/songs')

    return app
