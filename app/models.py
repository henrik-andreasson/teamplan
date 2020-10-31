from hashlib import md5
from time import time
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login
from flask import url_for
import base64
from datetime import datetime, timedelta
import os
# from sqlalchemy.orm import backref, relationship
# from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import uuid


Base = declarative_base()

service_user = db.Table('service_user',
                        db.Column('service_id', db.Integer, db.ForeignKey('service.id')),
                        db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
                        )


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        print("page: %s per_page: %s endpoint %s" % (page, per_page, endpoint))
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


class Service(PaginatedAPIMixin, db.Model):
    __tablename__ = "service"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(140))
    updated = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    color = db.Column(db.String(140))
    users = db.relationship('User', secondary=service_user)
    manager = db.relationship('User', foreign_keys='Service.manager_id')
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    work = db.relationship("Work")

    def __repr__(self):
        return '<Service {}>'.format(self.name)

    def users_dict(self):
        data = {}
        for user in self.users:
            data[user.username] = user.id
        return data

    def from_dict(self, data, new_service=False):
        for field in ['name', 'color']:
            if field in data:
                setattr(self, field, data[field])

    def to_dict(self):
        data = {
            'id': self.id,
            'name': self.name,
            'manager': self.manager_id,
            'color': self.color,
        }
        return data


class User(PaginatedAPIMixin, UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    api_key = db.Column(db.String(32), index=True, unique=True)
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    manual_schedule = db.Column(db.Integer)
    work_percent = db.Column(db.Integer)
    role = db.Column(db.String(140))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

    def get_api_key(self):
        if self.api_key:
            return self.api_key
        self.api_key = str(uuid.uuid4())
        db.session.add(self)
        db.session.commit()
        return self.api_key

    def revoke_api_key(self):
        self.api_key = None
        db.session.add(self)
        db.session.commit()
        return self.api_key

    @staticmethod
    def check_api_key(user, api_key):
        if user is None or user.api_key is None:
            return False
        elif user.api_key == api_key:
            return True
        else:
            return False


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Work(PaginatedAPIMixin, db.Model):
    __tablename__ = "work"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    stop = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    status = db.Column(db.String(140))
    color = db.Column(db.String(140))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    service = db.relationship('Service')

    def __repr__(self):
        return '<Work {}>'.format(self.service_id)

    def to_dict(self):
        data = {
            'id': self.id,
            'start': self.start,
            'stop': self.stop,
            'user_id': self.user_id,
            'service_id': self.service_id,
            'status': self.status,
            '_links': {
                'self': url_for('api.get_work', id=self.id)
            }
        }

        return data

    def from_dict(self, data):
        for field in ['color', 'status']:
            if field in data:
                setattr(self, 'status', data['status'])

        for field in ['start', 'stop']:
            if field in data:
                date = datetime.strptime(data[field], "%Y-%m-%d %H:%M")
                setattr(self, field, date)

        service = None
        if 'service_id' in data:
            service = Service.query.get(data['service_id'])
        elif 'service_name' in data:
            service = Service.query.filter_by(name=data['service_name']).first()
        else:
            return {'msg': "no input for service id or name", 'success': False}

        if service is not None:
            self.service_id = service.id
            self.color = service.color

        if 'user_id' in data:
            user = User.query.get(data['user_id'])
        elif 'user_name' in data:
            user = User.query.filter_by(username=data['user_name']).first()
        else:
            return {'msg': "no input for user id or name", 'success': False}

        if user is not None:
            self.user_id = user.id

        return {'msg': "work created", 'success': True}


class Absence(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    stop = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    status = db.Column(db.String(140))

    def __repr__(self):
        return '<Absence {}>'.format(self.body)


class Oncall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    stop = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    status = db.Column(db.String(140))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    service = db.relationship('Service')
    color = db.Column(db.String(140))

    def __repr__(self):
        return '<Oncall {} {} {}>'.format(self.service, self.start, self.stop)


class NonWorkingDays(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(140))
    start = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    stop = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    color = db.Column(db.String(140))

    def __repr__(self):
        return '<NonWorkingDays {}>'.format(self.name)
