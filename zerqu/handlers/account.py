# coding: utf-8

from flask import Blueprint, url_for, request, session
from flask import abort, redirect, render_template
from werkzeug.security import gen_salt
# TODO: use redis
from ..libs.cache import cache as redis
from ..libs.cache import ONE_DAY
from ..models import db, current_user, SocialUser, User, AuthSession
from ..forms import SignupForm, PasswordForm

bp = Blueprint('account', __name__, template_folder='templates')


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

    if current_user and not data.user_id:
        data.user_id = current_user.id
        with db.auto_commit():
            db.session.add(data)

    if data.user_id:
        user = User.cache.get(data.user_id)
        AuthSession.login(user, True)
        next_url = session.pop('next_url', '/')
        return redirect(next_url)

    session['social.service'] = data.service
    session['social.uuid'] = data.uuid

    if name == 'google' and data.info.get('verified_email'):
        email = data.info.get('email')
        if email:
            token = create_signature(email)
            url = url_for('.signup_or_change_password', token=token)
            return redirect(url)

    return 'TODO'


@bp.route('/-/<token>', methods=['GET', 'POST'])
def signup_or_change_password(token):
    key = 'account:sig:%s' % token
    email = redis.get(key)
    if not email:
        return abort(404)

    user = User.query.filter_by(email=email).first()
    social = None
    if user:
        form = PasswordForm()
    else:
        form = SignupForm()
        social_service = session.get('social.service')
        social_uuid = session.get('social.uuid')
        if social_service and social_uuid:
            social = SocialUser.query.get((social_service, social_uuid))
            if social.user_id:
                social = None

    if form.validate_on_submit():
        if not user:
            user = User(email=email, username=form.username.data.lower())

        user.password = form.password.data
        with db.auto_commit():
            db.session.add(user)

        if social:
            bind_social(social, user)

        redis.delete(key)
        AuthSession.login(user, True)
        return redirect('/')

    return render_template(
        'account/user.html',
        form=form,
        user=user,
        email=email,
        social=social,
    )


def create_signature(email):
    # save email to redis
    token = gen_salt(16)
    key = 'account:sig:%s' % token
    redis.set(key, email.lower(), ONE_DAY)
    return token


def bind_social(social, user):
    session.pop('social.service', None)
    session.pop('social.uuid', None)
    social.user_id = user.id
    with db.auto_commit():
        db.session.add(social)
