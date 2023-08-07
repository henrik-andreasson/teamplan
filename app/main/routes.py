from flask import render_template, flash, redirect, url_for, request, g, \
    current_app, session
from flask_login import current_user, login_required
from flask_babel import _, get_locale
# from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, WorkForm, ServiceForm, \
    AbsenceForm, OncallForm, NonWorkingDaysForm, GenrateMonthWorkForm, \
    FilterUserServiceForm, GenrateMonthOncallForm
from app.models import User, Work, Service, Absence, Oncall, NonWorkingDays
from app.main import bp
from calendar import Calendar
from datetime import datetime, date, timedelta
from sqlalchemy import func
from dateutil import relativedelta
from rocketchat_API.rocketchat import RocketChat
import calendar
from sqlalchemy import desc, asc


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

    if month is None:
        return -1
    else:
        print("month: {}".format(month))

    next_month = month + relativedelta.relativedelta(months=1)
    start_year = '{:02d}'.format(month.year)
    start_month = '{:02d}'.format(month.month)

    stop_year = '{:02d}'.format(next_month.year)
    stop_month = '{:02d}'.format(next_month.month)

    date_start = "%s-%s-01 00:00:00" % (start_year, start_month)
    date_stop = "%s-%s-01 00:00:00" % (stop_year, stop_month)
    dt_start = datetime.strptime(date_start, "%Y-%m-%d %H:%M:%S")
    dt_stop = datetime.strptime(date_stop, "%Y-%m-%d %H:%M:%S")
    stats = []
    for u in users:
        print("statuser: checking user: {}".format(u))
        stat_user = {}
        stat_user['username'] = u.username
        user_all_work = 0
        user_work_hrs = timedelta(days=0, seconds=0)

        for s in services:
            work_list = Work.query.filter((Work.service_id == s.id)
                                          & (Work.user_id == u.id)
                                          & (Work.start > dt_start)
                                          & (Work.stop < dt_stop)
                                          ).all()

            for w in work_list:
                user_work_hrs = user_work_hrs + (w.stop - w.start)

            stat_user[s.name] = len(work_list)
            user_all_work += stat_user[s.name]

        stat_user['oncall'] = Oncall.query.filter((Oncall.user_id == u.id)
                                                  & (Oncall.start > dt_start)
                                                  & (Oncall.start < dt_stop)
                                                  ).with_entities(func.count()).scalar()

        stat_user['user_all_work'] = user_all_work
        stat_user['user_work_hrs'] = user_work_hrs.total_seconds() / 3600
        stat_user['user_work_sec'] = user_work_hrs.total_seconds()
        if month_info is not None and 'working_sec_in_month' in month_info:
            stat_user['user_work_percent'] = '{:03.1f} %'.format(stat_user['user_work_sec'] / month_info['working_sec_in_month'] * 100)

        if user_all_work > 0:
            stats.append(stat_user)
    return stats


def users_stats(month, service):

    if month is None:
        return -1
    else:
        print("month: {}".format(month))

    next_month = month + relativedelta.relativedelta(months=1)
    start_year = '{:02d}'.format(month.year)
    start_month = '{:02d}'.format(month.month)

    stop_year = '{:02d}'.format(next_month.year)
    stop_month = '{:02d}'.format(next_month.month)

    date_start = "%s-%s-01 00:00:00" % (start_year, start_month)
    date_stop = "%s-%s-01 00:00:00" % (stop_year, stop_month)
    dt_start = datetime.strptime(date_start, "%Y-%m-%d %H:%M:%S")
    dt_stop = datetime.strptime(date_stop, "%Y-%m-%d %H:%M:%S")

    stats = {}

    for u in service.users:
        user_work_hrs = timedelta(days=0, seconds=0)

        work_list = Work.query.filter((Work.user_id == u.id)
                                      & (Work.start > dt_start)
                                      & (Work.stop < dt_stop)
                                      ).all()

        for w in work_list:
            user_work_hrs = user_work_hrs + (w.stop - w.start)

        stats[u.username] = user_work_hrs.total_seconds() / 3600
        print("users_stats: checking user: {} -> {}h".format(u.username, stats[u.username]))

    return stats


def users_work_within(start,stop,service):


    if start is None:
        return -1
    else:
        print(f"start: {start}")

    if stop is None:
        return -1
    else:
        print(f"stop: {stop}")

    if service is None:
        return -1
    else:
        print(f"service: {service}")

    stats = {}

    for u in service.users:
        stats[u.username] = Work.query.filter((Work.user_id == u.id)                          #   <---day -->
                                             & ((Work.start <= start) & (Work.stop >= start)  #<--work-->
                                             | (Work.start  >= start) & (Work.stop <=  stop)  #      <-->
                                             | (Work.start >=  start) & (Work.stop <=  stop)  #           <---->
                                         )).with_entities(func.count()).scalar()

        print("users_stats: checking user: {} -> {} shifts".format(u.username, stats[u.username]))

    return stats


def oncall_stats(ts, service):

    if ts is None:
        return -1
    else:
        print(f"ts: {ts}")

    if service is None:
        return -1

    stats = {}

    for u in service.users:
        stats[u.username] = Oncall.query.filter((Oncall.service_id == service.id)
                                         & (Oncall.user_id == u.id)
                                         & ((Oncall.start < ts) & (Oncall.stop > ts))
                                         ).with_entities(func.count()).scalar()

        print(f"oncall_stats: checking user: {u.username} for oncall at {ts} {stats[u.username]}")

    return stats


