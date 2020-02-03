from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, SelectMultipleField
from wtforms.fields.html5 import DateField, DateTimeField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User
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


class ServiceForm(FlaskForm):
    name = StringField(_l('name'), validators=[DataRequired()])
    color = StringField(_l('color'), validators=[DataRequired()])
    users = SelectMultipleField(_l('Users'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))

class WorkForm(FlaskForm):
    username = SelectField(_l('Username'))
    service = SelectField(_l('service'), validators=[DataRequired()])
    status = SelectField(_l('Status'), choices=[('assigned', 'Assigned'),
                                                ('unassigned', 'Unassigned'),
                                                ('wants-out', 'Wants out'),
                                                ('needs-out', 'Needs out')])
    start = DateTimeField(_l('Start work'), validators=[DataRequired()],
                          format='%Y-%m-%d %H:%M', default=datetime.now())
    stop = DateTimeField(_l('Stop work'),
                         validators=[DataRequired()], format='%Y-%m-%d %H:%M',
                         default=datetime.now())
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))

class AbsenceForm(FlaskForm):
    username = SelectField(_l('Username'))
    status = SelectField(_l('Status'), choices=[('requested', 'Requested'),
                                                ('approved', 'Approved'),
                                                ('denied', 'Denied')])
    start = DateTimeField(_l('Start absence'), validators=[DataRequired()],
                          format='%Y-%m-%d %H:%M',default=datetime.now())
    stop = DateTimeField(_l('Stop absence'),
                         validators=[DataRequired()], format='%Y-%m-%d %H:%M',
                         default=datetime.now())
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))

class OncallForm(FlaskForm):
    username = SelectField(_l('Username'))
    service = SelectField(_l('service'), validators=[DataRequired()])
    status = SelectField(_l('Status'), choices=[('assigned', 'Assigned'),
                                                ('unassigned', 'Unassigned'),
                                                ('wants-out', 'Wants out'),
                                                ('needs-out', 'Needs out')])
    start = DateTimeField(_l('Start Oncall'), validators=[DataRequired()],
                          format='%Y-%m-%d %H:%M',default=datetime.now())
    stop = DateTimeField(_l('Stop Oncall'),
                         validators=[DataRequired()], format='%Y-%m-%d %H:%M',
                         default=datetime.now())
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))

class NonWorkingDaysForm(FlaskForm):
    name = StringField(_l('name'), validators=[DataRequired()],
                        default="Non Working Day")
    start = DateTimeField(_l('Start Non Working Day'), validators=[DataRequired()],
                          format='%Y-%m-%d %H:%M',default=datetime.now())
    stop = DateTimeField(_l('Stop Non Working Day'), validators=[DataRequired()],
                        format='%Y-%m-%d %H:%M', default=datetime.now())
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))
