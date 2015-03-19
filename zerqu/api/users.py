# coding: utf-8

from flask import Blueprint
from flask import request, jsonify
from werkzeug.datastructures import MultiDict
from .base import require_oauth, require_confidential
from .base import cursor_query, first_or_404
from ..models import User
from ..forms import RegisterForm

bp = Blueprint('api_users', __name__)


@bp.route('', methods=['POST'])
@require_confidential
def create_user():
    form = RegisterForm(MultiDict(request.json), csrf_enabled=False)
    if not form.validate():
        return jsonify(
            error='invalid_form',
            error_form=form.errors,
        ), 400
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
    user = first_or_404(User, username=username)
    return jsonify(user)
