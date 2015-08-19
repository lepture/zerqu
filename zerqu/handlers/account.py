# coding: utf-8

from flask import Blueprint
from flask import url_for, request, session
from flask import abort, redirect, render_template
from zerqu.libs.cache import redis
from zerqu.libs.utils import full_url
from zerqu.models import db, current_user, SocialUser, User, AuthSession
from zerqu.forms import (
    RegisterForm,
    PasswordForm,
    FindPasswordForm,
    EmailForm,
)
from .sendmails import create_email_signature, get_email_from_signature
from .sendmails import send_change_password_email

bp = Blueprint('account', __name__, template_folder='templates')


@bp.route('/s/<name>')
def social_login(name):
    remote = SocialUser.get_remote_app(name)
    if not remote:
        abort(404)

    session['next_url'] = request.referrer or '/'
    callback = full_url('.social_authorize', name=name)
    return remote.authorize(callback=callback)


@bp.route('/s/<name>/authorize')
def social_authorize(name):
    social = SocialUser.handle_authorized_response(name)
    if social is None:
        return 'error'

    if current_user and not social.user_id:
        social.user_id = current_user.id
        with db.auto_commit():
            db.session.add(social)

    if social.user_id:
        user = User.cache.get(social.user_id)
        AuthSession.login(user, True)
        next_url = session.pop('next_url', '/')
        return redirect(next_url)

    session['social.service'] = social.service
    session['social.uuid'] = social.uuid

    if name == 'google' and social.info.get('verified_email'):
        email = social.info.get('email')
        if email:
            token = create_email_signature(email, 'signup')
            url = url_for('.signup', token=token)
            return redirect(url)

    return 'TODO'


@bp.route('/find-password', methods=['GET', 'POST'])
def find_password():
    form = FindPasswordForm()
    message = None
    if form.validate_on_submit():
        send_change_password_email(form.user.email)
        message = 'We have sent you an email, check your inbox'
    return render_template(
        'account/find-password.html',
        form=form,
        message=message,
    )


@bp.route('/-/<token>/signup', methods=['GET', 'POST'])
def signup(token):
    email, key = get_email_from_signature(token, 'signup')

    social_service = session.get('social.service')
    social_uuid = session.get('social.uuid')
    if social_service and social_uuid:
        social = SocialUser.query.get((social_service, social_uuid))
        if social.user_id:
            social = None
    else:
        social = None

    form = RegisterForm()
    form.email.data = email
    if form.validate_on_submit():
        user = form.create_user()
        redis.delete(key)

        if social:
            session.pop('social.service', None)
            session.pop('social.uuid', None)
            social.user_id = user.id
            with db.auto_commit():
                db.session.add(social)

        AuthSession.login(user, True)
        return redirect('/')

    return render_template(
        'account/signup.html',
        form=form,
        email=email,
        social=social,
    )


@bp.route('/-/<token>/password', methods=['GET', 'POST'])
def change_password(token):
    email, key = get_email_from_signature(token, 'password')
    user = User.query.filter_by(email=email).first_or_404()
    form = PasswordForm()

    if form.validate_on_submit():
        user.password = form.password.data
        with db.auto_commit():
            db.session.add(user)
        redis.delete(key)
        return redirect('/')
    return render_template(
        'account/password.html',
        form=form,
        user=user,
    )


@bp.route('/-/<token>/email', methods=['GET', 'POST'])
def change_email(token):
    email, key = get_email_from_signature(token, 'email')
    user = User.query.filter_by(email=email).first_or_404()
    form = EmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        with db.auto_commit():
            db.session.add(user)
        redis.delete(key)
        return redirect('/')
    return render_template(
        'account/email.html',
        form=form,
        user=user,
    )
