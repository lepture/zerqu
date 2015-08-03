# coding: utf-8

from flask import Blueprint
from flask import current_app, url_for, request, session
from flask import abort, redirect, render_template
from werkzeug.security import gen_salt
from ..libs.cache import redis, cache, ONE_DAY
from ..libs.utils import full_url
from ..libs.pigeon import send_text
from ..models import db, current_user, SocialUser, User, AuthSession
from ..forms import RegisterForm, PasswordForm, EmailForm

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
            token = create_signature(email, 'signup')
            url = url_for('.handle_signup', token=token)
            return redirect(url)

    return 'TODO'


@bp.route('/-/<token>/signup', methods=['GET', 'POST'])
def handle_signup(token):
    email, key = get_email_or_404(token, 'signup')

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
def handle_change_password(token):
    email, key = get_email_or_404(token, 'password')
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
def handle_change_email(token):
    email, key = get_email_or_404(token, 'email')
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


def create_signature(email, alt='signup'):
    # save email to redis
    token = gen_salt(16)
    key = 'account:%s:%s' % (alt, token)
    redis.set(key, email.lower(), ONE_DAY)
    return token


def get_email_or_404(token, alt='signup'):
    key = 'account:%s:%s' % (alt, token)
    email = redis.get(key)
    if not email:
        return abort(404)
    return email, key


def is_duplicated_email(key):
    key = 'email:%s' % key
    if cache.get(key):
        return True
    cache.set(key, 1, 300)
    return False


def send_signup_email(email):
    if is_duplicated_email('signup:%s' % email):
        return
    token = create_signature(email, 'signup')
    url = full_url('account.handle_signup', token=token)
    title = 'Sign up account for %s' % current_app.config['SITE_NAME']
    text = '%s\n\n%s' % (title, url)
    send_text(email, title, text)


def send_change_password_email(email):
    if is_duplicated_email('password:%s' % email):
        return
    token = create_signature(email, 'password')
    title = 'Change password for %s' % current_app.config['SITE_NAME']
    url = full_url('account.handle_change_password', token=token)
    text = '%s\n\n%s' % (title, url)
    send_text(email, title, text)
