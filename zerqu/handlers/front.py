# coding: utf-8

from flask import Blueprint
from flask import request
from flask import jsonify
from zerqu.libs import render_template
from ..models import User, AuthSession


bp = Blueprint('front', __name__)


@bp.route('/')
def home():
    return render_template('index.html')


@bp.route('/session', methods=['POST', 'DELETE'])
def account():
    if request.method == 'DELETE':
        if AuthSession.logout():
            return jsonify(status='ok')
        return jsonify(status='error')

    if request.mimetype != 'application/json':
        return jsonify(status='error')

    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify(
            status='error',
            error_code='missing_required_field',
            error_description='Username and password are required.'
        )
    if '@' in username:
        user = User.query.filter_by(email=username).first()
    else:
        user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify(
            status='error',
            error_code='login_failed',
            error_description='Invalid username or password.'
        )
    AuthSession.login(user)
    return jsonify(status='ok', data=user), 201
