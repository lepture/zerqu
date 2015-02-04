# coding: utf-8

from flask import Blueprint, request
from flask import jsonify
from werkzeug.datastructures import MultiDict
from .base import require_oauth, require_confidential
from ..models import current_user
from ..forms import RegisterForm

bp = Blueprint('api_users', __name__)


@bp.route('/user', methods=['POST'])
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


@bp.route('/user')
@require_oauth(login=True)
def current_authenticated_user():
    return jsonify(status='ok', data=current_user)