def absence_stats(start,stop,service):

    if start is None:
        return -1
    else:
        print(f"start: {start}")

    if stop is None:
        return -1
    else:
        print(f"stop: {stop}")

    if service is None:
        return -1
    else:
        print(f"service: {service}")

    stats = {}

    for u in service.users:
        stats[u.username] = Absence.query.filter((Absence.user_id == u.id)                        #   <---abs -->
                                             & ((Absence.start >= start) & (Absence.start <= stop)  #<--work-->
                                             | (Absence.start <=  start) & (Absence.stop <=  stop)  #      <-->
                                             | (Absence.start <=  start) & (Absence.stop >=  stop)  #           <---->
                                         )).with_entities(func.count()).scalar()

        print(f"abcense_stats: checking user: {u.username} for asence at {start} -> {stop} {stats[u.username]}")

    return stats


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    output_month = []

    users = User.query.order_by(User.username)
    services = Service.query.order_by(Service.name)
    showabsence = request.args.get('absence')
    month = request.args.get('month')

    form = FilterUserServiceForm()

    service_id = None
    user_id = None

    if month is not None:
        selected_month = datetime.strptime(month, "%Y-%m")
        session['selected_month'] = month
    elif 'selected_month' in session:
        month = session['selected_month']
        selected_month = datetime.strptime(month, "%Y-%m")
    else:
        selected_month = datetime.utcnow()

    showabsence = None
    if request.method == 'POST' and form.validate_on_submit():
        service_id = form.service.data
        user_id = form.user.data
        if form.showabsence.data is True:
            showabsence = "show"
            session['showabsence'] = "show"
        else:
            showabsence = None
            session['showabsence'] = None

    if 'showabsence' in session:
        showabsence = session['showabsence']

    service_obj = None
    if service_id is not None:
        service_obj = Service.query.get(service_id)

    if service_obj is None:
        service = None
    else:
        service = service_obj.name
        print("service: %s id: %s" % (service, service_obj.id))

    user = None
    if user_id is not None:
        user = User.query.get(user_id)

    if user is None:
        username = None
    else:
        username = user.username
        print("user: %s id: %s" % (username, user.id))

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
                dt_start = datetime.strptime(date_min, "%Y-%m-%d %H:%M:%S")
                dt_stop = datetime.strptime(date_max, "%Y-%m-%d %H:%M:%S")

                absence = []
                if service is not None and username is not None:
                    work = Work.query.filter((Work.service_id == service_obj.id)
                                             & (Work.user_id == user.id)
                                             & (Work.start > dt_start)
                                             & (Work.stop < dt_stop)
                                             ).order_by(Work.start)

                    oncall = Oncall.query.filter((Oncall.service_id == service_obj.id)
                                                 & (Oncall.user_id == user.id)
                                                 & ((Oncall.start > dt_start) & (Oncall.start < dt_stop))
                                                 ).order_by(Oncall.start)

                    absence = Absence.query.filter((Absence.user_id == user.id)
                                                   & ((Absence.start > dt_start) & (Absence.start < dt_stop)
                                                       | (Absence.stop > dt_start) & (Absence.stop < dt_stop)
                                                       | (Absence.start < dt_start) & (Absence.stop > dt_stop)
                                                      )
                                                   ).all()

                elif service is not None:
                    work = Work.query.filter((Work.service_id == service_obj.id)
                                             & (Work.start > dt_start)
                                             & (Work.stop < dt_stop)
                                             ).order_by(Work.start)

                    oncall = Oncall.query.filter((Oncall.service_id == service_obj.id)
                                                 & ((Oncall.start > dt_start) & (Oncall.start < dt_stop))
                                                 ).order_by(Oncall.start)

                    for u in service_obj.users:
                        absence += Absence.query.filter((Absence.user_id == u.id)
                                                        & ((Absence.start > dt_start) & (Absence.start < dt_stop)
                                                           | (Absence.stop > dt_start) & (Absence.stop < dt_stop)
                                                           | (Absence.start < dt_start) & (Absence.stop > dt_stop)
                                                           )
                                                        ).all()

                elif username is not None:
                    work = Work.query.filter((Work.user_id == user.id)
                                             & (Work.start > dt_start)
                                             & (Work.stop < dt_stop)
                                             ).order_by(Work.start)

                    oncall = Oncall.query.filter((Oncall.user_id == user.id)
                                                 & ((Oncall.start > dt_start) & (Oncall.start < dt_stop))
                                                 ).order_by(Oncall.start)

                    absence = Absence.query.filter((Absence.user_id == user.id)
                                                   & ((Absence.start > dt_start) & (Absence.start < dt_stop)
                                                      | (Absence.stop > dt_start) & (Absence.stop < dt_stop)
                                                      | (Absence.start < dt_start) & (Absence.stop > dt_stop)
                                                      )
                                                   ).all()

                else:
                    work = []
                    for s in services:
                        w = Work.query.filter((Work.service_id == s.id)
                                              & (Work.start > dt_start)
                                              & (Work.stop < dt_stop)
                                              ).order_by(Work.start)
                        work += w
                    oncall = Oncall.query.filter(
                                                 ((Oncall.start > dt_start) & (Oncall.start < dt_stop))
                                                 ).order_by(Oncall.start)
#                                                 | ((Oncall.stop > dt_start) & (Oncall.stop < dt_stop))
#                                                 | ((Oncall.start < dt_start) & (Oncall.stop > dt_stop))

                    absence = Absence.query.filter(
                                                   (Absence.start > dt_start) & (Absence.start < dt_stop)
                                                   | (Absence.stop > dt_start) & (Absence.stop < dt_stop)
                                                   | (Absence.start < dt_start) & (Absence.stop > dt_stop)
                                                   ).all()

                nonworkingdays = NonWorkingDays.query.filter((NonWorkingDays.start > dt_start)
                                                             & (NonWorkingDays.start < dt_stop)
                                                             ).all()

                extra_work_info = {}
                for w in work:
                    extra_work_info[w.id] = {}
                    extra_work_info[w.id]['no_of_work'] = 0
                    extra_work_info[w.id]['oncall'] = 0
                    extra_work_info[w.id]['absence'] = 0
                    if w.user_id is None:
                        print(f'user is none, skipping')
                        continue
                    extra_work_info[w.id]['no_of_work'] = Work.query.filter(((Work.user_id == w.user_id)          # <---day--->
                                                                      & (Work.start > dt_start)                   #  <--work->
                                                                      & (Work.stop < dt_stop)
                                                                      )).with_entities(func.count()).scalar()

                    extra_work_info[w.id]['oncall'] = Oncall.query.filter((Oncall.user_id == w.user_id)
                                                                & (Oncall.service_id == w.service_id)                      #   < -- oncall -->
                                                                & ((Oncall.start <= w.start) & (Oncall.stop >= w.stop)   #     <--wrk-->
                                                                |  (Oncall.start >= w.start) & (Oncall.start < w.stop)   # <--wrk-->
                                                                |  (Oncall.start < w.start) & (Oncall.stop > w.start)    #        <--wrk----->
                                                                )).with_entities(func.count()).scalar()

                    extra_work_info[w.id]['absence'] = Absence.query.filter((Absence.user_id == w.user_id)                         #   <---abs -->
                                                                       & ((Absence.start <= w.start) & (Absence.stop >= w.stop)  #    <--work->
                                                                       | (Absence.start  > w.start) & (Absence.start < w.stop) #  <-->
                                                                       | (Absence.stop  > w.start) & (Absence.stop < w.stop)   #           <---->
                                                                 )).with_entities(func.count()).scalar()

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
                day_info['extra_work_info'] = extra_work_info
                for w in extra_work_info:
                    ewi = extra_work_info[w]
                    asdf = ewi['absence']
                    print(f'asdf: {asdf}')

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
    month_info['today_day'] = date.today().strftime("%d")
    month_info['today_year_month'] = date.today().strftime("%Y-%m")
    month_info['date_link_to'] = current_app.config['DATE_LINK_TO']
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
                           oncall=oncall, form=form,
                           absence_color=current_app.config['ABSENCE_COLOR'],
                           nwd_color=current_app.config['NON_WORKING_DAYS_COLOR'],
                           max=month_info['working_hours_in_month'],
                           labels=bar_labels, values=bar_values)


