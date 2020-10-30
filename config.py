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
    POSTS_PER_PAGE = 25
    LANGUAGES = ['en', 'es']
    ROCKET_ENABLED = os.environ.get('ROCKET_ENABLED') or False
    ROCKET_USER = os.environ.get('ROCKET_USER') or 'teamplan'
    ROCKET_PASS = os.environ.get('ROCKET_PASS') or 'foo123'
    ROCKET_URL = os.environ.get('ROCKET_URL') or 'http://172.17.0.4:3000'
    ROCKET_CHANNEL = os.environ.get('ROCKET_CHANNEL') or 'GENERAL'
    NON_WORKING_DAYS_COLOR = os.environ.get('NON_WORKING_DAYS_COLOR') or "#FF2222"
    ABSENCE_COLOR = os.environ.get('ABSENCE_COLOR') or "#AAAAAA"
    OPEN_REGISTRATION = os.environ.get('OPEN_REGISTRATION') or False
    TEAMPLAN_TZ = os.environ.get('TEAMPLAN_TZ') or "Europe/Stockholm"
    ICAL_REMINDER_MINS = os.environ.get('ICAL_REMINDER_MINS') or "60"
    ICAL_INVITE_FROM = os.environ.get('ICAL_INVITE_FROM') or "schema@localhost"
    ICAL_UID_DOMAIN = os.environ.get('ICAL_UID_DOMAIN') or "localhost"
    DATE_LINK_TO = os.environ.get('DATE_LINK_TO') or "Absence"

# local means dont use CDN
    BOOTSTRAP_SERVE_LOCAL = os.environ.get('BOOTSTRAP_SERVE_LOCAL') or True
