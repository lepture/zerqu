# coding: utf-8

import re
import hashlib
import requests
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy import String, Unicode, Integer, DateTime
from zerqu.libs.utils import run_task
from .base import db, Base, JSON

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


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

    def keys(self):
        return ['title', 'image', 'description', 'info']

    def fetch_update(self):
        headers = {'User-Agent': UA}
        resp = requests.get(self.link, timeout=5, headers=headers)
        if resp.status_code != 200:
            self.info = {'error': 'status_code_error'}
        elif not resp.text:
            self.info = {'error': 'content_not_found'}
        else:
            info = parse_meta(resp.text)
            self.title = info.pop('title', None)
            self.image = info.pop('image', None)
            self.description = info.pop('description', None)
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
            page = cls(uuid=uuid, link=link)
            if user_id:
                page.user_id = user_id
            with db.auto_commit():
                db.session.add(page)
            run_task(page.fetch_update)
        return page


def sanitize_link(url):
    """Sanitize link. clean utm parameters on link."""
    if not re.match(r'^https?:\/\/', url):
        url = 'http://%s' % url

    rv = urlparse(url)

    if rv.query:
        query = re.sub(r'utm_\w+=[^&]+&?', '', rv.query)
        url = '%s://%s%s?%s' % (rv.scheme, rv.hostname, rv.path, query)

    # remove ? at the end of url
    url = re.sub(r'\?$', '', url)
    return url


meta_pattern = re.compile(ur'<meta[^>]+content=[^>]+>', re.U)
value_pattern = re.compile(
    ur'(name|property|content)=(?:\'|\")(.*?)(?:\'|\")',
    re.U
)


def parse_meta(content):
    head = content.split('</head>', 1)[0]
    rv = {}

    def get_value(key, name, content):
        if name not in ['og:%s' % key, 'twitter:%s' % key]:
            return False
        if key not in rv:
            rv[key] = content
        return True

    def parse_pair(kv):
        name = kv.get('name')
        if not name:
            name = kv.get('property')
        if not name:
            return None

        content = kv.get('content')
        if not content:
            return None

        if name == 'twitter:creator':
            rv['twitter'] = content
            return

        for key in ['title', 'image', 'description', 'url']:
            if get_value(key, name, content):
                return

    for text in meta_pattern.findall(head):
        kv = value_pattern.findall(text)
        if kv:
            parse_pair(dict(kv))

    if 'title' not in rv:
        m = re.findall(ur'<title>(.*?)</title>', head, flags=re.U)
        if m:
            rv['title'] = m[0]
    return rv
