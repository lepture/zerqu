# coding: utf-8

from flask import Blueprint
from flask import request
from flask import jsonify
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
    return jsonify(status='ok', data=user), 201
