
import re
import hashlib
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy import String, Integer, DateTime
from .base import db, Base, JSON


class WebPage(Base):
    __tablename__ = 'zq_webpage'

    uuid = Column(String(34), primary_key=True)
    link = Column(String(400), nullable=False)
    title = Column(String(80))
    image = Column(String(256))
    description = Column(String(140))
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
