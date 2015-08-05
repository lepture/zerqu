
from flask import request
from werkzeug.local import LocalProxy
from .auth import oauth
from .user import AuthSession
from ..libs.utils import Empty


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

    user = AuthSession.get_current_user()

    if user is None and request.path.startswith('/api/'):
        _, req = oauth.verify_request([])
        user = req.user

    if user is None:
        return ANONYMOUS

    request._current_user = user
    return user


current_user = LocalProxy(_get_current_user)
