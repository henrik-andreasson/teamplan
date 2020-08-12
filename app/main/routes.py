from flask import render_template, flash, redirect, url_for, request, g, \
    current_app, session
from flask_login import current_user, login_required
from flask_babel import _, get_locale
# from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, WorkForm, ServiceForm, \
    AbsenceForm, OncallForm, NonWorkingDaysForm, GenrateMonthWorkForm
from app.models import User, Work, Service, Absence, Oncall, NonWorkingDays
from app.main import bp
from calendar import Calendar
from datetime import datetime, date, timedelta
from sqlalchemy import func
from dateutil import relativedelta
from rocketchat_API.rocketchat import RocketChat
import calendar
import random


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


def service_stat_month(month, service=None, user=None, month_info=None):

    if user is None:
        users = User.query.order_by(User.username.desc())
    else:
        users = User.query.filter(User.username == user)

    if service is None:
        services = Service.query.order_by(Service.name.desc())
    else:
        services = Service.query.filter(Service.name == service)

    next_month = month + relativedelta.relativedelta(months=1)
    start_year = '{:02d}'.format(month.year)
    start_month = '{:02d}'.format(month.month)

    stop_year = '{:02d}'.format(next_month.year)
    stop_month = '{:02d}'.format(next_month.month)

    date_start = "%s-%s-01 00:00:00" % (start_year, start_month)
    date_stop = "%s-%s-01 00:00:00" % (stop_year, stop_month)
    stats = []
    for u in users:
        stat_user = {}
        stat_user['username'] = u.username
        user_all_work = 0
        user_work_hrs = timedelta(days=0, seconds=0)

        for s in services:
            work_list = Work.query.filter(Work.service_id == s.id,
                                          Work.username == u.username,
                                          func.datetime(Work.start) > date_start,
                                          func.datetime(Work.stop) < date_stop
                                          ).all()

            for w in work_list:
                user_work_hrs = user_work_hrs + (w.stop - w.start)

            stat_user[s.name] = len(work_list)
            user_all_work += stat_user[s.name]

        stat_user['oncall'] = Oncall.query.filter(Oncall.username == u.username,
                                                  func.datetime(Oncall.start) > date_start,
                                                  func.datetime(Oncall.start) < date_stop
                                                  ).with_entities(func.count()).scalar()

        stat_user['user_all_work'] = user_all_work
        stat_user['user_work_hrs'] = user_work_hrs.total_seconds() / 3600
        stat_user['user_work_sec'] = user_work_hrs.total_seconds()
        stat_user['user_work_percent'] = '{:03.1f} %'.format(stat_user['user_work_sec'] / month_info['working_sec_in_month'] * 100)

        if user_all_work > 0:
            stats.append(stat_user)
    return stats


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    output_month = []

    users = User.query.order_by(User.username)
    services = Service.query.order_by(Service.name)
    username = request.args.get('username')
    service = request.args.get('service')
    showabsence = request.args.get('absence')
    month = request.args.get('month')

    if month is not None:
        selected_month = datetime.strptime(month, "%Y-%m")
        session['selected_month'] = month
    elif 'selected_month' in session:
        month = session['selected_month']
        selected_month = datetime.strptime(month, "%Y-%m")
    else:
        selected_month = datetime.utcnow()

    if username is not None:
        if 'selected_user' in session:
            session.pop('selected_user', None)
            username = None
        else:
            session['selected_user'] = username
    elif 'selected_user' in session:
        username = session['selected_user']

    if service is not None:
        if 'selected_service' in session:
            session.pop('selected_service', None)
            service = None
        else:
            session['selected_service'] = service
    elif 'selected_service' in session:
        service = session['selected_service']

    if showabsence is not None:
        if 'showabsence' in session:
            session.pop('showabsence', None)
            showabsence = None
        else:
            session['showabsence'] = "show"
    elif 'showabsence' in session:
        showabsence = session['showabsence']

    if service is not None:
        service_obj = Service.query.filter_by(name=service).first()
        print("service: %s id: %s" % (service, service_obj.id))

    next_month = selected_month + relativedelta.relativedelta(months=1)
    prev_month = selected_month + relativedelta.relativedelta(months=-1)

    calendar = Calendar().monthdayscalendar(selected_month.year,
                                            selected_month.month)
    display_month = '{:02d}'.format(selected_month.month)
    display_year = '{:02d}'.format(selected_month.year)
    working_days_in_month = 0
    non_working_days_in_month = 0
    working_days = [0, 1, 2, 3, 4, 5]

    mon_week = 0
    for week in calendar:
        mon_week = mon_week + 1
        output_week = []
        weekday = 0
        for day in week:
            weekday = weekday + 1

            day_info = {}

