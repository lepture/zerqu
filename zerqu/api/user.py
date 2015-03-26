# coding: utf-8

from flask import Blueprint
from flask import request, jsonify
from .base import require_oauth
from ..models import db, current_user, User

bp = Blueprint('api_user', __name__)


@bp.route('')
@require_oauth(login=True)
def view_current_user():
    return jsonify(current_user)


@bp.route('', methods=['PATCH'])
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


@bp.route('/email')
@require_oauth(login=True, scopes=['user:email'])
def view_current_user_email():
    return jsonify(email=current_user.email)
