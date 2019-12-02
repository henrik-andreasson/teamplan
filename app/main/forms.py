from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms_components import TimeField
from wtforms.fields.html5 import DateTimeField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User, Work, Service
from datetime import datetime, time


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))


class ServiceForm(FlaskForm):
    name = StringField(_l('name'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))


class WorkForm(FlaskForm):
    username = SelectField(_l('Username'))
    service = SelectField(_l('service'), validators=[DataRequired()])
    status = SelectField(_l('Status'), choices=[('assigned', 'Assigned'),
                                                ('unassigned', 'Unassigned'),
                                                ('wants-out', 'Wants out'),
                                                ('needs-out', 'Needs out')])
    date = DateTimeField(_l('Date of work'),
                         validators=[DataRequired()], format='%Y-%m-%d',
                         default=datetime.now())
    start = TimeField(_l('Start of work'),
                         validators=[DataRequired()], format='%H:%M',
                         default=time(8,0))
    stop = TimeField(_l('End of work'),
                         validators=[DataRequired()], format='%H:%M',
                         default=time(12,30))
    submit = SubmitField(_l('Submit'))
