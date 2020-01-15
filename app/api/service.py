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


@bp.route('/service', methods=['POST'])
def create_service():
    data = request.get_json() or {}
    if 'name' not in data or 'color' not in data:
        return bad_request('must include name and color fields')

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
    data = Service.to_collection_dict(Service.query, page, per_page, 'api.get_service')
    return jsonify(data)


@bp.route('/service/<int:id>', methods=['GET'])
@token_auth.login_required
def get_service(id):
    return jsonify(Service.query.get_or_404(id).to_dict())


@bp.route('/service/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_service(id):
    service = Service.query.get_or_404(id)
    data = request.get_json() or {}
    service.from_dict(data, new_service=False)
    db.session.commit()
    return jsonify(work.to_dict())



@bp.route('/service/adduser', methods=['POST'])
def add_user_to_service():

    data = request.get_json() or {}
    if 'service' not in data or 'username' not in data:
        return bad_request('must include service(name) and username fields')

    service = Service.query.filter_by(name=data['service']).first()
    user = User.query.filter_by(username=data['username']).first()

    service.users.append(user)
    db.session.commit()
    response = jsonify(service.to_dict())

    response.status_code = 201
    response.headers['Location'] = url_for('api.get_service', id=service.id)
    return response
