# coding: utf-8

import datetime
from flask import current_app
from sqlalchemy import Column
from sqlalchemy import String, DateTime, Integer, SmallInteger
from flask_oauthlib.client import OAuth
from flask_oauthlib.contrib.apps import (
    google,
    twitter,
    facebook,
    github,
    weibo,
)
from .base import db, Base, JSON
from .user import User

__all__ = ['SocialUser', 'init_app']


social = OAuth()


class SocialUser(Base):
    __tablename__ = 'zq_social_user'

    GOOGLE = 1
    TWITTER = 2
    FACEBOOK = 3
    GITHUB = 4
    WEIBO = 5

    STATUS_INACTIVE = 0
    STATUS_ACTIVE = 1
    STATUS_SHARE = 2

    SERVICES = {
        'google': GOOGLE,
        'twitter': TWITTER,
        'facebook': FACEBOOK,
        'github': GITHUB,
        'weibo': WEIBO,
    }

    service = Column(SmallInteger, primary_key=True)
    uuid = Column(String(64), primary_key=True)
    info = Column(JSON, default={})

    status = Column(SmallInteger, default=STATUS_ACTIVE)
    reputation = Column(Integer, default=0)

    user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    @staticmethod
    def get_remote_app(name):
        key = 'social.login.%s' % name
        return current_app.extensions.get(key)

    @classmethod
    def handle_authorized_response(cls, name):
        remote = cls.get_remote_app(name)
        resp = remote.authorized_response()
        if resp is None:
            return None

        profile = fetch_profile(remote, resp)
        if not profile:
            return None

        uuid = profile.pop('uuid')
        reputation = profile.pop('reputation')

        service_id = cls.SERVICES.get(name)

        data = cls.query.get((service_id, uuid))
        if data:
            data.info = profile
            data.reputation = reputation
            with db.auto_commit():
                db.session.add(data)
            return data

        data = cls(
            service=service_id,
            uuid=uuid,
            reputation=reputation,
            info=profile,
        )

        if name == 'google' and profile.get('verified_email'):
            email = profile.get('email')
            user = User.query.filter_by(email=email).first()
            if user:
                data.user_id = user.id

        with db.auto_commit():
            db.session.add(data)

        return data


def init_app(app):
    logins = app.config.get('SITE_SOCIAL_LOGINS')
    if not logins:
        return

    social.init_app(app)

    for name in logins:
        remote = register_service(name)
        if not remote:
            raise RuntimeError('No %r service' % name)
        key = 'social.login.%s' % name
        app.extensions[key] = remote


def register_service(name):
    if name == 'google':
        return google.register_to(social)

    if name == 'twitter':
        return twitter.register_to(social)

    if name == 'facebook':
        return facebook.register_to(social)

    if name == 'github':
        return github.register_to(social)

    if name == 'weibo':
        return weibo.register_to(social)


def fetch_profile(remote, data):
    if not isinstance(data, dict):
        return None

    if remote.name == 'google':
        return _fetch_google(remote, data)

    if remote.name == 'twitter':
        return _fetch_twitter(remote, data)

    if remote.name == 'github':
        return _fetch_github(remote, data)


def _fetch_google(remote, data):
    token = (data['access_token'],)
    resp = remote.get('userinfo', token=token)
    data.update(resp.data)
    data['service'] = 'google'
    data['uuid'] = data['id']
    data['avatar_url'] = data['picture']
    # Google user has a good reputation
    data['reputation'] = 500
    return data


def _fetch_twitter(remote, data):
    token = (data['oauth_token'], data['oauth_token_secret'])
    url = (
        'account/verify_credentials.json'
        '?include_email=true&include_entities=false'
    )
    resp = remote.get(url, token=token)
    data.update(resp.data)
    avatar_url = data['profile_image_url_https'].replace('_normal.', '.')
    data['avatar_url'] = avatar_url
    data['uuid'] = data['id_str']
    data['service'] = 'twitter'

    status = data.pop('status', None)
    if not status:
        data['reputation'] = 10
        return data

    created_at = status.get('created_at')
    if not created_at:
        data['reputation'] = 20
        return data

    d = datetime.datetime.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
    delta = datetime.datetime.utcnow() - d
    c = data['followers_count'] ** 0.4 + data['listed_count'] ** 0.6
    data['reputation'] = int(c * (10 - delta.days) + 100)
    return data


def _fetch_github(remote, data):
    token = (data['access_token'],)
    resp = remote.get('user', token=token)
    data.update(resp.data)
    data['service'] = 'github'
    data['uuid'] = str(data['id'])
    data['reputation'] = data['followers'] ** 0.4 * 20 + 100
    return data
