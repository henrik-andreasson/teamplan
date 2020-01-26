from flask import jsonify, g
from app import db
from app.api import bp

@bp.route('/apikey', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = g.current_user.get_api_key()
    db.session.commit()
    return jsonify({'token': token})


@bp.route('/apikey', methods=['DELETE'])
@basic_auth.login_required
def revoke_token():
    g.current_user.revoke_api_key()
    db.session.commit()
    return '', 204
