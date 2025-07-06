import os


class Config:
    basedir = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'music.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False

    UPLOAD_FOLDER = os.path.join(basedir, '..', 'uploads')
    TEMPLATE_FOLDER = os.path.join(basedir, '..', 'templates')
    STATIC_FOLDER = os.path.join(basedir, '..', 'static')
    TEMP_FOLDER = os.path.join(basedir, '..', 'tmp')
    ALLOWED_EXTENSIONS = {'mp3'}


class DevelopmentConfig(Config):
    DEBUG = False


class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')