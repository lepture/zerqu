
from flask import request
from werkzeug.local import LocalProxy
from zerqu.libs.utils import Empty
from .auth import oauth
from .user import User, UserSession


class Anonymous(Empty):
    id = None

    def __str__(self):
        return "Anonymous User"

    def __repr__(self):
        return "<User: Anonymous>"

ANONYMOUS = Anonymous()


def _get_current_user():
    user = getattr(request, '_current_user', None)
    if user:
        return user

    user = UserSession.get_current_user()

    if user is None and request.path.startswith('/api/'):
        _, req = oauth.verify_request([])
        user = req.user

    if user is None:
        return ANONYMOUS

    request._current_user = user
    return user


def iter_items_with_users(items, users=None):
    if not users:
        users = User.cache.get_dict([o.user_id for o in items])
    for item in items:
        data = dict(item)
        user = users.get(str(item.user_id))
        if user:
            data['user'] = dict(user)
        yield data


current_user = LocalProxy(_get_current_user)