# id day is zero the month has not started, ie the 1:st of the month may be a
# Wednesday then monday and tuseday is 0
            if day != 0:
                if weekday in working_days:
                    working_days_in_month += 1

                display_day = '{:02d}'.format(day)
                day_info = {'display_day': display_day, 'week_day': weekday}

                date_min = "%s-%s-%s 00:00:00" % (display_year, display_month,
                                                  display_day)
                date_max = "%s-%s-%s 23:59:00" % (display_year, display_month,
                                                  display_day)

                absence = []
                if service is not None and username is not None:
                    work = Work.query.filter((Work.service_id == service_obj.id)
                                             & (Work.username == username)
                                             & (func.datetime(Work.start) > date_min)
                                             & (func.datetime(Work.stop) < date_max)
                                             ).order_by(Work.start)

                    oncall = Oncall.query.filter((Oncall.service == service)
                                                 & (func.datetime(Oncall.start) > date_min)
                                                 & (func.datetime(Oncall.stop) < date_max)
                                                 ).order_by(Oncall.start)

                    absence = Absence.query.filter(username == username,
                                                   func.datetime(Absence.start) > date_min,
                                                   func.datetime(Absence.stop) < date_max
                                                   ).all()

                elif service is not None:
                    work = Work.query.filter((Work.service_id == service_obj.id)
                                             & (func.datetime(Work.start) > date_min)
                                             & (func.datetime(Work.stop) < date_max)
                                             ).order_by(Work.start)

                    oncall = Oncall.query.filter((Oncall.service == service)
                                                 & (func.datetime(Oncall.start) > date_min)
                                                 & (func.datetime(Oncall.stop) < date_max)
                                                 ).order_by(Oncall.start)

                    for u in service_obj.users:
                        absence += Absence.query.filter(username == u.username,
                                                        func.datetime(Absence.start) > date_min,
                                                        func.datetime(Absence.stop) < date_max
                                                        ).all()

                elif username is not None:
                    work = Work.query.filter(Work.username == username,
                                             func.datetime(Work.start) > date_min,
                                             func.datetime(Work.stop) < date_max
                                             ).order_by(Work.start)

                    oncall = Oncall.query.filter((Oncall.username == username)
                                                 & (func.datetime(Oncall.start) > date_min)
                                                 & (func.datetime(Oncall.start) < date_max)
                                                 ).order_by(Oncall.service)

                    absence = Absence.query.filter(username == username,
                                                   func.datetime(Absence.start) > date_min,
                                                   func.datetime(Absence.stop) < date_max
                                                   ).all()

                else:
                    services = Service.query.all()
                    work = []
                    for s in services:
                        w = Work.query.filter((Work.service_id == s.id)
                                              & (func.datetime(Work.start) > date_min)
                                              & (func.datetime(Work.stop) < date_max)
                                              ).order_by(Work.start)
                        work += w
                    oncall = Oncall.query.filter((func.datetime(Oncall.start) > date_min)
                                                 & (func.datetime(Oncall.start) < date_max)
                                                 ).order_by(Oncall.service)

                    absence = Absence.query.filter(func.datetime(Absence.start) > date_min,
                                                   func.datetime(Absence.stop) < date_max
                                                   ).all()

                nonworkingdays = NonWorkingDays.query.filter((func.datetime(NonWorkingDays.start) > date_min)
                                                             & (func.datetime(NonWorkingDays.start) < date_max)
                                                             ).all()
                if weekday not in working_days:
                    # TODO does not accounts for half days off
                    non_working_days_in_month += 1

                week_date = date(selected_month.year,
                                 selected_month.month, day)
                day_info['week'] = week_date.isocalendar()[1]
                day_info['work'] = work
                day_info['oncall'] = oncall
                day_info['nwd'] = nonworkingdays
                day_info['absence'] = absence
            output_week.insert(weekday, day_info)

        output_month.insert(mon_week, output_week)

    month_str = selected_month.strftime("%Y-%m")
    month_info = {}
    month_info['non_working_days_in_month'] = non_working_days_in_month
    # TODO substract non_working_days_in_month
    month_info['working_days_in_month'] = working_days_in_month
    month_info['working_hours_in_month'] = working_days_in_month * 8
    month_info['working_sec_in_month'] = working_days_in_month * 8 * 60 * 60
    month_info['selected_month'] = month_str
    month_info['selected_service'] = service
    month_info['selected_user'] = username
    month_info['showabsence'] = showabsence
    month_info['prev'] = prev_month.strftime("%b")
    month_info['this'] = selected_month.strftime("%Y %B")
    month_info['next'] = next_month.strftime("%b")
    next_url = url_for('main.index', month=next_month.strftime("%Y-%m"))
    prev_url = url_for('main.index', month=prev_month.strftime("%Y-%m"))

    print("selected month: %s" % selected_month)
    stats = service_stat_month(selected_month, service, username, month_info)

