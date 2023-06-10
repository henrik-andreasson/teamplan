from flask import render_template, redirect, url_for, flash, request, \
    current_app
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from flask_babel import _
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm, ChangePasswordForm, \
    AdminChangePasswordForm, AdminUpdateUserForm, AdminSelecteUserForm
from app.models import User
from app.auth.email import send_password_reset_email


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title=_('Sign In'), form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():

    if current_app.config['OPEN_REGISTRATION'] is True:
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
    else:
        if not current_user.is_authenticated:
            flash(_('Registration is not open, contact admin to get an account'))
            return redirect(url_for('main.index'))
        elif current_app.config['ENFORCE_ROLES'] is True:
            loggedin = User.query.filter_by(
                username=current_user.username).first()
            if loggedin.role != "admin":
                flash(_('Registration of users is limited to admins'))
                return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        if loggedin.role != "admin":
            flash(_('Congratulations, you are now a registered user!'))
        else:
            flash(_(f'New user {user.username} are now a registered user!'))

        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title=_('Register'),
                           form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@bp.route('/change_password/', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Password changed'))
        return redirect(url_for('main.index'))

    return render_template('auth/change_password.html', form=form)


@bp.route('/user/set_password/', methods=['GET', 'POST'])
@login_required
def user_set_password():

    admin = User.query.filter_by(username=current_user.username).first()
    if admin.role != "admin":
        flash(_('Updating other users is limited to admins'))
        return redirect(url_for('main.index'))

    form = AdminChangePasswordForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.get(form.username.data)
        if user is not None:
            user.set_password(form.password.data)
            db.session.commit()
            flash(_('Password changed'))
            return redirect(url_for('main.index'))
        else:
            flash(_('Password change FAILED'))
            return redirect(url_for('main.index'))

    return render_template('auth/change_password.html', form=form)


@bp.route('/user/save/', methods=['GET', 'POST'])
@login_required
def user_save():
    admin = User.query.filter_by(username=current_user.username).first()
    if admin.role != "admin":
        flash(_('Updating other users is limited to admins'))
        return redirect(url_for('main.index'))

    userid = request.args.get('user')
    if userid is None:
        flash(_('Userid not passed to user update'))
        return redirect(url_for('main.index'))

    user = User.query.get(userid)
    if user is None:
        flash(_('Userid not passed to user update'))
        return redirect(url_for('main.index'))

    form = AdminUpdateUserForm()
    form.username.choices = [(user.id, user.username)]

    if request.method == 'POST' and form.validate_on_submit():
        user.email = form.email.data
        user.work_percent = form.work_percent.data
        user.role = form.role.data
        user.active = form.active.data
        db.session.commit()
        flash(_('User Updated'))
        return redirect(url_for('main.index'))
    else:
        form.email.data = user.email
        form.manual_schedule.data = user.manual_schedule
        form.work_percent.data = user.work_percent
        form.active.data = user.active
        form.role.data = user.role 
        return render_template('auth/register.html', form=form)


@bp.route('/user/update/', methods=['GET', 'POST'])
@login_required
def user_update():

    admin = User.query.filter_by(username=current_user.username).first()
    if admin.role != "admin":
        flash(_('Updating other users is limited to admins'))
        return redirect(url_for('main.index'))

    form = AdminSelecteUserForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.get(form.username.data)
        if user is not None:
            return redirect(url_for('auth.user_save', user=user.id))
        else:
            flash(_('User update FAILED'))
            return redirect(url_for('main.index'))

    return render_template('auth/change_password.html', form=form)
