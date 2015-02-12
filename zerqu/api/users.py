# coding: utf-8

from flask import Blueprint, request
from flask import jsonify
from werkzeug.datastructures import MultiDict
from .base import require_oauth, require_confidential
from .base import cursor_query
from .errors import NotFound
from ..models import db, current_user, User
from ..forms import RegisterForm

bp = Blueprint('api_users', __name__)


@bp.route('/users', methods=['POST'])
@require_confidential
def create_user():
    form = RegisterForm(MultiDict(request.json), csrf_enabled=False)
    if not form.validate():
        return jsonify(
            status='error',
            error_code='error_form',
            error_form=form.errors,
        ), 400
    user = form.create_user()
    return jsonify(status='ok', data=user), 201


@bp.route('/users')
@require_oauth(login=False, cache_time=300)
def list_users():
    data = cursor_query(User, 'desc')
    return jsonify(status='ok', data=data)


@bp.route('/user')
@require_oauth(login=True)
def view_current_user():
    return jsonify(status='ok', data=current_user)


@bp.route('/user', methods=['PATCH'])
@require_oauth(login=True, scopes=['user:write'])
def update_current_user():
    user = User.query.get(current_user.id)
    # TODO: use form to validate
    description = request.json.get('description')
    if description:
        user.description = description
        db.session.add(user)
        db.session.commit()
    return jsonify(status='ok', data=user)


@bp.route('/users/<username>')
@require_oauth(login=False, cache_time=600)
def view_user(username):
    user = User.cache.filter_first(username=username)
    if not user:
        raise NotFound('User "%s"' % username)
    return jsonify(status='ok', data=user)