# bar chart
    bar_labels = []
    bar_values = []
    for u in stats:
        bar_labels.append(u['username'])
        bar_values.append(u['user_work_hrs'])

    return render_template('month.html', title=_('Month'), month=output_month,
                           users=users, services=services, stats=stats,
                           month_info=month_info, next_url=next_url,
                           prev_url=prev_url, selected_month=month_str,
                           oncall=oncall,
                           absence_color=current_app.config['ABSENCE_COLOR'],
                           nwd_color=current_app.config['NON_WORKING_DAYS_COLOR'],
                           max=month_info['working_hours_in_month'],
                           labels=bar_labels, values=bar_values)


@bp.route('/explore')
@login_required
def explore():

    page = request.args.get('page', 1, type=int)
    work = Work.query.filter(Work.status != "assigned").paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.explore', page=work.next_num) \
        if work.has_next else None
    prev_url = url_for('main.explore', page=work.prev_num) \
        if work.has_prev else None
    return render_template('work.html', title=_('Explore'),
                           allwork=work.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    print("user: %s services: %s" % (user.username, user.services))

    page = request.args.get('page', 1, type=int)
    users_work = Work.query.filter(Work.username == username).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username, page=users_work.next_num) if users_work.has_next else None
    prev_url = url_for('main.user', username=user.username, page=users_work.prev_num) if users_work.has_prev else None
    return render_template('user.html', user=user, allwork=users_work.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/service/add', methods=['GET', 'POST'])
@login_required
def service_add():
    if 'cancel' in request.form:
        return redirect(request.referrer)

    form = ServiceForm()
    form.users.choices = [(u.username, u.username)
                          for u in User.query.all()]

    if form.validate_on_submit():
        service = Service(name=form.name.data, color=form.color.data)
        for u in form.users.data:
            user = User.query.filter_by(username=u).first()
            print("Adding: User: %s to: %s" % (user.username, service.name))
            service.users.append(user)
        db.session.add(service)
        db.session.commit()
        flash(_('Service have been saved.'))
        return redirect(url_for('main.service_list'))

    page = request.args.get('page', 1, type=int)
    services = Service.query.order_by(Service.updated.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.service_list', page=services.next_num) if services.has_next else None
    prev_url = url_for('main.service_list', page=services.prev_num) if services.has_prev else None
    return render_template('service.html', form=form, services=services.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/service/edit', methods=['GET', 'POST'])
@login_required
def service_edit():
    if 'cancel' in request.form:
        return redirect(request.referrer)

    servicename = request.args.get('name')
    service = Service.query.filter_by(name=servicename).first()

    if service is None:
        render_template('service.html', title=_('Service is not defined'))

    form = ServiceForm(formdata=request.form, obj=service)
# TODO select the previously selected users: service.users
    form.users.choices = [(u.username, u.username)
                          for u in User.query.all()]

    if request.method == 'POST' and form.validate_on_submit():
        # TODO remove not selected users ...
        for u in form.users.data:
            user = User.query.filter_by(username=u).first()
            print("Adding: User: %s to: %s" % (user.username, service.name))
            service.users.append(user)
        service.name = form.name.data
        service.color = form.color.data

        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.service_list'))

    else:
        return render_template('service.html', title=_('Edit Service'),
                               form=form)


@bp.route('/service/list/', methods=['GET', 'POST'])
@login_required
def service_list():
    page = request.args.get('page', 1, type=int)
    services = Service.query.order_by(Service.updated.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.service_list', page=services.next_num) if services.has_next else None
    prev_url = url_for('main.service_list', page=services.prev_num) if services.has_prev else None
    return render_template('services.html', services=services.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/ical_info', methods=['GET'])
@login_required
def ical_info():
    services = Service.query.all()
    return render_template('ical_info.html', title=_('Ical Info'),
                           user=current_user, services=services)


@bp.route('/ical_reset_api_key', methods=['GET'])
@login_required
def ical_reset_api_key():

    current_user.revoke_api_key()
    current_user.get_api_key()

    services = Service.query.all()
    return render_template('ical_info.html', title=_('Ical Info'),
                           user=current_user, services=services)


@bp.route('/work/add', methods=['GET', 'POST'])
@login_required
def work_add():
    form = WorkForm()
    if 'cancel' in request.form:
        return redirect(request.referrer)

    if 'selected_user' in session:
        form.username.default = session['selected_user']
        user = User.query.filter_by(username=session['selected_user']).first()
        form.username.choices = [(user.username, user.username)]
        form.service.choices = []
        for s in Service.query.all():
            for serviceuser in s.users:
                if serviceuser.username == user.username:
                    form.service.choices.extend([(s.name, s.name)])

    elif 'selected_service' in session:
        service = Service.query.filter_by(name=session['selected_service']).first()
        form.service.choices = [(service.name, service.name)]
        form.username.choices = [(u.username, u.username)
                                 for u in service.users]

    else:
        form.service.choices = [(s.name, s.name) for s in Service.query.all()]
        form.username.choices = [(u.username, u.username)
                                 for u in User.query.all()]

    if request.method == 'POST' and form.validate_on_submit():
        service = Service.query.filter_by(name=form.service.data).first()
        work = Work(start=form.start.data,
                    stop=form.stop.data,
                    username=form.username.data,
                    color=service.color,
                    status=form.status.data)
        work.service = service
        db.session.add(work)
        db.session.commit()
        flash(_('New work is now posted!'))

        new_work_mess = 'new work: %s\t%s\t%s\t@%s\nby %s\n ' % (
                         work.start, work.stop, work.service,
                         work.username, current_user.username)
        if current_app.config['ROCKET_ENABLED']:
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket.chat_post_message(
             new_work_mess,
             channel=current_app.config['ROCKET_CHANNEL']
             ).json()

        return redirect(url_for('main.index'))

    else:
        day = request.args.get('day')
        month = request.args.get('month')
        if day is not None and month is not None:
            date_start_str = month + "-" + day + " 08:00"
            date_stop_str = month + "-" + day + " 12:30"

            form.start.data = datetime.strptime(date_start_str, "%Y-%m-%d %H:%M")
            form.stop.data = datetime.strptime(date_stop_str, "%Y-%m-%d %H:%M")

        # TODO figure out how to show work added by the current user this session
        allwork = Work.query.order_by(Work.id.desc()).limit(10)
        return render_template('work.html', title=_('Add Work'),
                               form=form, allwork=allwork)


@bp.route('/work/add/month', methods=['GET', 'POST'])
@login_required
def work_add_month():
    form = GenrateMonthWorkForm()
    month = request.args.get('month')
    if 'cancel' in request.form:
        return redirect(request.referrer)

    if month is not None:
        selected_month = datetime.strptime(month, "%Y-%m")
        session['selected_month'] = month
    elif 'selected_month' in session:
        month = session['selected_month']
        selected_month = datetime.strptime(month, "%Y-%m")
    else:
        selected_month = datetime.utcnow()

    form.service.choices = [(s.name, s.name) for s in Service.query.all()]

    if request.method == 'POST' and form.validate_on_submit():
        service = Service.query.filter_by(name=form.service.data).first()
        selected_month = form.month.data
        status = form.status.data

        c = calendar.Calendar()
        for i in c.itermonthdays(selected_month.year, selected_month.month):

            try:
                weekday = calendar.weekday(selected_month.year, selected_month.month, i)
            except ValueError:
                continue
            if weekday < calendar.SATURDAY:

                start = "%d-%02d-%02d %s:%s" % (selected_month.year, selected_month.month, i, "08", "00")
                stop = "%d-%02d-%02d %s:%s" % (selected_month.year, selected_month.month, i, "12", "30")
                work = Work(start=datetime.strptime(start, "%Y-%m-%d %H:%M"),
                            stop=datetime.strptime(stop, "%Y-%m-%d %H:%M"),
                            color=service.color,
                            status=status)
                if status == "assigned":
                    user = random.choice(service.users)
                    work.username = user.username

                work.service = service
                db.session.add(work)
                db.session.commit()

                start = "%d-%02d-%02d %s:%s" % (selected_month.year, selected_month.month, i, "12", "30")
                stop = "%d-%02d-%02d %s:%s" % (selected_month.year, selected_month.month, i, "17", "00")
                work = Work(start=datetime.strptime(start, "%Y-%m-%d %H:%M"),
                            stop=datetime.strptime(stop, "%Y-%m-%d %H:%M"),
                            color=service.color,
                            status=status)
                if status == "assigned":
                    user = random.choice(service.users)
                    work.username = user.username

                work.service = service
                db.session.add(work)
                db.session.commit()

        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.index'))

    else:

        return render_template('generate_month_work.html', title=_('Add Work for a month'),
                               form=form)


@bp.route('/work/edit/', methods=['GET', 'POST'])
@login_required
def work_edit():

    workid = request.args.get('work')

    if 'cancel' in request.form:
        return redirect(request.referrer)
    if 'delete' in request.form:
        return redirect(url_for('main.work_delete', work=workid))

    work = Work.query.get(workid)

    if work is None:
        render_template('service.html', title=_('Work is not defined'))

    form = WorkForm(formdata=request.form, obj=work)
    service = Service.query.get(work.service_id)
    form.username.choices = [(u.username, u.username)
                             for u in User.query.all()]
    form.service.choices = [(service.name, service.name)]

    if request.method == 'POST' and form.validate_on_submit():
        string_from = '%s\t%s\t%s\t@%s\n' % (work.start, work.stop,
                                             work.service, work.username)
        service = Service.query.filter_by(name=form.service.data).first()
        work.start = form.start.data
        work.stop = form.stop.data
        work.username = form.username.data
        work.color = service.color
        work.status = form.status.data
        work.service = service

        db.session.commit()
        flash(_('Your changes have been saved.'))

        if current_app.config['ROCKET_ENABLED']:
            string_to = '%s\t%s\t%s\t@%s\n' % (work.start, work.stop,
                                               work.service, work.username)
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket.chat_post_message('edit of work from: \n%s\nto:\n%s\nby: %s' % (
                                 string_from, string_to, current_user.username),
                                 channel=current_app.config['ROCKET_CHANNEL']
                                 ).json()

        return redirect(url_for('main.index'))

    else:
        return render_template('index.html', title=_('Edit Work'),
                               form=form)


@bp.route('/work/list/', methods=['GET', 'POST'])
@login_required
def work_list():

    page = request.args.get('page', 1, type=int)
    username = request.args.get('username')
    servicename = request.args.get('service')
    s = Service.query.filter_by(name=servicename).first()

    if username is not None:
        work = Work.query.filter_by(username=username).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    elif s is not None:
        work = Work.query.filter_by(service_id=s.id).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    else:
        work = Work.query.order_by(Work.start).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.work_list', page=work.next_num) \
        if work.has_next else None
    prev_url = url_for('main.work_list', page=work.prev_num) \
        if work.has_prev else None

    return render_template('work.html', title=_('Work'),
                           allwork=work.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/work/delete/', methods=['GET', 'POST'])
@login_required
def work_delete():

    workid = request.args.get('work')
    work = Work.query.get(workid)

    if work is None:
        flash(_('Work was not deleted, id not found!'))
        return redirect(url_for('main.index'))

    deleted_msg = 'Work deleted: %s\t%s\t%s\t@%s\n' % (work.start, work.stop,
                                                       work.service.name,
                                                       work.username)
    if current_app.config['ROCKET_ENABLED']:
        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])
        rocket.chat_post_message('work deleted: \n%s\nto:\n%s\nby: %s' % (
                             deleted_msg, current_user.username),
                             channel=current_app.config['ROCKET_CHANNEL']
                             ).json()
    flash(deleted_msg)
    db.session.delete(work)
    db.session.commit()

    return redirect(url_for('main.index'))


@bp.route('/absence/add', methods=['GET', 'POST'])
@login_required
def absence_add():

    if 'cancel' in request.form:
        return redirect(request.referrer)

    form = AbsenceForm()
    page = request.args.get('page', 1, type=int)

    form.username.choices = [(u.username, u.username)
                             for u in User.query.all()]

    absence = Absence.query.order_by(Absence.start).paginate(
              page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.absence_list', page=absence.next_num) \
        if absence.has_next else None
    prev_url = url_for('main.absence_list', page=absence.prev_num) \
        if absence.has_prev else None

    if request.method == 'POST' and form.validate_on_submit():
        absence = Absence(start=form.start.data,
                          stop=form.stop.data,
                          username=form.username.data,
                          status=form.status.data)
        db.session.add(absence)
        db.session.commit()
        flash(_('New absence is now posted!'))
        print("rocket enabled?: %s" % current_app.config['ROCKET_ENABLED'])
        if current_app.config['ROCKET_ENABLED']:
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket.chat_post_message('new absence: %s\t%s\t%s\t@%s ' % (
                                 absence.start, absence.stop, absence.status,
                                 absence.username),
                                 channel=current_app.config['ROCKET_CHANNEL']
                                 ).json()

        return redirect(url_for('main.index'))
    else:
        return render_template('absence.html', title=_('Add absence'),
                               allabsence=absence.items, form=form,
                               next_url=next_url, prev_url=prev_url)


@bp.route('/absence/edit/', methods=['GET', 'POST'])
@login_required
def absence_edit():

    absenceid = request.args.get('absence')
    absence = Absence.query.get(absenceid)

    if 'cancel' in request.form:
        return redirect(request.referrer)

    if 'delete' in request.form:
        return redirect(url_for('main.absence_delete', absence=absenceid))

    if absence is None:
        render_template('service.html', title=_('absence is not defined'))

    form = AbsenceForm(formdata=request.form, obj=absence)
    form.username.choices = [(u.username, u.username)
                             for u in User.query.all()]

    if request.method == 'POST' and form.validate_on_submit():
        rocket_msg_from = 'edit of absence from: \n%s\t%s\t%s\t@%s' % (absence.start,
                                                                       absence.stop,
                                                                       absence.status,
                                                                       absence.username)

        form.populate_obj(absence)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        if current_app.config['ROCKET_ENABLED']:
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket_msg_to = 'to: \n%s\t%s\t%s\t@%s ' % (absence.start,
                                                        absence.stop,
                                                        absence.status,
                                                        absence.username)
            rocket.chat_post_message("%s\n%s\n\nby: %s" % (rocket_msg_from,
                                                           rocket_msg_to,
                                                           current_user.username),
                                     channel=current_app.config['ROCKET_CHANNEL']
                                     ).json()

        return redirect(url_for('main.index'))

    else:
        return render_template('index.html', title=_('Edit absence'),
                               form=form)


@bp.route('/absence/list/', methods=['GET', 'POST'])
@login_required
def absence_list():

    page = request.args.get('page', 1, type=int)
    username = request.args.get('username')

    if username is not None:
        absence = Absence.query.filter_by(username=username).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    else:
        absence = Absence.query.order_by(Absence.start).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.absence_list', page=absence.next_num) \
        if absence.has_next else None
    prev_url = url_for('main.absence_list', page=absence.prev_num) \
        if absence.has_prev else None

    return render_template('absence.html', title=_('absence'),
                           allabsence=absence.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/absence/delete/', methods=['GET', 'POST'])
@login_required
def absence_delete():

    absenceid = request.args.get('absence')
    absence = Absence.query.get(absenceid)

    if absence is None:
        flash(_('Absence was not deleted, id not found!'))
        return redirect(url_for('main.index'))

    deleted_msg = 'Absence deleted: %s\t%s\t%s\n' % (absence.start, absence.stop, absence.username)
    if current_app.config['ROCKET_ENABLED']:
        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])
        rocket.chat_post_message('absence deleted: \n%s\nto:\n%s\nby: %s' % (
                             deleted_msg, current_user.username),
                             channel=current_app.config['ROCKET_CHANNEL']
                             ).json()
    flash(deleted_msg)
    db.session.delete(absence)
    db.session.commit()

    return redirect(url_for('main.index'))


@bp.route('/oncall/add', methods=['GET', 'POST'])
@login_required
def oncall_add():
    form = OncallForm()
    if 'cancel' in request.form:
        return redirect(request.referrer)

    form.username.choices = [(u.username, u.username)
                             for u in User.query.all()]

    form.service.choices = [(s.name, s.name) for s in Service.query.all()]

    if request.method == 'POST' and form.validate_on_submit():
        service = Service.query.filter_by(name=form.service.data).first()
        oncall = Oncall(start=form.start.data,
                        stop=form.stop.data,
                        username=form.username.data,
                        service=form.service.data,
                        color=service.color,
                        status=form.status.data)
        db.session.add(oncall)
        db.session.commit()
        flash(_('New oncall is now posted!'))

        new_oncall_mess = 'new oncall: %s\t%s\t%s\t@%s\nby %s\n ' % (oncall.start,
                                                                     oncall.stop,
                                                                     oncall.service,
                                                                     oncall.username,
                                                                     current_user.username)
        if current_app.config['ROCKET_ENABLED']:
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket.chat_post_message(new_oncall_mess,
                                     channel=current_app.config['ROCKET_CHANNEL']
                                     ).json()

        return redirect(url_for('main.index'))
    else:
        day = request.args.get('day')
        month = request.args.get('month')
        if day is not None and month is not None:
            date_start_str = month + "-" + day
            date_start_str = month + "-" + day + " 08:00"

            form.start.data = datetime.strptime(date_start_str, "%Y-%m-%d %H:%M")
            form.stop.data = form.start.data + relativedelta.relativedelta(days=7)

        return render_template('oncall.html', title=_('Add oncall'),
                               form=form)


@bp.route('/oncall/edit/', methods=['GET', 'POST'])
@login_required
def oncall_edit():
    if 'cancel' in request.form:
        return redirect(request.referrer)

    oncallid = request.args.get('oncall')
    oncall = Oncall.query.get(oncallid)

    if oncall is None:
        render_template('main.index', title=_('oncall is not defined'))

    if 'delete' in request.form:
        return redirect(url_for('main.oncall_delete', oncall=oncallid))

    form = OncallForm(formdata=request.form, obj=oncall)
    form.username.choices = [(u.username, u.username)
                             for u in User.query.all()]
    form.service.choices = [(s.name, s.name) for s in Service.query.all()]

    if request.method == 'POST' and form.validate_on_submit():
        string_from = '%s\t%s\t%s\t@%s\n' % (oncall.start, oncall.stop,
                                             oncall.service, oncall.username)
        form.populate_obj(oncall)
        db.session.commit()
        flash(_('Your changes have been saved.'))

        if current_app.config['ROCKET_ENABLED']:
            string_to = '%s\t%s\t%s\t@%s\n' % (oncall.start, oncall.stop,
                                               oncall.service, oncall.username)
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket.chat_post_message('edit of oncall from: \n%s\nto:\n%s\nby: %s' % (
                                 string_from, string_to, current_user.username),
                                 channel=current_app.config['ROCKET_CHANNEL']
                                 ).json()

        return redirect(url_for('main.index'))

    else:
        return render_template('index.html', title=_('Edit oncall'),
                               form=form)


@bp.route('/oncall/list/', methods=['GET', 'POST'])
@login_required
def oncall_list():

    page = request.args.get('page', 1, type=int)
    username = request.args.get('username')
    service = request.args.get('service')

    if username is not None:
        oncall = Oncall.query.filter_by(username=username).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    elif service is not None:
        oncall = Oncall.query.filter_by(service=service).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    else:
        oncall = Oncall.query.order_by(Oncall.start).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.oncall_list', page=oncall.next_num) \
        if oncall.has_next else None
    prev_url = url_for('main.oncall_list', page=oncall.prev_num) \
        if oncall.has_prev else None

    return render_template('oncall.html', title=_('oncall'),
                           alloncall=oncall.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/oncall/delete/', methods=['GET', 'POST'])
@login_required
def oncall_delete():

    oncallid = request.args.get('oncall')
    oncall = Oncall.query.get(oncallid)

    if oncall is None:
        flash(_('oncall was not deleted, id not found!'))
        return redirect(url_for('main.index'))

    deleted_msg = 'oncall deleted: %s\t%s\t%s @%s\n' % (oncall.start,
                                                        oncall.stop,
                                                        oncall.service,
                                                        oncall.username)
    if current_app.config['ROCKET_ENABLED']:
        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])
        rocket.chat_post_message('oncall deleted: \n%s\nto:\n%s\nby: %s' % (
                             deleted_msg, current_user.username),
                             channel=current_app.config['ROCKET_CHANNEL']
                             ).json()
    flash(deleted_msg)
    db.session.delete(oncall)
    db.session.commit()

    return redirect(url_for('main.index'))


@bp.route('/nonworkingdays/add', methods=['GET', 'POST'])
@login_required
def nonworkingdays_add():
    if 'cancel' in request.form:
        return redirect(request.referrer)
    form = NonWorkingDaysForm()
    page = request.args.get('page', 1, type=int)

    if request.method == 'POST' and form.validate_on_submit():
        nonworkingdays = NonWorkingDays(start=form.start.data,
                                        stop=form.stop.data,
                                        name=form.name.data)
        db.session.add(nonworkingdays)
        db.session.commit()
        flash(_('New nonworkingdays is now posted!'))

        if current_app.config['ROCKET_ENABLED']:
            new_nonworkingdays_mess = 'new nonworkingdays: %s\t%s\t%s\nby %s\n ' % (nonworkingdays.start,
                                                                                    nonworkingdays.stop, nonworkingdays.name,
                                                                                    current_user.username)
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket.chat_post_message(new_nonworkingdays_mess,
                                     channel=current_app.config['ROCKET_CHANNEL']
                                     ).json()

        return redirect(url_for('main.index'))
    else:

        nonworkingdays = NonWorkingDays.query.order_by(NonWorkingDays.start).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)

        return render_template('nonworkingdays.html', title=_('Add nonworkingdays'),
                               allnwd=nonworkingdays.items, form=form)


@bp.route('/nonworkingdays/edit/', methods=['GET', 'POST'])
@login_required
def nonworkingdays_edit():

    if 'cancel' in request.form:
        return redirect(request.referrer)

    nonworkingdaysid = request.args.get('nwd')
    nwd = NonWorkingDays.query.get(nonworkingdaysid)

    if nwd is None:
        render_template('nonworkingdays.html',
                        title=_('nonworkingdays is not defined'))

    if 'delete' in request.form:
        return redirect(url_for('main.nonworkingday_delete',
                                nwd=nonworkingdaysid))

    form = NonWorkingDaysForm(formdata=request.form, obj=nwd)

    if request.method == 'POST' and form.validate_on_submit():
        string_from = '%s\t%s\t%s\n' % (nwd.start,
                                        nwd.stop,
                                        nwd.name)
        form.populate_obj(nwd)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        string_to = '%s\t%s\t%s\n' % (nwd.start,
                                      nwd.stop,
                                      nwd.name)
        if current_app.config['ROCKET_ENABLED'] is not False:
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket.chat_post_message('edit of nonworkingdays from: \n%s\nto:\n%s\nby: %s' % (
                                 string_from, string_to, current_user.username),
                                 channel=current_app.config['ROCKET_CHANNEL']
                                 ).json()

        return redirect(url_for('main.index'))

    else:
        return render_template('index.html', title=_('Edit nonworkingdays'),
                               form=form)


@bp.route('/nonworkingdays/list/', methods=['GET', 'POST'])
@login_required
def nonworkingdays_list():

    page = request.args.get('page', 1, type=int)

    nonworkingdays = NonWorkingDays.query.order_by(NonWorkingDays.start).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.nonworkingdays_list', page=nonworkingdays.next_num) \
        if nonworkingdays.has_next else None
    prev_url = url_for('main.nonworkingdays_list', page=nonworkingdays.prev_num) \
        if nonworkingdays.has_prev else None

    return render_template('nonworkingdays.html', title=_('nonworkingdays'),
                           allnwd=nonworkingdays.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/nonworkingday/delete/', methods=['GET', 'POST'])
@login_required
def nonworkingday_delete():

    nonworkingdayid = request.args.get('nwd')
    nonworkingday = NonWorkingDays.query.get(nonworkingdayid)

    if nonworkingday is None:
        flash(_('nonworkingday was not deleted, id not found!'))
        return redirect(url_for('main.index'))

    deleted_msg = 'nonworkingday deleted: %s\t%s\t%s\n' % (nonworkingday.start,
                                                           nonworkingday.stop,
                                                           nonworkingday.name)
    if current_app.config['ROCKET_ENABLED']:
        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])
        rocket.chat_post_message('nonworkingday deleted: \n%s\nto:\n%s\nby: %s' % (
                             deleted_msg, current_user.username),
                             channel=current_app.config['ROCKET_CHANNEL']
                             ).json()
    flash(deleted_msg)
    db.session.delete(nonworkingday)
    db.session.commit()

    return redirect(url_for('main.index'))
