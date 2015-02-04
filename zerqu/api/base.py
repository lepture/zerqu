# coding: utf-8

from flask import Blueprint
from flask import jsonify
from flask import request, json, session
from werkzeug.exceptions import HTTPException
from werkzeug._compat import text_type
from functools import wraps
from ..models import AuthSession, OAuthClient
from ..models.auth import oauth
from ..libs.ratelimit import ratelimit
from ..versions import VERSION, API_VERSION

bp = Blueprint('api', __name__)


class APIException(HTTPException):
    error_code = 'invalid_request'

    def __init__(self, code=None, error=None, description=None, response=None):
        if code is not None:
            self.code = code
        if error is not None:
            self.error_code = error
        super(APIException, self).__init__(description, response)

    def get_body(self, environ=None):
        return text_type(json.dumps(dict(
            status='error',
            error_code=self.error_code,
            error_description=self.description,
        )))

    def get_headers(self, environ=None):
        return [('Content-Type', 'application/json')]


def generate_limit_params(scopes):
    user = AuthSession.get_current_user()
    if user:
        request._current_user = user
        return 'limit:sid:%s' % session.get('id'), 600, 300

    valid, req = oauth.verify_request(scopes)
    if scopes and not valid:
        raise APIException(
            401,
            'authorization_required',
            'Authorization is required'
        )

    if valid:
        request._current_user = req.user
        # TODO
        key = 'limit:%s-%d' % (req.client_id, req.user.id)
        return key, 600, 600

    client_id = request.values.get('client_id')
    if client_id:
        c = OAuthClient.query.filter_by(
            client_id=client_id
        ).first()
        if not c:
            raise APIException(
                400,
                'invalid_client',
                'Client not found on client_id',
            )
        return 'limit:%d' % c.id
    return 'limit:ip:%s' % request.remote_addr, 3600, 3600


def require_oauth(*scopes):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            prefix, count, duration = generate_limit_params(scopes)
            remaining, expires = ratelimit(prefix, count, duration)
            if remaining <= 0 and expires:
                raise APIException(
                    code=429,
                    error='limit_exceeded',
                    description=(
                        'Rate limit exceeded, retry in %is'
                    ) % expires
                )
            request._rate_remaining = remaining
            request._rate_expires = expires
            return f(*args, **kwargs)
        return decorated
    return wrapper


@bp.after_request
def ratelimit_hook(response):
    if hasattr(request, '_rate_remaining'):
        response.headers['X-Rate-Limit'] = str(request._rate_remaining)
    if hasattr(request, '_rate_expires'):
        response.headers['X-Rate-Expires'] = str(request._rate_expires)

    # javascript can request API
    response.headers['Access-Control-Allow-Origin'] = '*'
    # api not available in iframe
    response.headers['X-Frame-Options'] = 'deny'
    # security protection
    response.headers['Content-Security-Policy'] = "default-src 'none'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@bp.route('/')
def index():
    return jsonify(status='ok', data=dict(
        system='zerqu',
        version=VERSION,
        api_version=API_VERSION,
    ))
