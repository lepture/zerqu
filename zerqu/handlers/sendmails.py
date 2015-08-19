

from functools import wraps
from flask import current_app, abort
from werkzeug.security import gen_salt
from zerqu.libs.cache import redis, cache, ONE_DAY
from zerqu.libs.pigeon import send_text
from zerqu.libs.utils import full_url, run_task


def prevent_duplicated(key_pattern):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = key_pattern % args
            sent = cache.get(key)
            if sent:
                return True
            cache.set(key, 1, timeout=300)
            return f(*args, **kwargs)
        return decorated
    return wrapper


def create_email_signature(email, alt='signup'):
    # save email to redis
    token = gen_salt(16)
    key = 'account:%s:%s' % (alt, token)
    redis.set(key, email.lower(), ONE_DAY)
    return token


def get_email_from_signature(token, alt='signup'):
    key = 'account:%s:%s' % (alt, token)
    email = redis.get(key)
    if not email:
        return abort(404)
    return email, key


@prevent_duplicated('email:signup:%s')
def send_signup_email(email):
    token = create_email_signature(email, 'signup')
    url = full_url('account.signup', token=token)
    title = 'Sign up account for %s' % current_app.config['SITE_NAME']
    text = '%s\n\n%s' % (title, url)
    run_task(send_text, email, title, text)


@prevent_duplicated('email:password:%s')
def send_change_password_email(email):
    token = create_email_signature(email, 'password')
    title = 'Change password for %s' % current_app.config['SITE_NAME']
    url = full_url('account.change_password', token=token)
    text = '%s\n\n%s' % (title, url)
    run_task(send_text, email, title, text)
