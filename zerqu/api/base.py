# coding: utf-8

from flask import Blueprint
from flask import request, abort, jsonify
from functools import wraps
from ..models import AuthSession
from ..models.auth import oauth

bp = Blueprint('api', __name__)


def require_user(*scopes):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = AuthSession.get_current_user()
            if user:
                # TODO: verify scopes
                request._current_user = user
                return f(*args, **kwargs)
            valid, req = oauth.verify_request(scopes)
            if not valid:
                return abort(401)
            request._current_user = req.user
            return f(*args, **kwargs)
        return decorated
    return wrapper


@bp.errorhandler(401)
def handle_api_error(e):
    return jsonify(
        status="error",
        error_code="authorization_required",
        error_description="Authorization is required"
    )
