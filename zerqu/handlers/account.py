# coding: utf-8

from flask import Blueprint
from flask import current_app, url_for, request, session
from flask import abort, redirect, render_template
from werkzeug.security import gen_salt
# TODO: use redis
from ..libs.cache import cache as redis
from ..libs.cache import ONE_DAY
from ..libs.utils import full_url
from ..libs.pigeon import mailer
from ..models import db, current_user, SocialUser, User, AuthSession
from ..forms import RegisterForm, PasswordForm

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
            token = create_signature(email)
            url = url_for('.handle_signup', token=token)
            return redirect(url)

    return 'TODO'


@bp.route('/-/<token>', methods=['GET', 'POST'])
def signup_or_change_password(token):
    email, key = get_email_or_404(token)
    user = User.query.filter_by(email=email).first()
    if user:
        return password_template(user, key)
    return signup_template(email, key)


@bp.route('/-/<token>/signup', methods=['GET', 'POST'])
def handle_signup(token):
    return signup_template(*get_email_or_404(token))


@bp.route('/-/<token>/password', methods=['GET', 'POST'])
def handle_change_password(token):
    email, key = get_email_or_404(token)
    user = User.query.filter_by(email=email).first_or_404()
    return password_template(user, key)


def password_template(user, key):
    form = PasswordForm()

    if form.validate_on_submit():
        user.password = form.password.data
        with db.auto_commit():
            db.session.add(user)
        redis.delete(key)
        AuthSession.login(user, True)
        return redirect('/')
    return render_template(
        'account/password.html',
        form=form,
        user=user,
    )


def signup_template(email, key):
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


def create_signature(email):
    # save email to redis
    token = gen_salt(16)
    key = 'account:sig:%s' % token
    redis.set(key, email.lower(), ONE_DAY)
    return token


def get_email_or_404(token):
    key = 'account:sig:%s' % token
    email = redis.get(key)
    if not email:
        return abort(404)
    return email, key


def send_signup_email(email):
    token = create_signature(email)
    url = full_url('account.handle_signup', token=token)
    title = 'Sign up account for %s' % current_app.config['SITE_NAME']
    text = '%s\n\n%s' % (title, url)
    mailer.send_text(email, title, text)


def send_change_password_email(email):
    token = create_signature(email)
    title = 'Change password for %s' % current_app.config['SITE_NAME']
    url = full_url('account.handle_change_password', token=token)
    text = '%s\n\n%s' % (title, url)
    mailer.send_text(email, title, text)
