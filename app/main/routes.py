from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
from guess_language import guess_language
from app import db
from app.main.forms import EditProfileForm, PostForm, WorkForm, ServiceForm
from app.models import User, Work, Service
from app.translate import translate
from app.main import bp

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

    page = request.args.get('page', 1, type=int)
    work = Work.query.order_by(Work.updated.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=work.next_num) \
        if work.has_next else None
    prev_url = url_for('main.index', page=work.prev_num) \
        if work.has_prev else None
    return render_template('work.html', title=_('Work'),
                           allwork=work.items, next_url=next_url,
                           prev_url=prev_url)


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
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/service/', methods=['GET', 'POST'])
@login_required
def service():

    form=ServiceForm()

    if form.validate_on_submit():
        service = Service(name=form.name.data)
        db.session.add(service)
        db.session.commit()
        flash(_('Service have been saved.'))
        return redirect(url_for('main.service'))

    page = request.args.get('page', 1, type=int)
    services = Service.query.order_by(Service.updated.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.service', page=services.next_num) if services.has_next else None
    prev_url = url_for('main.service', page=services.prev_num) if services.has_prev else None
    return render_template('service.html', form=form, services=services.items,
                           next_url=next_url, prev_url=prev_url)

#    return render_template('service.html',form=form)


@bp.route('/service_list/', methods=['GET', 'POST'])
@login_required
def service_list():
    page = request.args.get('page', 1, type=int)
    services = Service.query.order_by(Service.updated.desc()).paginate(
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.service', page=services.next_num) if services.has_next else None
    prev_url = url_for('main.service', page=services.prev_num) if services.has_prev else None
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


@bp.route('/work/add')
@login_required
def work_add():
    form = WorkForm()
    if form.validate_on_submit():
#        service = Service.query.filter_by(name=form.service.data).first()
        work = Work(start=form.start.data,
        stop=form.stop.data,username=form.username.data,
        service=form.service.data,status=form.status.data) #,service_id=service.id
        db.session.add(work)
        db.session.commit()
        flash(_('New work is now posted!'))
        return redirect(url_for('main.index'))

    return render_template('index.html', title=_('Add Work'),
                           form=form)



@bp.route('/work/edit/', methods=['GET', 'POST'])
@login_required
def work_edit():

    workid = request.args.get('work')
    work = Work.query.get(workid)

    if work is None:
        internal_error()

    form = WorkForm(formdata=request.form, obj=work)

    if request.method == 'POST' and form.validate_on_submit():
        form.populate_obj(work)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.index'))

    else:
        return render_template('index.html', title=_('Edit Work'),
                           form=form)
