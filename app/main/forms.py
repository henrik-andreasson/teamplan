from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, \
    SelectMultipleField, BooleanField
from wtforms.fields.html5 import DateTimeField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User, Service
from datetime import datetime


class FilterUserServiceForm(FlaskForm):
    service = SelectField(_l('Service'), coerce=int)
    user = SelectField(_l('User'), coerce=int)
    showabsence = BooleanField(_l('Show Absence'))
    submit = SubmitField(_l('Filter List'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service.choices = [(s.id, s.name) for s in Service.query.order_by(Service.name).all()]
        self.service.choices.insert(0, (-1, _l('All')))
        self.user.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
        self.user.choices.insert(0, (-1, _l('All')))


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[Length(min=2, max=40)])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))

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
    users = SelectMultipleField(_l('Users'), coerce=int, render_kw={"size": 20})
    manager = SelectField(_l('Manager'), validators=[DataRequired()], coerce=int)
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))
    delete = SubmitField(_l('Delete'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.users.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
        self.manager.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]


class WorkForm(FlaskForm):
    user = SelectField(_l('Username'), coerce=int)
    service = SelectField(_l('service'), validators=[DataRequired()], coerce=int)
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
    delete = SubmitField(_l('Delete'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
        self.service.choices = [(s.id, s.name) for s in Service.query.order_by(Service.name).all()]


class GenrateMonthWorkForm(FlaskForm):
    service = SelectField(_l('service'), validators=[DataRequired()])
    month = DateTimeField(_l('motnh'), validators=[DataRequired()],
                          format='%Y-%m', default=datetime.now())
    status = SelectField(_l('Status'), choices=[('assigned', 'Assigned'),
                                                ('unassigned', 'Unassigned')])
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))


class AbsenceForm(FlaskForm):
    user = SelectField(_l('Username'), coerce=int)
    status = SelectField(_l('Status'), choices=[('requested', 'Requested'),
                                                ('approved', 'Approved'),
                                                ('denied', 'Denied')])
    start = DateTimeField(_l('Start absence'), validators=[DataRequired()],
                          format='%Y-%m-%d %H:%M', default=datetime.now())
    stop = DateTimeField(_l('Stop absence'),
                         validators=[DataRequired()], format='%Y-%m-%d %H:%M',
                         default=datetime.now())
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))
    delete = SubmitField(_l('Delete'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]


class OncallForm(FlaskForm):
    user = SelectField(_l('Username'), coerce=int)
    service = SelectField(_l('service'), coerce=int, validators=[DataRequired()])
    status = SelectField(_l('Status'), choices=[('assigned', 'Assigned'),
                                                ('unassigned', 'Unassigned'),
                                                ('wants-out', 'Wants out'),
                                                ('needs-out', 'Needs out')])
    start = DateTimeField(_l('Start Oncall'), validators=[DataRequired()],
                          format='%Y-%m-%d %H:%M', default=datetime.now())
    stop = DateTimeField(_l('Stop Oncall'),
                         validators=[DataRequired()], format='%Y-%m-%d %H:%M',
                         default=datetime.now())
    absenceday = SelectField(_l('Add absence day'),
                             choices=[(0, _l('None')),
                                      (1, _l('Monday')),
                                      (2, _l('Tuseday')),
                                      (3, _l('Wednesday')),
                                      (4, _l('Thursday')),
                                      (5, _l('Friday'))],
                             default=5, coerce=int)
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))
    delete = SubmitField(_l('Delete'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user.choices = [(u.id, u.username) for u in User.query.order_by(User.username).all()]
        self.service.choices = [(s.id, s.name) for s in Service.query.order_by(Service.name).all()]


class GenrateMonthOncallForm(FlaskForm):
    service = SelectField(_l('service'), validators=[DataRequired()])
    month = DateTimeField(_l('motnh'), validators=[DataRequired()],
                          format='%Y-%m', default=datetime.now())
    status = SelectField(_l('Status'), choices=[('assigned', 'Assigned'),
                                                ('unassigned', 'Unassigned')])
    oncallstartday = SelectField(_l('Oncall - Start day'),
                                 choices=[(0, _l('None')),
                                          (1, _l('Monday')),
                                          (2, _l('Tuseday')),
                                          (3, _l('Wednesday')),
                                          (4, _l('Thursday')),
                                          (5, _l('Friday'))],
                                 default=1, coerce=int)
    oncallabsenceday = SelectField(_l('Oncall - Add absence day'),
                                   choices=[(0, _l('None')),
                                            (1, _l('Monday')),
                                            (2, _l('Tuseday')),
                                            (3, _l('Wednesday')),
                                            (4, _l('Thursday')),
                                            (5, _l('Friday'))],
                                   default=5, coerce=int)
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))


class NonWorkingDaysForm(FlaskForm):
    name = StringField(_l('name'),
                       validators=[DataRequired()], default="Non Working Day")
    start = DateTimeField(_l('Start Non Working Day'),
                          validators=[DataRequired()],
                          format='%Y-%m-%d %H:%M', default=datetime.now())
    stop = DateTimeField(_l('Stop Non Working Day'),
                         validators=[DataRequired()],
                         format='%Y-%m-%d %H:%M', default=datetime.now())
    submit = SubmitField(_l('Submit'))
    cancel = SubmitField(_l('Cancel'))
    delete = SubmitField(_l('Delete'))
