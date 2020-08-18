from app.api import bp
from flask import jsonify, current_app
from app.models import Work, User, Service
from flask import url_for
from app import db
from app.api.errors import bad_request
from flask import request
from app.api.auth import token_auth
from rocketchat_API.rocketchat import RocketChat
from datetime import datetime


@bp.route('/work', methods=['POST'])
@token_auth.login_required
def create_work():
    data = request.get_json() or {}
    if 'start' not in data or 'stop' not in data or \
       ('service_id' not in data and 'service_name' not in data):
        return bad_request('must include start,stop and service_name or service_id')

    if 'service_id' in data:
        check_service = Service.query.filter_by(id=data['service_id']).first()
    elif 'service_name' in data:
        check_service = Service.query.filter_by(name=data['service_name']).first()

    dt_start = datetime.strptime(data['start'], "%Y-%m-%d %H:%M")
    dt_stop = datetime.strptime(data['stop'], "%Y-%m-%d %H:%M")

    print("service: {}/{} start: {} stop {}".format(check_service.name, check_service.id, dt_start, dt_stop))

    allwork = Work.query.filter((Work.service_id == check_service.id)).all()
    for w in allwork:
        # print("work: service: {} start: {} stop: {} user: {}".format(w.service.name, w.start, w.stop, w.user.username))
        if w.service.name == check_service.name and w.start == dt_start and w.stop == dt_stop:
            print("matching service, start and stop: {}".format(check_service.name))
            status = {'msg': "service work record with matching start, stop and service exist", 'success': False, 'id': w.id}
            return bad_request(status)

    work = Work()

    if 'status' not in data:
        work.status = "unassigned"

    status = work.from_dict(data)
    if status['success'] is False:
        return bad_request(status['msg'])

    db.session.add(work)
    db.session.commit()
    response = jsonify(work.to_dict())
    if current_app.config['ROCKET_ENABLED']:
        rocket = RocketChat(current_app.config['ROCKET_USER'],
                            current_app.config['ROCKET_PASS'],
                            server_url=current_app.config['ROCKET_URL'])
        chatmsg = 'new work: %s\t%s\t%s\t@%s ' % (work.start, work.stop,
                                                  work.service, work.username)
        rocket.chat_post_message(chatmsg,
                                 channel=current_app.config['ROCKET_CHANNEL']).json()

    response.status_code = 201
    response.headers['Location'] = url_for('api.get_work', id=work.id)
    return response


@bp.route('/worklist', methods=['GET'])
@token_auth.login_required
def get_worklist():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Work.to_collection_dict(Work.query, page, per_page,
                                   'api.get_worklist')
    return jsonify(data)


@bp.route('/work/<int:id>', methods=['GET'])
@token_auth.login_required
def get_work(id):
    return jsonify(Work.query.get_or_404(id).to_dict())


@bp.route('/work/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_work(id):
    work = Work.query.get_or_404(id)
    data = request.get_json() or {}
    user = User.query.filter_by(username=data['username']).first()
    if 'username' in data or user:
        return bad_request('please use a different username')

    work.from_dict(data, new_work=False)
    db.session.commit()
    return jsonify(work.to_dict())
