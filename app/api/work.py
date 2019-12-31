from app.api import bp
from flask import jsonify, current_app
from app.models import Work, User, Service
from flask import url_for
from app import db
from app.api.errors import bad_request
from flask import request
# from flask import g, abort
from app.api.auth import token_auth
from pprint import pprint
from rocketchat_API.rocketchat import RocketChat


@bp.route('/work', methods=['POST'])
def create_work():
    data = request.get_json() or {}
    if 'start' not in data or 'stop' not in data or \
       'service' not in data:
        return bad_request('must include start,stop,servicefields')

    work = Work()
    work.from_dict(data, new_work=True)
    if 'status' not in data:
        work.status = "unassigned"

    service = Service.query.filter_by(name=data['service']).first()
    work.color = service.color

    db.session.add(work)
    db.session.commit()
    response = jsonify(work.to_dict())
    rocket = RocketChat(current_app.config['ROCKET_USER'], current_app.config['ROCKET_PASS'], server_url=current_app.config['ROCKET_URL'])
    rocket.chat_post_message('new work: %s\t%s\t%s\t@%s ' % (work.start,work.stop,work.service,work.username), channel=current_app.config['ROCKET_CHANNEL']).json()


    response.status_code = 201
    response.headers['Location'] = url_for('api.get_work', id=work.id)
    return response


@bp.route('/worklist', methods=['GET'])
@token_auth.login_required
def get_worklist():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Work.to_collection_dict(Work.query, page, per_page, 'api.get_work')
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
    if 'username' in data and User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')

    work.from_dict(data, new_work=False)
    db.session.commit()
    return jsonify(work.to_dict())
