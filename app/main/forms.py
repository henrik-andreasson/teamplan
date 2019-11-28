from flask import request
from flask_wtf import FlaskForm
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.fields.html5 import DateTimeField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User, Work, Service
from datetime import datetime

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

def FindUsers():
    return User.query.filter_by()

def FindServices():
    return Service.query.filter_by()

class WorkForm(FlaskForm):

    username = QuerySelectField(query_factory=FindUsers,
                                allow_blank=True, get_label='username')
    service = QuerySelectField(query_factory=FindServices,
                               allow_blank=True, get_label='name')
    status = SelectField(_l('Status'), choices=[('assigned', 'Assigned'),
                ('unassigned', 'Unassigned'),
                ('wants-out', 'Wants out'),
                ('needs-out', 'Needs out')])
    start = DateTimeField(_l('Start of work'),
                          validators=[DataRequired()], format='%Y-%m-%d %H:%M',
                          default=datetime.now())
    stop = DateTimeField(_l('End of work'),
                         validators=[DataRequired()], format='%Y-%m-%d %H:%M',
                         default=datetime.now())
    submit = SubmitField(_l('Submit'))
