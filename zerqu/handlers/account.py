# coding: utf-8

from flask import Blueprint, url_for, request, session
from flask import abort, redirect
from ..models import SocialUser, User, AuthSession

bp = Blueprint('account', __name__)


@bp.route('/s/<name>')
def social_login(name):
    remote = SocialUser.get_remote_app(name)
    if not remote:
        abort(404)

    session['next_url'] = request.referrer or '/'
    callback = url_for('.social_authorize', name=name, _external=True)
    return remote.authorize(callback=callback)


@bp.route('/s/<name>/authorize')
def social_authorize(name):
    data = SocialUser.handle_authorized_response(name)
    if data is None:
        return 'error'

    if data.user_id:
        user = User.cache.get(data.user_id)
        AuthSession.login(user, True)
        next_url = session.pop('next_url', '/')
        return redirect(next_url)
    return name


@bp.route('', methods=['POST'])
def request_change_password():
    pass


@bp.route('/-/<token>', methods=['GET', 'POST'])
def change_password(token):
    pass


def create_signature(email):
    # save email to redis
    return


def verify_signature(token):
    # verify in redis
    return True


def destroy_signature(token):
    # remove from redis
    pass
