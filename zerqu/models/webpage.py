# coding: utf-8

import hashlib
import requests
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy import String, Unicode, Integer, DateTime
from werkzeug.urls import url_parse, url_join
from zerqu.libs.utils import run_task
from Zerqu.libs.webparser import parse_meta, sanitize_link
from .base import db, Base, JSON


UA = 'Mozilla/5.0 (compatible; Zerqu)'


class WebPage(Base):
    __tablename__ = 'zq_webpage'

    uuid = Column(String(34), primary_key=True)
    link = Column(String(400), nullable=False)
    title = Column(Unicode(80))
    image = Column(String(256))
    description = Column(Unicode(140))
    info = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    domain = Column(String(200))
    # first created by this user
    user_id = Column(Integer)

    def __init__(self, uuid, link, user_id=None):
        self.uuid = uuid
        self.link = link
        url = url_parse(link)
        self.domain = url.host
        if user_id:
            self.user_id = user_id

    def keys(self):
        return [
            'uuid', 'title', 'image', 'description', 'info', 'link',
            'domain', 'created_at', 'updated_at',
        ]

    def fetch_update(self):
        headers = {'User-Agent': UA}
        resp = requests.get(self.link, timeout=5, headers=headers)
        if resp.status_code != 200:
            self.info = {'error': 'status_code_error'}
        elif not resp.text:
            self.info = {'error': 'content_not_found'}
        else:
            info = parse_meta(resp.text)
            self.title = info.pop('title', '')[:80]
            self.description = info.pop('description', '')[:140]
            image = info.pop('image', None)
            if image and len(image) < 256:
                self.image = url_join(self.link, image)
            self.info = info

        with db.auto_commit():
            db.session.add(self)

    @classmethod
    def get_or_create(cls, link, user_id=None):
        link = sanitize_link(link)
        if not link.startswith('http'):
            return None

        uuid = hashlib.md5(link.encode('utf-8')).hexdigest()
        page = cls.query.get(uuid)
        if not page:
            page = cls(uuid=uuid, link=link, user_id=user_id)
            with db.auto_commit():
                db.session.add(page)
        if not page.info:
            run_task(page.fetch_update)
        return page
