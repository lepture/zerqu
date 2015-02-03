# coding: utf-8

import time
import logging
from flask import Blueprint
from flask import jsonify
from flask import request, json, session
from werkzeug.exceptions import HTTPException
from werkzeug._compat import text_type
from functools import wraps
from ..models import redis, AuthSession, OAuthClient
from ..models.auth import oauth

bp = Blueprint('api', __name__)

logger = logging.getLogger('zerqu.api')


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


def generate_limit_key():
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
    return 'limit:ip:%s' % request.remote_addr


def ratelimit(prefix=None, count=600, duration=300):
    if prefix is None:
        prefix = generate_limit_key()

    logger.info('Ratelimit on %s' % prefix)
    count_key = '%s$c' % prefix
    reset_key = '%s$r' % prefix
    remaining, resetting = redis.mget(count_key, reset_key)

    if not remaining and not resetting:
        remaining = count - 1
        expires_at = duration + int(time.time())
        with redis.pipeline() as pipe:
            pipe.set(count_key, remaining, ex=duration, nx=True)
            pipe.set(reset_key, expires_at, ex=duration, nx=True)
            pipe.execute()
        expires = duration
    else:
        expires = int(resetting) - int(time.time())
        if remaining <= 0 and expires:
            raise APIException(
                code=429,
                error='limit_exceeded',
                description=(
                    'Rate limit exceeded, retry in %is'
                ) % expires
            )
        remaining = int(remaining) - 1
        redis.set(count_key, remaining, ex=expires, xx=True)
    return remaining, expires


def require_oauth(*scopes):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = AuthSession.get_current_user()
            if user:
                request._current_user = user
                key = 'limit:sid:%s' % session.get('id')
                ratelimit(key, count=600, duration=300)
                return f(*args, **kwargs)
            valid, req = oauth.verify_request(scopes)
            if scopes and not valid:
                raise APIException(
                    401,
                    'authorization_required',
                    'Authorization is required'
                )
            if valid:
                request._current_user = req.user
                key = 'limit:%s-%d' % (req.client_id, req.user.id)
                ratelimit(key, count=600, duration=600)
            else:
                ratelimit(count=3600, duration=3600)
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
@require_oauth
def index():
    # TODO: add system information
    return jsonify(status='ok', data=dict(
        system='zerqu',
        version='0.1',
        api_version='0.1',
    ))
