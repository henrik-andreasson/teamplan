from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_babel import _, lazy_gettext as _l
from app.models import User


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    manual_schedule = SelectField(_l('Manually Schedule'),
                                  choices=[('1', 'Yes'), (0, 'No')],
                                  coerce=int, default=0)
    work_percent = StringField(_l('Work Percent'), default=100)
    role = SelectField(_l('Role'), choices=[('user', 'User'),
                                            ('admin', 'Admin')])

    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))


class ChangePasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'),
                              validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Change Password'))


class AdminChangePasswordForm(FlaskForm):
    username = SelectField(_l('User'), coerce=int)
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'),
                              validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Change Password'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username.choices = [(u.id, u.username)
                                 for u in User.query.order_by(User.username).all()]
        self.username.choices.insert(0, (-1, _l('- Select -')))


class AdminSelecteUserForm(FlaskForm):
    username = SelectField(_l('User'), coerce=int)
    submit = SubmitField(_l('Select'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username.choices = [(u.id, u.username)
                                 for u in User.query.order_by(User.username).all()]
        self.username.choices.insert(0, (-1, _l('- Select -')))


class AdminUpdateUserForm(FlaskForm):
    username = SelectField(_l('User'), coerce=int)
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    manual_schedule = SelectField(_l('Manually Schedule'),
                                  choices=[('1', 'Yes'), (0, 'No')],
                                  coerce=int, default=0)
    work_percent = StringField(_l('Work Percent'), default=100)
    role = SelectField(_l('Role'), choices=[('user', 'User'),
                                            ('admin', 'Admin')])

    submit = SubmitField(_l('Register'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username.choices = [(u.id, u.username)
                                 for u in User.query.order_by(User.username).all()]
        self.username.choices.insert(0, (-1, _l('- Select -')))
