# coding: utf-8

from functools import wraps
from flask import request, session
from oauthlib.common import to_unicode
from flask_oauthlib.utils import decode_base64
from ..errors import NotAuth, NotConfidential
from ..errors import LimitExceeded, InvalidClient
from ..models import oauth, cache, current_user
from ..models import AuthSession, OAuthClient
from ..libs.ratelimit import ratelimit


def generate_limit_params(login, scopes):
    if scopes is None:
        scopes = []

    user = AuthSession.get_current_user()
    if user:
        request._current_user = user
        return 'limit:sid:%s' % session.get('id'), 600, 300

    valid, req = oauth.verify_request(scopes)
    if login and (not valid or not req.user):
        raise NotAuth()

    if valid:
        request.oauth_client = req.access_token.client
        request._current_user = req.user
        key = 'limit:tok:%s' % req.access_token.access_token
        return key, 600, 600

    client_id = request.values.get('client_id')
    if client_id:
        c = OAuthClient.query.filter_by(
            client_id=client_id
        ).first()
        if not c:
            description = 'Client of %s not found' % client_id
            raise InvalidClient(description=description)

        request.oauth_client = c
        return 'limit:client:%d' % c.id, 600, 600
    return 'limit:ip:%s' % request.remote_addr, 3600, 3600


def require_oauth(login=True, scopes=None, cache_time=None):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            prefix, count, duration = generate_limit_params(login, scopes)
            remaining, expires = ratelimit(prefix, count, duration)
            if remaining <= 0 and expires:
                description = 'Rate limit exceeded, retry in %is' % expires
                raise LimitExceeded(description=description)

            request._rate_remaining = remaining
            request._rate_expires = expires

            # don't cache when user is logged in
            if current_user:
                return f(*args, **kwargs)

            if request.method == 'GET' and cache_time is not None:
                key = 'api:%s' % request.full_path
                response = cache.get(key)
                if response:
                    return response
                response = f(*args, **kwargs)
                cache.set(key, response, cache_time)
                return response
            return f(*args, **kwargs)
        return decorated
    return wrapper


def require_confidential(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth:
            raise NotConfidential()
        try:
            _, s = auth.split(' ')
            client_id, client_secret = decode_base64(s).split(':')
            client_id = to_unicode(client_id, 'utf-8')
            client_secret = to_unicode(client_secret, 'utf-8')
        except:
            raise NotConfidential()
        client = oauth._clientgetter(client_id)
        if not client or client.client_secret != client_secret:
            raise NotConfidential()
        if not client.is_confidential:
            raise NotConfidential()
        return f(*args, **kwargs)
    return decorated


def headers_hook(response):
    if hasattr(request, '_rate_remaining'):
        response.headers['X-Rate-Limit'] = str(request._rate_remaining)
    if hasattr(request, '_rate_expires'):
        response.headers['X-Rate-Expires'] = str(request._rate_expires)

    # javascript can request API
    if request.method == 'GET':
        response.headers['Access-Control-Allow-Origin'] = '*'

    # api not available in iframe
    response.headers['X-Frame-Options'] = 'deny'
    # security protection
    response.headers['Content-Security-Policy'] = "default-src 'none'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response
