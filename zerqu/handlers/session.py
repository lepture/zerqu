# coding: utf-8

from flask import Blueprint
from flask import request
from flask import jsonify
from ..errors import LimitExceeded
from ..models import User, AuthSession


bp = Blueprint('session', __name__)


@bp.route('', methods=['POST', 'DELETE'])
def session():
    if request.method == 'DELETE':
        if AuthSession.logout():
            return jsonify(status='ok')
        return jsonify(status='error'), 400

    if request.mimetype != 'application/json':
        return jsonify(status='error'), 400

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify(
            status='error',
            error_code='missing_required_field',
            error_description='Username and password are required.'
        ), 400

    # can only try login a user 5 times
    prefix = 'limit:login:{0}:{1}'.format(username, request.remote_addr)
    LimitExceeded.raise_on_limit(prefix, 5, 3600)

    prefix = 'limit:login:{0}'.format(request.remote_addr)
    LimitExceeded.raise_on_limit(prefix, 60, 3600)

    if '@' in username:
        user = User.cache.filter_first(email=username)
    else:
        user = User.cache.filter_first(username=username)

    if not user or not user.check_password(password):
        return jsonify(
            status='error',
            error_code='login_failed',
            error_description='Invalid username or password.'
        ), 400
    permanent = data.get('permanent', False)
    AuthSession.login(user, permanent)
    return jsonify(user), 201
