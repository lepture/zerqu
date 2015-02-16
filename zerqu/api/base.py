# coding: utf-8

from functools import wraps
from flask import request, session
from oauthlib.common import to_unicode
from flask_oauthlib.utils import decode_base64
from .errors import APIException
from ..models import db, oauth, cache, current_user
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
        raise APIException(
            401,
            'authorization_required',
            'Authorization is required'
        )

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
            raise APIException(
                400,
                'invalid_client',
                'Client of %s not found' % client_id,
            )
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
                raise APIException(
                    code=429,
                    error='limit_exceeded',
                    description=(
                        'Rate limit exceeded, retry in %is'
                    ) % expires
                )
            request._rate_remaining = remaining
            request._rate_expires = expires

            if request.method == 'GET' and isinstance(cache_time, int):
                key = 'api:%s' % request.full_path
                if login:
                    key = '%s:%d' % (key, current_user.id)
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
        error = APIException(
            code=403,
            error='confidential_only',
            description='Only confidential clients are allowed'
        )
        if not auth:
            raise error
        try:
            _, s = auth.split(' ')
            client_id, client_secret = decode_base64(s).split(':')
            client_id = to_unicode(client_id, 'utf-8')
            client_secret = to_unicode(client_secret, 'utf-8')
        except:
            raise error
        client = oauth._clientgetter(client_id)
        if not client or client.client_secret != client_secret:
            raise error
        if not client.is_confidential:
            raise error
        return f(*args, **kwargs)
    return decorated


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


def int_or_raise(key, value=0, maxvalue=None):
    try:
        num = int(request.args.get(key, value))
        if maxvalue is not None and num > maxvalue:
            return maxvalue
        return num
    except ValueError:
        raise APIException(
            description='Require int type on %s parameter' % key
        )


def cursor_query(model, order_by='desc'):
    """Return a cursor query on the given model. The model must has id as
    the primary key.
    """
    before = int_or_raise('before')
    after = int_or_raise('after')
    count = int_or_raise('count', 20, 100)
    if before and after:
        desc = (
            'Parameters conflict, before and after should not appear '
            'at the same time.'
        )
        raise APIException(description=desc)

    query = db.session.query(model.id)
    if before:
        query = query.filter(model.id < before)
    elif after:
        query = query.filter(model.id > after)

    if order_by == 'desc':
        query = query.order_by(model.id.desc())

    ids = [i for i, in query.limit(count)]
    data = model.cache.get_many(ids)

    cursor = {'key': 'id'}
    if len(data) < count:
        return data, cursor
    cursor['before'] = data[-1].id
    cursor['after'] = data[0].id
    return data, cursor


def pagination(total):
    page = int_or_raise('page', 1)
    if page < 1:
        raise APIException('page should be larger than 1')

    perpage = int_or_raise('perpage', 20, 100)
    if perpage < 10:
        raise APIException('perpage should be larger than 10')

    pages = int((total - 1) / perpage) + 1

    rv = {
        'total': total,
        'pages': pages,
        'page': page,
        'prev': None,
        'next': None,
    }

    if page > 1:
        rv['prev'] = page - 1
    if page < pages:
        rv['next'] = page + 1
    return rv
