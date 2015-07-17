# coding: utf-8

from flask import Blueprint
from flask import session, request, jsonify
from ..errors import LimitExceeded
from ..models import User, AuthSession
from ..forms import RegisterEmailForm
from .account import send_signup_email, send_change_password_email


bp = Blueprint('session', __name__)


@bp.route('', methods=['POST', 'DELETE'])
def login_session():
    if request.method == 'DELETE':
        if AuthSession.logout():
            return '', 204
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
        return handle_login_failed(username, user)

    permanent = data.get('permanent', False)
    AuthSession.login(user, permanent)
    return jsonify(user), 201


@bp.route('/new', methods=['POST'])
def signup_session():
    form = RegisterEmailForm.create_api_form()
    send_signup_email(form.email.data)
    return jsonify(message='We have sent you an email for sign up.')


def handle_login_failed(username, user):
    last_username = session.get('login.username', None)

    if last_username != username:
        session['login.username'] = username
        session['login.count'] = 1
        count = 1
    else:
        count = session['login.count']
        count += 1
        session['login.count'] = count

    if count < 3:
        return jsonify(
            status='error',
            error_code='login_failed',
            error_description='Invalid username or password.'
        ), 400

    if count == 3 and user:
        send_change_password_email(user.email)
    elif count == 3 and '@' in username:
        send_signup_email(username)

    return jsonify(
        status='error',
        error_code='login_failed',
        error_description=(
            'We have sent you an email '
            'in case you forgot your password.'
        )
    ), 400