@bp.route('/plan_month', methods=['GET', 'POST'])
@login_required
def plan_month():
    output_month = []

    users = User.query.order_by(User.username)
    services = Service.query.order_by(Service.name)
    showabsence = request.args.get('absence')
    month = request.args.get('month')

    form = FilterUserServiceForm()

    service_id = None
    user_id = None

    if month is not None:
        selected_month = datetime.strptime(month, "%Y-%m")
        session['selected_month'] = month
    elif 'selected_month' in session:
        month = session['selected_month']
        selected_month = datetime.strptime(month, "%Y-%m")
    else:
        selected_month = datetime.utcnow()

    showabsence = None
    if request.method == 'POST' and form.validate_on_submit():
        service_id = form.service.data
        user_id = form.user.data
        if form.showabsence.data is True:
            showabsence = "show"
            session['showabsence'] = "show"
        else:
            showabsence = None
            session['showabsence'] = None

    if 'showabsence' in session:
        showabsence = session['showabsence']

    service_obj = None
    if service_id is not None:
        service_obj = Service.query.get(service_id)

    if service_obj is None:
        service = None
    else:
        service = service_obj.name
        print("service: %s id: %s" % (service, service_obj.id))

    user = None
    if user_id is not None:
        user = User.query.get(user_id)

    if user is None:
        username = None
    else:
        username = user.username
        print("user: %s id: %s" % (username, user.id))

    next_month = selected_month + relativedelta.relativedelta(months=1)
    prev_month = selected_month + relativedelta.relativedelta(months=-1)

    calendar = Calendar().monthdayscalendar(selected_month.year,
                                            selected_month.month)
    display_month = '{:02d}'.format(selected_month.month)
    display_year = '{:02d}'.format(selected_month.year)

    working_days = [0, 1, 2, 3, 4, 5]

    mon_week = 0
    for week in calendar:
        mon_week = mon_week + 1
        output_week = []
        weekday = 0
        for day in week:
            weekday = weekday + 1
            if weekday not in working_days:
                continue

            day_info = {}

# id day is zero the month has not started, ie the 1:st of the month may be a
# Wednesday then monday and tuseday is 0
            if day != 0:

                display_day = '{:02d}'.format(day)
                day_info = {'display_day': display_day, 'week_day': weekday}

                date_min = "%s-%s-%s 00:00:00" % (display_year, display_month,
                                                  display_day)
                date_max = "%s-%s-%s 23:59:00" % (display_year, display_month,
                                                  display_day)
                dt_start = datetime.strptime(date_min, "%Y-%m-%d %H:%M:%S")
                dt_stop = datetime.strptime(date_max, "%Y-%m-%d %H:%M:%S")

                users = []
                if service_obj is not None:
                    for su in service_obj.users:
                        user_info = {}
                        user_info['user'] = su
                        work = Work.query.filter(((Work.user_id == su.id)
                                                  & (Work.start > dt_start)
                                                  & (Work.stop < dt_stop)
                                                  )).with_entities(func.count()).scalar()

                        user_info['work_today'] = work

#                        print(f'userinfo: {user_info["user"].username} work: {work}')
                        user_info['absence'] = Absence.query.filter((Absence.user_id == su.id)
                                                                    & ((Absence.start > dt_start) & (Absence.start < dt_stop)
                                                                       | (Absence.stop > dt_start) & (Absence.stop < dt_stop)
                                                                       | (Absence.start < dt_start) & (Absence.stop > dt_stop)
                                                                       )
                                                                    ).with_entities(func.count()).scalar()
#                        print(f'userinfo: absence: {user_info["absence"]}')

                        users.append(user_info)

                week_date = date(selected_month.year,
                                 selected_month.month, day)
                day_info['week'] = week_date.isocalendar()[1]
                day_info['users'] = users
            output_week.insert(weekday, day_info)

        output_month.insert(mon_week, output_week)

    month_str = selected_month.strftime("%Y-%m")
    month_info = {}
    month_info['selected_month'] = month_str
    month_info['selected_service'] = service
    month_info['selected_user'] = username
    month_info['showabsence'] = showabsence
    month_info['prev'] = prev_month.strftime("%b")
    month_info['this'] = selected_month.strftime("%Y %B")
    month_info['next'] = next_month.strftime("%b")
    month_info['today_day'] = date.today().strftime("%d")
    month_info['today_year_month'] = date.today().strftime("%Y-%m")
    month_info['date_link_to'] = current_app.config['DATE_LINK_TO']
    next_url = url_for('main.index', month=next_month.strftime("%Y-%m"))
    prev_url = url_for('main.index', month=prev_month.strftime("%Y-%m"))

    return render_template('plan.html', title=_('Month'), month=output_month,
                           users=users, services=services,
                           month_info=month_info, next_url=next_url,
                           prev_url=prev_url, selected_month=month_str,
                           form=form,
                           absence_color=current_app.config['ABSENCE_COLOR'],
                           nwd_color=current_app.config['NON_WORKING_DAYS_COLOR'])


@bp.route('/explore')
@login_required
def explore():

    dt_today = datetime.utcnow()
    now_day = '{:02d}'.format(dt_today.day)
    now_month = '{:02d}'.format(dt_today.month)

    date_min = "%s-%s-%s 00:00:00" % (dt_today.year, now_month, now_day)
    dt_start = datetime.strptime(date_min, "%Y-%m-%d %H:%M:%S")

    all = request.args.get('all', 0, type=int)
    page = request.args.get('page', 1, type=int)

    if all:
        work = Work.query.filter((Work.status != "assigned")).order_by(Work.start.desc()).paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    else:
        work = Work.query.filter((Work.status != "assigned")
                                 & (Work.start > dt_start)
                                 ).order_by(Work.start.desc()).paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'])

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
    services = Service.query.order_by(Service.name)

    page = request.args.get('page', 1, type=int)
    users_work = Work.query.filter(Work.user_id == user.id).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.user', username=user.username, page=users_work.next_num) if users_work.has_next else None
    prev_url = url_for('main.user', username=user.username, page=users_work.prev_num) if users_work.has_prev else None
    return render_template('user.html', user=user, allwork=users_work.items,
                           services=services, next_url=next_url, prev_url=prev_url)


