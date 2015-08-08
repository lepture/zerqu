# coding: utf-8

from functools import wraps

from flask import request, session
from oauthlib.common import to_unicode
from flask_oauthlib.utils import decode_base64

from zerqu.libs.errors import NotAuth, NotConfidential, InvalidClient
from zerqu.libs.ratelimit import ratelimit
from zerqu.models import oauth, cache, current_user
from zerqu.models import AuthSession, OAuthClient


class ApiBlueprint(object):
    def __init__(self, name):
        self.name = name
        self.deferred = []

    def route(self, rule, **options):
        def wrapper(f):
            self.deferred.append((f, rule, options))
            return f
        return wrapper

    def register(self, bp, url_prefix=None):
        if url_prefix is None:
            url_prefix = '/' + self.name

        for f, rule, options in self.deferred:
            endpoint = options.pop("endpoint", f.__name__)
            bp.add_url_rule(url_prefix + rule, endpoint, f, **options)


def oauth_limit_params(login, scopes):
    if scopes is None:
        scopes = []

    user = AuthSession.get_current_user()
    if user:
        request._current_user = user
        return 'limit:sid:{0}'.format(session.get('id')), 600, 300

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
        return 'limit:client:{0}'.format(c.id), 600, 600
    return 'limit:ip:{0}'.format(request.remote_addr), 3600, 3600


def oauth_ratelimit(login, scopes):
    prefix, count, duration = oauth_limit_params(login, scopes)
    rv = ratelimit(prefix, count, duration)
    request._rate_remaining, request._rate_expires = rv


def cache_response(cache_time):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if current_user or request.method != 'GET':
                return f(*args, **kwargs)

            key = 'api:%s' % request.full_path
            response = cache.get(key)
            if response:
                return response
            response = f(*args, **kwargs)
            cache.set(key, response, cache_time)
            return response
        return decorated
    return wrapper


def require_oauth(login=True, scopes=None, cache_time=None):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            oauth_ratelimit(login, scopes)

            if cache_time is not None:
                return cache_response(cache_time)(f)(*args, **kwargs)

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
