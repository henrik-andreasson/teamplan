from flask import render_template, flash, redirect, url_for, request, g, \
    current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
# from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, WorkForm, ServiceForm
from app.models import User, Work, Service
# from app.translate import translate
from app.main import bp
from calendar import Calendar
from datetime import datetime
from sqlalchemy import func


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    today = datetime.utcnow()
    output_month = []

    calendar = Calendar().monthdayscalendar(today.year, today.month)
    display_month = '{:02d}'.format(today.month)
    display_year = '{:02d}'.format(today.year)

    mon_week = 0
    for week in calendar:
        mon_week = mon_week + 1
        print ("week: %s" % mon_week)
        output_week = []
        weekday = 0
        for day in week:
            print ("day: %s" % day)
            weekday = weekday + 1

            day_info = {}
            if day != 0:
                display_day = '{:02d}'.format(day)
                day_info = {'display_day': display_day}

                date_min = "%s-%s-%s 00:00:00" % (display_year, display_month,
                                                  display_day)
                date_max = "%s-%s-%s 23:59:00" % (display_year, display_month,
                                                  display_day)
                print("search for work: %s %s" % (date_min, date_max))
                work = Work.query.filter(func.datetime(Work.start) > date_min,
                                         func.datetime(Work.stop) < date_max).all()

                day_info['work'] = work

            output_week.insert(weekday, day_info)

        output_month.insert(mon_week, output_week)
    return render_template('month.html', title=_('Month'), month=output_month)


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
    page = request.args.get('page', 1, type=int)
    users_work = Work.query.filter(Work.username == username).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=users_work.next_num) if users_work.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=users_work.prev_num) if users_work.has_prev else None
    return render_template('user.html', user=user, allwork=users_work.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/service/add', methods=['GET', 'POST'])
@login_required
def service_add():

    form = ServiceForm()

    if form.validate_on_submit():
        service = Service(name=form.name.data)
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

    form = ServiceForm()

    servicename = request.args.get('name')
    print("id: %s" % servicename)
    service = Service.query.filter_by(name=servicename).first()

    if service is None:
        render_template('service.html', title=_('Service is not defined'))

    form = ServiceForm(formdata=request.form, obj=service)

    if request.method == 'POST' and form.validate_on_submit():
        form.populate_obj(service)
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


@bp.route('/work/add', methods=['GET', 'POST'])
@login_required
def work_add():
    form = WorkForm()

    form.username.choices = [(u.username, u.username)
                             for u in User.query.all()]

    form.service.choices = [(s.name, s.name) for s in Service.query.all()]

    if request.method == 'POST' and form.validate_on_submit():
        service = Service.query.filter_by(name=form.service.data).first()
        work = Work(start=form.start.data,
                    stop=form.stop.data,
                    username=form.username.data,
                    service=form.service.data,
                    color=service.color,
                    status=form.status.data)
        db.session.add(work)
        db.session.commit()
        flash(_('New work is now posted!'))
        return redirect(url_for('main.index'))
    else:
        return render_template('work.html', title=_('Add Work'),
                               form=form)


@bp.route('/work/edit/', methods=['GET', 'POST'])
@login_required
def work_edit():

    workid = request.args.get('work')
    work = Work.query.get(workid)

    if work is None:
        render_template('service.html', title=_('Work is not defined'))

    form = WorkForm(formdata=request.form, obj=work)
    form.username.choices = [(u.username, u.username)
                             for u in User.query.all()]
    form.service.choices = [(s.name, s.name) for s in Service.query.all()]

    if request.method == 'POST' and form.validate_on_submit():
        form.populate_obj(work)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.index'))

    else:
        return render_template('index.html', title=_('Edit Work'),
                               form=form)


@bp.route('/work/list/', methods=['GET', 'POST'])
@login_required
def work_list():

    page = request.args.get('page', 1, type=int)
    username = request.args.get('username')
    service = request.args.get('service')

    if username is not None:
        work = Work.query.filter_by(username=username).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    elif service is not None:
        work = Work.query.filter_by(service=service).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    else:
        work = Work.query.order_by(Work.date).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.index', page=work.next_num) \
        if work.has_next else None
    prev_url = url_for('main.index', page=work.prev_num) \
        if work.has_prev else None

    for i in work.items:
        i.start = i.start.strftime("%H:%M")
        i.stop = i.stop.strftime("%H:%M")

    return render_template('work.html', title=_('Work'),
                           allwork=work.items, next_url=next_url,
                           prev_url=prev_url)