@bp.route('/user/list')
@login_required
def user_list():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    services = Service.query.all()

    next_url = url_for('main.user_list', page=users.next_num) if users.has_next else None
    prev_url = url_for('main.user_list', page=users.prev_num) if users.has_prev else None
    return render_template('users.html', users=users.items, services=services,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/service/add', methods=['GET', 'POST'])
@login_required
def service_add():
    if 'cancel' in request.form:
        return redirect(url_for('main.index'))

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Service registration is limited to admins'))
            return redirect(url_for('main.index'))

    form = ServiceForm()

    if form.validate_on_submit():
        service = Service(name=form.name.data,
                          lightcolor=form.lightcolor.data,
                          darkcolor=form.darkcolor.data)
        for u in form.users.data:
            user = User.query.get(u)
            print("Adding: User: %s to: %s" % (user.username, service.name))
            service.users.append(user)
        service.manager = User.query.filter_by(id=form.manager.data).first()
        db.session.add(service)
        db.session.commit()
        flash(_('Service have been saved.'))
        return redirect(url_for('main.service_list'))

    page = request.args.get('page', 1, type=int)
    services = Service.query.order_by(Service.updated.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.service_list', page=services.next_num) if services.has_next else None
    prev_url = url_for('main.service_list', page=services.prev_num) if services.has_prev else None
    return render_template('service.html', form=form, services=services.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/service/edit', methods=['GET', 'POST'])
@login_required
def service_edit():
    if 'cancel' in request.form:
        return redirect(url_for('main.index'))

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Service modification is limited to admins'))
            return redirect(url_for('main.index'))

    servicename = request.args.get('name')
    service = Service.query.filter_by(name=servicename).first()
    if service is None:
        render_template('service.html', title=_('Service is not defined'))

    form = ServiceForm(formdata=request.form, obj=service)

    if request.method == 'POST' and form.validate_on_submit():
        # TODO remove not selected users ...
        service.users = []
        for u in form.users.data:
            user = User.query.filter_by(id=u).first()
            print("Adding: User: %s to: %s" % (user.username, service.name))
            service.users.append(user)
        service.manager = User.query.filter_by(id=form.manager.data).first()
        service.name = form.name.data
        service.lightcolor = form.lightcolor.data
        service.darkcolor = form.darkcolor.data

        db.session.commit()

        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.service_list'))

    else:

        pre_selected_users = [(su.id) for su in service.users]
        form = ServiceForm(users=pre_selected_users)
        form.manager.data = service.manager_id
        form.name.data = service.name
        form.darkcolor.data = service.darkcolor
        form.lightcolor.data = service.lightcolor
        return render_template('service.html', title=_('Edit Service'),
                               form=form)


@bp.route('/service/list/', methods=['GET', 'POST'])
@login_required
def service_list():
    page = request.args.get('page', 1, type=int)
    services = Service.query.order_by(Service.updated.desc()).paginate(
        page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.service_list', page=services.next_num) if services.has_next else None
    prev_url = url_for('main.service_list', page=services.prev_num) if services.has_prev else None
    return render_template('services.html', services=services.items,
                           title=_('List Services'),
                           next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    edituser = User.query.filter_by(username=current_user.username).first()
    if edituser is None:
        render_template('edit_profile.html', title=_('User is not found'))

    if form.validate_on_submit():

        edituser.about_me = form.about_me.data
        edituser.set_theme(form.theme.data)
        print(f'user theme: {edituser.theme}')
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = edituser.username
        form.theme.data = edituser.theme
        form.about_me.data = edituser.about_me
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

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Work registration is limited to admins / Service managers'))
            return redirect(url_for('main.index'))

    form = WorkForm()
    if 'cancel' in request.form:
        return redirect(url_for('main.index'))

    if 'selected_user' in session:
        user = User.query.filter_by(username=session['selected_user']).first()
        form.user.data = user.id
        form.service.choices = []
        for s in Service.query.all():
            for serviceuser in s.users:
                if serviceuser.username == user.username:
                    form.service.choices.extend([(s.id, s.name)])

    elif 'selected_service' in session:
        service = Service.query.filter_by(name=session['selected_service']).first()
        form.service.choices = [(service.id, service.name)]
        form.user.choices = [(u.id, u.username)
                             for u in service.users]

    if request.method == 'POST' and form.validate_on_submit():
        print("service: {}".format(form.service.data))
        service = Service.query.get(form.service.data)
        if service is None:
            flash(_('Service not found'))
            return redirect(url_for('main.index'))

        user = User.query.get(form.user.data)
        if user is None:
            flash(_('User not found'))
            return redirect(url_for('main.index'))

        work = Work(start=form.start.data,
                    stop=form.stop.data,
                    status=form.status.data)
        work.user = user
        work.service = service
        db.session.add(work)
        db.session.commit()
        flash(_('New work is now saved!'))

        new_work_mess = 'new work: %s\t%s\t%s\t@%s\nby %s\n ' % (
                         work.start, work.stop, work.service,
                         work.user.username, current_user.username)
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

        start = request.args.get('start')
        if start is not None:
            form.start.data = datetime.strptime(start, "%Y-%m-%d %H:%M")

        stop = request.args.get('stop')
        if stop is not None:
            form.stop.data = datetime.strptime(stop, "%Y-%m-%d %H:%M")

        xxuser = request.args.get('user')
        print(f'get-select-user: {xxuser}')
        if xxuser is not None:
            form.user.data = xxuser

        service = request.args.get('service')
        if service is not None:
            form.service.data = service

        # TODO figure out how to show work added by the current user this session
        return render_template('work.html', title=_('Add Work'),
                               form=form)


def select_user_for_weighted_work(service, start, stop):
    if service is None:
        print("select_user_for_weighted_work: Service none")
        return None

    if start is None:
        print("select_user_for_weighted_work: start none")
        return None

    if stop is None:
        print("select_user_for_weighted_work: stop none")
        return None

    day_start = "%d-%02d-%02d %s:%s" % (start.year, start.month, start.day, "00", "00")
    day_stop = "%d-%02d-%02d %s:%s" % (stop.year, stop.month, stop.day, "23", "59")
    dt_start = datetime.strptime(day_start, "%Y-%m-%d %H:%M")
    dt_stop = datetime.strptime(day_stop, "%Y-%m-%d %H:%M")
    print("finding user for work at service: {} start: {} stop: {}".format(service.name, start, stop))

    stats = users_stats(start, service)

    user_with_least_hours = None

    # TODO weird sort ...

    least_worked_hours = 10000
    # check on how many services a user work
    # TODO: able to add % work on a service then use that here

    available_users = []

    for au in service.users:
        print("available_users: user: {} works at service: {}".format(au.username, service.name))
        user_is_absent = 0
        absentees = Absence.query.filter((Absence.user_id == au.id)
                                         # & ((Absence.start >= start) & (Absence.stop <= start)  # absence stop after shift start , ends before/same as shift stop
                                         #    | (Absence.start >= start) & (Absence.stop <= stop)   # absence starts at/before shift starts and end at/before it ends
                                         #    | (Absence.start >= start) & (Absence.start <= stop)   # absence starts at/after shift starts but before it ends
                                         #    | (Absence.start <= start) & (Absence.stop >= stop)  # absence starts before shift and ends after shift or same as shift
                                         #    )
                                         ).all()

        for a in absentees:
            print("absence user: {} start: {} stop: {}".format(a.user.username, a.start, a.stop))
            if a.start >= start and a.stop <= start:
                print("abcense matching1, user: {} should not work during {} to {}".format(a.user.username, a.start, a.stop))
                user_is_absent = 1

            elif a.start >= start and a.stop <= stop:
                print("abcense matching2, user: {} should not work during {} to {}".format(a.user.username, a.start, a.stop))
                user_is_absent = 1

            elif a.start >= stop and a.start <= stop:
                print("abcense matching3, user: {} should not work during {} to {}".format(a.user.username, a.start, a.stop))
                user_is_absent = 1

            elif a.start <= stop and a.stop >= stop:
                print("abcense matching4, user: {} should not work during {} to {}".format(a.user.username, a.start, a.stop))
                user_is_absent = 1

        if user_is_absent == 0:
            print("Adding user {} to list is no absent".format(au.username))
            available_users.append(au)
        else:
            print("Will NOT add user {} to list is absent".format(au.username))

    final_set_of_users = []

    for user2 in available_users:
        print("available_users: user: {} works at service and is not absent: {}".format(user2.username, service.name))
        user_already_working = 0

        already_working = Work.query.filter((Work.user_id == user2.id)
                                            & (Work.start >= dt_start)
                                            & (Work.stop <= dt_stop)
                                            ).all()
        for w in already_working:
            for remove_working_user in available_users:
                if remove_working_user.username == w.user.username:
                    print("user: {} is already working {} to {} at: {} not assigning any work".format(w.user.username, w.start, w.stop, w.service))
                    user_already_working = 1
        if user_already_working == 0:
            final_set_of_users.append(user2)
            print("Adding user {} to list is no absent".format(au.username))
        else:
            print("Will NOT add user {} to list is absent".format(au.username))

    for user in final_set_of_users:

        print("final round: User: {} has {} h".format(user.username, stats[user.username]))
        if stats[user.username] < least_worked_hours:
            print("Selecting: {}({}) over {} ({})".format(user, stats[user.username], user_with_least_hours, least_worked_hours))
            user_with_least_hours = user.username
            least_worked_hours = stats[user.username]

    print("Final Select: {}({})\n".format(user_with_least_hours, least_worked_hours))
    return user_with_least_hours


def users_stats_oncall(month, service):

    if month is None:
        return -1
    else:
        print("month: {}".format(month))

    measure_start_month = month - relativedelta.relativedelta(months=12)
    measure_stop_month = month + relativedelta.relativedelta(months=1)
    measure_stop_date = "%s-%s-01 00:00:00" % (measure_stop_month.year, measure_stop_month.month)
    measure_start_date = "%s-%s-01 00:00:00" % (measure_start_month.year, measure_start_month.month)

    dt_measure_stop = datetime.strptime(measure_stop_date, "%Y-%m-%d %H:%M:%S")
    dt_measure_start = datetime.strptime(measure_start_date, "%Y-%m-%d %H:%M:%S")
    stats = {}
#    print("measuring oncalls for stats from: {} to {}".format(dt_measure_start, dt_measure_stop))

    for u in service.users:
        number_of_oncalls = 0
        oncall_list = Oncall.query.filter((Oncall.user_id == u.id)
                                          & (Oncall.start > dt_measure_start)
                                          & (Oncall.start < dt_measure_stop)
                                          ).all()
        import pprint
        pp = pprint.PrettyPrinter()
        pp.pprint(oncall_list)

        last_oncall = dt_measure_start
        for oc in oncall_list:
            if last_oncall < oc.stop:
                last_oncall = oc.stop
            number_of_oncalls += 1

        stats[u.username] = last_oncall
# TODO        stats[u.username]['number_of_oncalls'] = number_of_oncalls

    return stats


def select_user_for_weighted_oncall(service, start, stop):
    if service is None:
        print("select_user_for_weighted_work: Service none")
        return None

    if start is None:
        print("select_user_for_weighted_work: start none")
        return None

    if stop is None:
        print("select_user_for_weighted_work: stop none")
        return None

    day_start = "%d-%02d-%02d %s:%s" % (start.year, start.month, start.day, "00", "00")
    day_stop = "%d-%02d-%02d %s:%s" % (stop.year, stop.month, stop.day, "23", "59")
    dt_start = datetime.strptime(day_start, "%Y-%m-%d %H:%M")
    dt_stop = datetime.strptime(day_stop, "%Y-%m-%d %H:%M")

    stats = users_stats_oncall(start, service)
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(stats)

    available_users = service.users.copy()

    for au in available_users:
        print("user: {} works at service: {}".format(au.username, service.name))

        absentees = Absence.query.filter((Absence.user_id == au.id)
                                         & ((Absence.start > dt_start) & (Absence.start < dt_stop)
                                            | (Absence.stop > dt_start) & (Absence.stop < dt_stop)
                                            | (Absence.start < dt_start) & (Absence.stop > dt_stop)
                                            )
                                         ).all()

        for a in absentees:
            print("user: {} is absent during {} to {} not assigning any work".format(a.user.username, a.start, a.stop))
            if a.user in available_users:
                available_users.remove(a.user)
                continue

    since_last_oncall = dt_start
    selected_oncall_user = None
    for user in available_users:
        print("Checking: User: {} for {} {}-{}".format(user, service.name, start, stop))

        print("User: {} has last oncall at: {} vs last_oncall: {}".format(user.username, stats[user.username], since_last_oncall))

        if stats[user.username] < since_last_oncall:
            print("Selecting: {}({}) over {} ({})".format(user, stats[user.username], selected_oncall_user, since_last_oncall))
            selected_oncall_user = user.username
            since_last_oncall = stats[user.username]

    print("Oncall final Select: {}({})\n".format(selected_oncall_user, since_last_oncall))
    return selected_oncall_user


@bp.route('/work/add/month', methods=['GET', 'POST'])
@login_required
def work_add_month():

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Generate month is limited to admins / service managers'))
            return redirect(url_for('main.index'))

    form = GenrateMonthWorkForm()
    month = request.args.get('month')
    if 'cancel' in request.form:
        return redirect(url_for('main.index'))

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
                # TODO: make the shifts configurable
                fm_start = "%d-%02d-%02d %s:%s" % (selected_month.year, selected_month.month, i, "08", "00")
                fm_stop = "%d-%02d-%02d %s:%s" % (selected_month.year, selected_month.month, i, "12", "30")
                dt_fm_start = datetime.strptime(fm_start, "%Y-%m-%d %H:%M")
                dt_fm_stop = datetime.strptime(fm_stop, "%Y-%m-%d %H:%M")

                allwork = Work.query.filter((Work.service_id == service.id)).all()
                work_fm_exist = None
                for w in allwork:
                    if w.service.name == service.name and w.start == dt_fm_start and w.stop == dt_fm_stop:
                        work_fm_exist = True

                if not work_fm_exist:
                    work = Work(start=dt_fm_start,
                                stop=dt_fm_stop,
                                status=status)
                    print("New work, {}-{}".format(fm_start, fm_stop))
                    if status == "assigned":
                        selected_username = select_user_for_weighted_work(service, dt_fm_start, dt_fm_stop)
                        selected_user = User.query.filter_by(username=selected_username).first()
                        if selected_user is not None:
                            work.user = selected_user
                        else:
                            work.status = "unassigned"
                            print("failed to find the user object from the username {}".format(selected_username))

                    work.service = service
                    db.session.add(work)
                    db.session.commit()

                # TODO: make the shifts configurable
                em_start = "%d-%02d-%02d %s:%s" % (selected_month.year, selected_month.month, i, "12", "30")
                em_stop = "%d-%02d-%02d %s:%s" % (selected_month.year, selected_month.month, i, "17", "00")
                dt_em_start = datetime.strptime(em_start, "%Y-%m-%d %H:%M")
                dt_em_stop = datetime.strptime(em_stop, "%Y-%m-%d %H:%M")

                work_em_exist = None
                for w in allwork:
                    if w.service.name == service.name and w.start == dt_fm_start and w.stop == dt_fm_stop:
                        work_em_exist = True

                if not work_em_exist:

                    work = Work(start=dt_em_start,
                                stop=dt_em_stop,
                                status=status)
                    if status == "assigned":
                        selected_username2 = select_user_for_weighted_work(service, dt_em_start, dt_em_stop)
                        selected_user2 = User.query.filter_by(username=selected_username2).first()
                        if selected_user2 is not None:
                            work.user = selected_user2
                        else:
                            work.status = "unassigned"
                            print("failed to find the user object from the username {}".format(selected_username2))

                    work.service = service
                    db.session.add(work)
                    db.session.commit()

        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.index'))

    else:
        form.month.data = selected_month
        return render_template('generate_month_work.html', title=_('Add Work for a month'),
                               form=form)


@bp.route('/work/edit/', methods=['GET', 'POST'])
@login_required
def work_edit():

    workid = request.args.get('work')

    if 'cancel' in request.form:
        return redirect(url_for('main.index'))
    if 'delete' in request.form:
        return redirect(url_for('main.work_delete', work=workid))

    work = Work.query.get(workid)

    if work is None:
        render_template('service.html', title=_('Work is not defined'))

    form = WorkForm(obj=work)

    if request.method == 'POST' and form.validate_on_submit():
        if work.user is None:
            string_from = '%s\t%s\t%s\t@%s\t%s\n' % (work.start, work.stop,
                                                 work.service, _("none"),work.status)
        else:
            string_from = '%s\t%s\t%s\t@%s\t%s\n' % (work.start, work.stop,
                                                 work.service, work.user.username, work.status)
        service = Service.query.get(form.service.data)

        if current_app.config['ENFORCE_ROLES'] is True:
            user = User.query.filter_by(username=current_user.username).first()
            if user.role != "admin" and (form.status.data == "unassigned"):
                flash(_('Users may only change to wants/needs-out status, other are limited to admins'))
                return redirect(url_for('main.index'))
            if user.role != "admin" and form.user.data != user.id:
                flash(_('Users may only assign work to them self, other are limited to admins'))
                return redirect(url_for('main.index'))
            # if user.role != "admin" and (form.status.data != "wants-out" or form.status.data != "needs-out"):
            #     flash(_('Users may only take that is status: wants/needs-out, other are limited to admins'))

        if service is None:
            print("service is none...")

        elif work.service_id != service.id:
            userworksatservice = None
            for su in service.users:
                print(f'checking user: {su.id}/{su.username} against {form.user.data} for service: {service.name}')
                if form.user.data == su.id:
                    print(f'found user: {su.id}/{su.username} against {form.user.data} for service: {service.name}')
                    userworksatservice = True
            if userworksatservice != True:
                flashmsg = _('User/service illegal combination, user set no none, other changes saved.')
                print('User/service illegal combination, user set no none, other changes saved.')
                work.status = "unassigned"
                work.user_id = None
                work.user = None
                work.service = service
                work.service_id = service.id

        else:
            work.service = service
            work.service_id = service.id

        if form.user.data == 0:
            work.status = "unassigned"
            work.user_id = None
            work.user = None

        elif work.user_id != form.user.data:
            work.status = "assigned"
            work.user_id = form.user.data

        elif form.status.data == "unassigned":
            work.status = "unassigned"
            work.user_id = None
            work.user = None

        else:
            work.status = form.status.data

        work.start = form.start.data
        work.stop = form.stop.data

        db.session.commit()
        if work.user is not None:
            string_to = '%s\t%s\t%s\t@%s\t%s\n' % (work.start, work.stop,
                                                   work.service, work.user.username,
                                                   work.status)
        else:
            string_to = '%s\t%s\t%s\t%s\t%s\n' % (work.start, work.stop,
                                                  work.service, "none", work.status)

        if current_app.config['ROCKET_ENABLED']:
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket.chat_post_message('edit of work from: \n%s\nto:\n%s\nby: %s' % (
                                 string_from, string_to, current_user.username),
                                 channel=current_app.config['ROCKET_CHANNEL']
                                 ).json()
        flashmsg = _(f"Changed work: {string_from} to {string_to}.")
        flash(flashmsg)


        return redirect(url_for('main.index'))

    else:
        form.service.data = work.service_id
        form.user.data = work.user_id
        service = Service.query.get(work.service_id)

        user_stats = users_stats(work.start, service)
        onstats = oncall_stats(work.start, service)
        abstats = absence_stats(work.start, work.stop, work.service)
        users_working = users_work_within(work.start, work.stop, work.service)

        userlist = []
        userlist.extend([(0, f'- None -')])

        for su in work.service.users:
            userlist.extend([(su.id, f'{su.username} work: {user_stats[su.username]} h oncall: {onstats[su.username]} absent:{abstats[su.username]} shifts today: {users_working[su.username]}')])
        form.user.choices = userlist

#        form.user.choices = [(su.id, su.username) for su in work.service.users]

        return render_template('work.html', title=_('Edit Work'),
                               form=form)


@bp.route('/work/list/', methods=['GET', 'POST'])
@login_required
def work_list():

    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'start')
    order = request.args.get('order', 'asc')
    username = request.args.get('username')

    work_vars = list(vars(Work).keys())
    work_vars.append('username')
    work_vars.append('service')

    if sort not in work_vars:
        flash(_('No such varibale to sort by %s' % sort))
        return redirect(url_for('main.index'))

    if order not in ['asc', 'desc']:
        flash(_('Bad order to sort by'))
        return redirect(url_for('main.index'))

    if sort == 'username':
        sortstr = "{}(Work.{})".format(order, 'user_id')
        work = Work.query.order_by(eval(sortstr)).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])

    elif sort == 'service':
        sortstr = "{}(Work.{})".format(order, 'service_id')
        work = Work.query.order_by(eval(sortstr)).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])

    elif username is not None:
        u = User.query.filter(User.username == username).first_or_404()
        work = Work.query.filter(Work.user_id == u.id).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])

    else:
        sortstr = "{}(Work.{})".format(order, sort)
        work = Work.query.order_by(eval(sortstr)).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])

    next_url = url_for('main.work_list', page=work.next_num, sort=sort, order=order) \
        if work.has_next else None
    prev_url = url_for('main.work_list', page=work.prev_num, sort=sort, order=order) \
        if work.has_prev else None

    return render_template('work.html', title=_('Work'),
                           allwork=work.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/work/delete/', methods=['GET', 'POST'])
@login_required
def work_delete():

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Delete work is limited to admins / service managers'))
            return redirect(url_for('main.index'))

    workid = request.args.get('work')
    work = Work.query.get(workid)

    if work is None:
        flash(_('Work was not deleted, id not found!'))
        return redirect(url_for('main.index'))
    if work.user is not None:
        deleted_msg = 'Work deleted: %s\t%s\t%s\t@%s\n' % (work.start, work.stop,
                                                           work.service.name, work.user.username)
    else:
        deleted_msg = 'Work deleted: %s\t%s\t%s\t%s\n' % (work.start, work.stop,
                                                          work.service, "none")

    if current_app.config['ROCKET_ENABLED']:
        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])
        rocket.chat_post_message('work deleted: \n%s\n by: %s' % (
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
        return redirect(url_for('main.index'))

    form = AbsenceForm()

    if request.method == 'POST' and form.validate_on_submit():

        if current_app.config['ENFORCE_ROLES'] is True:
            user = User.query.filter_by(username=current_user.username).first()
            if user.role != "admin" and form.status.data != "requested":
                flash(_('status is changed to requested, only admins / service managers can directly approve'))
                form.status.data = "requested"

        absence = Absence(start=form.start.data,
                          stop=form.stop.data,
                          user_id=form.user.data,
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
                                 absence.user.username),
                                 channel=current_app.config['ROCKET_CHANNEL']
                                 ).json()

        return redirect(url_for('main.index'))
    else:
        day = request.args.get('day')
        month = request.args.get('month')
        if day is not None and month is not None:
            date_start_str = month + "-" + day + " 08:00"
            date_stop_str = month + "-" + day + " 17:00"

            form.start.data = datetime.strptime(date_start_str, "%Y-%m-%d %H:%M")
            form.stop.data = datetime.strptime(date_stop_str, "%Y-%m-%d %H:%M")

        return render_template('absence.html', title=_('Add absence'),
                               form=form)


@bp.route('/absence/edit/', methods=['GET', 'POST'])
@login_required
def absence_edit():

    absenceid = request.args.get('absence')
    absence = Absence.query.get(absenceid)

    if 'cancel' in request.form:
        return redirect(url_for('main.index'))

    if 'delete' in request.form:
        return redirect(url_for('main.absence_delete', absence=absenceid))

    if absence is None:
        render_template('service.html', title=_('absence is not defined'))

    form = AbsenceForm(formdata=request.form, obj=absence)

    if request.method == 'POST' and form.validate_on_submit():

        if current_app.config['ENFORCE_ROLES'] is True:
            user = User.query.filter_by(username=current_user.username).first()
            if user.role != "admin" and form.status.data != "requested":
                flash(_('status is changed to requested, only admins / service managers can directly approve'))
                form.status.data = "requested"

        rocket_msg_from = 'edit of absence from: \n%s\t%s\t%s\t@%s' % (absence.start,
                                                                       absence.stop,
                                                                       absence.status,
                                                                       absence.user.username)

        absence.start = form.start.data
        absence.stop = form.stop.data
        absence.user_id = form.user.data
        absence.status = form.status.data

        db.session.commit()
        flash(_('Your changes have been saved.'))
        if current_app.config['ROCKET_ENABLED']:
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket_msg_to = 'to: \n%s\t%s\t%s\t@%s ' % (absence.start,
                                                        absence.stop,
                                                        absence.status,
                                                        absence.user.username)
            rocket.chat_post_message("%s\n%s\n\nby: %s" % (rocket_msg_from,
                                                           rocket_msg_to,
                                                           current_user.username),
                                     channel=current_app.config['ROCKET_CHANNEL']
                                     ).json()

        return redirect(url_for('main.index'))

    else:
        form.user.data = absence.user_id

        return render_template('index.html', title=_('Edit absence'),
                               form=form)


@bp.route('/absence/list/', methods=['GET', 'POST'])
@login_required
def absence_list():

    page = request.args.get('page', 1, type=int)
    username = request.args.get('username')

    u = User.query.filter(User.username == username).first()

    if u is not None:

        absence = Absence.query.filter_by(Absence.user_id == u.id).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])

    else:
        absence = Absence.query.order_by(Absence.start).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])

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

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin" and absence.user_id != user.id:
            flash(_('Delete others absence is only available to admins / service managers'))
            return redirect(url_for('main.index'))

    deleted_msg = 'Absence deleted: %s\t%s\t%s\n' % (absence.start, absence.stop, absence.user.username)
    if current_app.config['ROCKET_ENABLED']:
        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])
        rocket.chat_post_message('absence deleted: \n%s\n by: %s' % (
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
        return redirect(url_for('main.index'))

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Add oncall is only available to admins / service managers'))
            return redirect(url_for('main.index'))

    if request.method == 'POST' and form.validate_on_submit():
        service = Service.query.get(form.service.data)
        if service is None:
            flash(_('service not found'))
            return redirect(url_for('main.index'))

        oncall = Oncall(start=form.start.data,
                        stop=form.stop.data,
                        user_id=form.user.data,
                        service_id=form.service.data,
                        status=form.status.data)

        if form.absenceday.data != 0:

            dt_absence_start = form.start.data + timedelta(days=-form.start.data.weekday() + form.absenceday.data - 1, weeks=1, hours=-form.start.data.hour + 8)
            dt_absence_stop = form.start.data + timedelta(days=-form.start.data.weekday() + form.absenceday.data - 1, weeks=1, hours=-form.start.data.hour + 17)

            absence = Absence(start=dt_absence_start,
                              stop=dt_absence_stop,
                              user_id=form.user.data)
            db.session.add(absence)

        db.session.add(oncall)
        db.session.commit()
        flash(_('New oncall is now posted!'))

        new_oncall_mess = 'new oncall: %s\t%s\t%s\t@%s\nby %s\n ' % (oncall.start,
                                                                     oncall.stop,
                                                                     oncall.service,
                                                                     oncall.user.username,
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
        return redirect(url_for('main.index'))

    oncallid = request.args.get('oncall')
    oncall = Oncall.query.get(oncallid)

    if oncall is None:
        render_template('main.index', title=_('oncall is not defined'))

    if 'delete' in request.form:
        return redirect(url_for('main.oncall_delete', oncall=oncallid))

    form = OncallForm(obj=oncall)
    if request.method == 'POST' and form.validate_on_submit():

        if current_app.config['ENFORCE_ROLES'] is True:
            user = User.query.filter_by(username=current_user.username).first()
            if user.role != "admin" and (form.status.date != "wants-out" or form.status.data != "needs-out"):
                flash(_('Edit oncall, other than requesting wants/needs out, is only available to admins / service managers'))
                return redirect(url_for('main.index'))

        if oncall.user is None:
            string_from = '%s\t%s\t%s\t@%s\n' % (oncall.start, oncall.stop,
                                                 oncall.service, _("none"))
        else:
            string_from = '%s\t%s\t%s\t@%s\n' % (oncall.start, oncall.stop,
                                                 oncall.service, oncall.user.username)

        oncall.status = form.status.data
        oncall.start = form.start.data
        oncall.stop = form.stop.data
        oncall.user_id = form.user.data
        oncall.service_id = form.service.data
        db.session.commit()

        if form.absenceday.data != 0:
            # TODO: add link to absence from oncall and update via that, this creates a duplicate off day ...
            dt_absence_start = form.start.data + timedelta(days=-form.start.data.weekday() + form.absenceday.data - 1, weeks=1, hours=-form.start.data.hour + 8)
            dt_absence_stop = form.start.data + timedelta(days=-form.start.data.weekday() + form.absenceday.data - 1, weeks=1, hours=-form.start.data.hour + 17)

            absence = Absence(start=dt_absence_start,
                              stop=dt_absence_stop,
                              user_id=form.user.data)
            db.session.add(absence)

        flash(_('Your changes have been saved.'))

        if current_app.config['ROCKET_ENABLED']:
            string_to = '%s\t%s\t%s\t@%s\n' % (oncall.start, oncall.stop,
                                               oncall.service, oncall.user.username)
            rocket = RocketChat(current_app.config['ROCKET_USER'],
                                current_app.config['ROCKET_PASS'],
                                server_url=current_app.config['ROCKET_URL'])
            rocket.chat_post_message('edit of oncall from: \n%s\nto:\n%s\nby: %s' % (
                                 string_from, string_to, current_user.username),
                                 channel=current_app.config['ROCKET_CHANNEL']
                                 ).json()

        return redirect(url_for('main.index'))

    else:
        form.user.data = oncall.user_id
        form.service.data = oncall.service_id
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
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    elif service is not None:
        oncall = Oncall.query.filter_by(service=service).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])
    else:
        oncall = Oncall.query.order_by(Oncall.start).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])

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

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Delete oncall is only available to admins / service managers'))
            return redirect(url_for('main.index'))

    deleted_msg = 'oncall deleted: %s\t%s\t%s @%s\n' % (oncall.start,
                                                        oncall.stop,
                                                        oncall.service,
                                                        oncall.user.username)
    if current_app.config['ROCKET_ENABLED']:
        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])
        rocket.chat_post_message('oncall deleted: \n%s\nby: %s' % (
                             deleted_msg, current_user.username),
                             channel=current_app.config['ROCKET_CHANNEL']
                             ).json()
    flash(deleted_msg)
    db.session.delete(oncall)
    db.session.commit()

    return redirect(url_for('main.index'))


