# coding: utf-8

from flask import Blueprint
from flask import request, jsonify
from werkzeug.datastructures import MultiDict
from .base import require_oauth, require_confidential
from .base import cursor_query
from ..models import db, User, current_user
from ..forms import RegisterForm
from ..errors import FormError

bp = Blueprint('api_users', __name__)


@bp.route('', methods=['POST'])
@require_confidential
def create_user():
    form = RegisterForm(MultiDict(request.get_json()), csrf_enabled=False)
    if not form.validate():
        raise FormError(form)
    user = form.create_user()
    return jsonify(user), 201


@bp.route('')
@require_oauth(login=False, cache_time=300)
def list_users():
    data, cursor = cursor_query(User, 'desc')
    return jsonify(data=data, cursor=cursor)


@bp.route('/<username>')
@require_oauth(login=False, cache_time=600)
def view_user(username):
    user = User.cache.first_or_404(username=username)
    return jsonify(user)


@bp.route('/me')
@require_oauth(login=True)
def view_current_user():
    return jsonify(current_user)


@bp.route('/me', methods=['PATCH'])
@require_oauth(login=True, scopes=['user:write'])
def update_current_user():
    user = User.query.get(current_user.id)
    # TODO: use form to validate
    description = request.get_json().get('description')
    if description:
        user.description = description
        db.session.add(user)
        db.session.commit()
    return jsonify(user)


@bp.route('/me/email')
@require_oauth(login=True, scopes=['user:email'])
def view_current_user_email():
    return jsonify(email=current_user.email)
