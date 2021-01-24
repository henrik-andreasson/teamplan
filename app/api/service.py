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

# TODO: check role = admin ...  
@bp.route('/service', methods=['POST'])
@token_auth.login_required
def create_service():
    data = request.get_json() or {}
    if 'name' not in data or 'color' not in data:
        return bad_request('must include name and color fields')

    check_service = Service.query.filter_by(name=data['name']).first()
    if check_service is not None:
        return bad_request('Service already exist with id: %s' % check_service.id)

    service = Service()
    service.from_dict(data, new_service=True)

    db.session.add(service)
    db.session.commit()
    response = jsonify(service.to_dict())

    response.status_code = 201
    response.headers['Location'] = url_for('api.get_service', id=service.id)
    return response


@bp.route('/servicelist', methods=['GET'])
@token_auth.login_required
def get_servicelist():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Service.to_collection_dict(Service.query, page, per_page, 'api.get_servicelist')
    return jsonify(data)


@bp.route('/service/<int:id>', methods=['GET'])
@bp.route('/service/<name>', methods=['GET'])
@token_auth.login_required
def get_service(id=None, name=None):
    if id is not None:
        return jsonify(Service.query.get_or_404(id).to_dict())
    elif name is not None:
        return jsonify(Service.query.filter_by(name=name).first_or_404().to_dict())
    else:
        return bad_request('must include service-name or -id')


@bp.route('/service/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_service(id):
    service = Service.query.get_or_404(id)
    data = request.get_json() or {}
    service.from_dict(data, new_service=False)
    db.session.commit()
    return jsonify(service.to_dict())


@bp.route('/service/<servicename>/adduser/<username>', methods=['POST'])
@token_auth.login_required
def add_user_to_service(servicename=None, username=None):

    if servicename is None:
        return bad_request('must include servicename in url')

    if username is None:
        return bad_request('must include username fields')

    print("service: {} and user: {}".format(servicename, username))
    service = Service.query.filter(Service.name == servicename).first_or_404()
    user = User.query.filter(User.username == username).first()

    if service is None:

        retdata = {}
        retdata['message'] = "Can not find service"
        response = jsonify(retdata)
        response.status_code = 403
        return response

    if user is None:
        retdata = {}
        retdata['message'] = "Can not find user"
        retdata['user'] = username
        response = jsonify(retdata)
        response.status_code = 403
        return response

    for u in service.users:
        if user.username == u.username:
            return bad_request('User already member of the service')

    service.users.append(user)
    db.session.commit()
    response = jsonify(service.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_service', id=service.id)
    return response


@bp.route('/service/<int:id>/users', methods=['GET'])
@bp.route('/service/<name>/users', methods=['GET'])
@token_auth.login_required
def user_list(id=None, name=None):

    if name is not None:
        service = Service.query.filter(Service.name == name).first_or_404()
    elif id is not None:
        service = Service.query.get(id)
    else:
        return bad_request('must include user-name or id in URL')

    if service is None:
        return bad_request('Error retriving the service')

    response = jsonify(service.users_dict())
    response.status_code = 201
    return response


@bp.route('/service/<int:id>/manager/<username>', methods=['GET'])
@bp.route('/service/<servicename>/manager/<username>', methods=['GET'])
@token_auth.login_required
def manager_of_service(servicename=None, id=None, username=None):

    if servicename is None:
        return bad_request('must include servicename in url')

    if username is None:
        return bad_request('must include username fields')

    print("service: {} manager: {}".format(servicename, username))

    service = Service.query.filter(Service.name == servicename).first_or_404()
    user = User.query.filter_by(username=username).first()

    if service is None:

        retdata = {}
        retdata['message'] = "Can not find service"
        response = jsonify(retdata)
        response.status_code = 403
        return response

    if user is None:
        retdata = {}
        retdata['message'] = "Can not find user"
        retdata['user'] = username
        response = jsonify(retdata)
        response.status_code = 403
        return response

    service.manager = user
    db.session.commit()
    response = jsonify(service.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_service', id=service.id)
    return response