@bp.route('/oncall/add/month', methods=['GET', 'POST'])
@login_required
def oncall_add_month():

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Generate oncall month is limited to admins / service managers'))
            return redirect(url_for('main.index'))

    form = GenrateMonthOncallForm()
    month = request.args.get('month')
    if 'cancel' in request.form:
        return redirect(url_for('main.index'))

    if month is not None:
        selected_month = datetime.strptime(month, "%Y-%m")
        session['selected_month'] = month
    elif 'selected_month' in session:
        month = session['selected_month']
        selected_month = datetime.strptime(month, "%Y-%m")
    else:
        selected_month = datetime.utcnow()

    form.service.choices = [(s.id, s.name) for s in Service.query.all()]

    if request.method == 'POST' and form.validate_on_submit():
        service = Service.query.filter_by(id=form.service.data).first()
        selected_month = form.month.data
        status = form.status.data

        c = calendar.Calendar()
        for i in c.itermonthdays(selected_month.year, selected_month.month):

            try:
                weekday = calendar.weekday(selected_month.year, selected_month.month, i)
            except ValueError:
                continue
            if weekday == calendar.MONDAY:
                # TODO: make the oncall start day configurable
                oncall_start = "%d-%02d-%02d %s:%s" % (selected_month.year, selected_month.month, i, "08", "00")
                dt_oncall_start = datetime.strptime(oncall_start, "%Y-%m-%d %H:%M")
                dt_oncall_stop = dt_oncall_start + relativedelta.relativedelta(days=7)
                oncall_check_exist = Oncall.query.filter((Oncall.service_id == service.id)
                                                         & (Oncall.start == dt_oncall_start)
                                                         & (Oncall.stop == dt_oncall_stop)
                                                         ).all()
                if not oncall_check_exist:
                    oncall = Oncall(start=dt_oncall_start,
                                    stop=dt_oncall_stop,
                                    status=status)
                    print("New oncall, {}-{}".format(dt_oncall_start, dt_oncall_stop))
                    if status == "assigned":
                        selected_username = select_user_for_weighted_oncall(service, dt_oncall_start, dt_oncall_stop)
                        selected_user = User.query.filter_by(username=selected_username).first()
                        if selected_user is not None:
                            oncall.user = selected_user
                            if form.oncallabsenceday.data != 0:
                                #        when ever the oncall starts - its weekday (find monday) + 1 week (next monday) + selected absence day
                                oncall_absence_day = dt_oncall_start - timedelta(days=-dt_oncall_start.weekday()) + timedelta(days=7) + timedelta(days=form.oncallabsenceday.data - 1)
                                # TODO make the start and end of day configurable
                                dt_absence_start = datetime(oncall_absence_day.year, oncall_absence_day.month, oncall_absence_day.day, 8, 0)
                                dt_absence_stop = datetime(oncall_absence_day.year, oncall_absence_day.month, oncall_absence_day.day, 17, 0)
                                absence = Absence(start=dt_absence_start,
                                                  stop=dt_absence_stop,
                                                  user_id=selected_user.id)
                                db.session.add(absence)
                        else:
                            oncall.status = "unassigned"
                            print("failed to find the user to assign for oncall {}".format(selected_username))

                    oncall.service = service
                    db.session.add(oncall)
                    db.session.commit()

        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.index'))

    else:
        form.month.data = selected_month
        return render_template('generate_month_oncall.html', title=_('Add Oncall for a month'),
                               form=form)


