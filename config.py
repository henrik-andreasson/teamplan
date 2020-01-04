import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-email@example.com']
    LANGUAGES = ['en', 'es']
    POSTS_PER_PAGE = 25
    ROCKET_ENABLED=os.environ.get('ROCKET_ENABLED') or False
    ROCKET_USER=os.environ.get('ROCKET_USER') or 'teamplan'
    ROCKET_PASS=os.environ.get('ROCKET_PASS') or 'foo123'
    ROCKET_URL=os.environ.get('ROCKET_URL') or 'http://172.17.0.4:3000'
    ROCKET_CHANNEL=os.environ.get('ROCKET_CHANNEL') or 'GENERAL'
    NON_WORKING_DAYS_COLOR=os.environ.get('NON_WORKING_DAYS_COLOR') or "#FF2222"
