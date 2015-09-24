# coding: utf-8
"""
    Web page parser
    ~~~~~~~~~~~~~~~

    Parsing open graph meta data, including twitter cards.
"""

import re
from werkzeug.urls import url_parse

__version__ = '0.1'
__author__ = 'Hsiaoming Yang <me@lepture.com>'

# use simple regex, no need for lxml
META_TAG = re.compile(ur'<meta[^>]+content=[^>]+>', re.U | re.I)
META_ATTR = re.compile(
    ur'(name|property|content)=(?:\'|\")(.*?)(?:\'|\")',
    re.U | re.I | re.S
)
TITLE = re.compile(ur'<title>(.*?)</title>', re.U | re.I | re.S)


def parse_meta(content):
    """Parse og information from HTML content.

    :param content: HTML content to be parsed. unicode required.
    """
    head = content.split(u'</head>', 1)[0]
    rv = {}

    def get_value(key, name, content):
        if name not in [u'og:%s' % key, u'twitter:%s' % key]:
            return False
        if key not in rv:
            rv[key] = content
        return True

    def parse_pair(kv):
        name = kv.get(u'name')
        if not name:
            name = kv.get(u'property')
        if not name:
            return None

        content = kv.get(u'content')
        if not content:
            return None

        if name == u'twitter:creator':
            rv[u'twitter'] = content
            return

        for key in [u'title', u'image', u'description', u'url']:
            if get_value(key, name, content):
                return

    for text in META_TAG.findall(head):
        kv = META_ATTR.findall(text)
        if kv:
            parse_pair(dict(kv))

    if u'title' not in rv:
        m = TITLE.findall(head)
        if m:
            rv[u'title'] = m[0]
    return rv


def sanitize_link(url):
    """Sanitize link. clean utm parameters on link."""
    if not re.match(r'^https?:\/\/', url):
        url = 'http://%s' % url

    rv = url_parse(url)

    if rv.query:
        query = re.sub(r'utm_\w+=[^&]+&?', '', rv.query)
        url = '%s://%s%s?%s' % (rv.scheme, rv.host, rv.path, query)

    # remove ? at the end of url
    url = re.sub(r'\?$', '', url)
    return url