@bp.route('/nonworkingdays/add', methods=['GET', 'POST'])
@login_required
def nonworkingdays_add():
    if 'cancel' in request.form:
        return redirect(url_for('main.index'))

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Add of Non working days is only available to admins / service managers'))
            return redirect(url_for('main.index'))

    form = NonWorkingDaysForm()

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

        return redirect(url_for('main.nonworkingdays_list'))
    else:

        return render_template('nonworkingdays.html', title=_('Add nonworkingdays'),
                               form=form)


@bp.route('/nonworkingdays/edit/', methods=['GET', 'POST'])
@login_required
def nonworkingdays_edit():

    if 'cancel' in request.form:
        return redirect(url_for('main.index'))

    nonworkingdaysid = request.args.get('nwd')
    nwd = NonWorkingDays.query.get(nonworkingdaysid)

    if nwd is None:
        render_template('nonworkingdays.html',
                        title=_('nonworkingdays is not defined'))

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Edit of Non working days is only available to admins / service managers'))
            return redirect(url_for('main.index'))

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

        return redirect(url_for('main.nonworkingdays_list'))

    else:
        return render_template('index.html', title=_('Edit nonworkingdays'),
                               form=form)


@bp.route('/nonworkingdays/list/', methods=['GET', 'POST'])
@login_required
def nonworkingdays_list():

    page = request.args.get('page', 1, type=int)

    nonworkingdays = NonWorkingDays.query.order_by(NonWorkingDays.start).paginate(
            page=page, per_page=current_app.config['POSTS_PER_PAGE'])

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

    if current_app.config['ENFORCE_ROLES'] is True:
        user = User.query.filter_by(username=current_user.username).first()
        if user.role != "admin":
            flash(_('Delete of Non working days is only available to admins / service managers'))
            return redirect(url_for('main.index'))

    deleted_msg = 'nonworkingday deleted: %s\t%s\t%s\n' % (nonworkingday.start,
                                                           nonworkingday.stop,
                                                           nonworkingday.name)
    if current_app.config['ROCKET_ENABLED']:
        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])
        rocket.chat_post_message('nonworkingday deleted: \n%s\n by: %s' % (
                             deleted_msg, current_user.username),
                             channel=current_app.config['ROCKET_CHANNEL']
                             ).json()
    flash(deleted_msg)
    db.session.delete(nonworkingday)
    db.session.commit()

    return redirect(url_for('main.index'))
