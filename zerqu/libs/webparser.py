# coding: utf-8
"""
    Web page parser
    ~~~~~~~~~~~~~~~

    Parsing open graph meta data, including twitter cards.
"""

import re
import requests
from werkzeug.urls import url_parse, url_join
from werkzeug.utils import unescape

__version__ = '0.1'
__author__ = 'Hsiaoming Yang <me@lepture.com>'

# use simple regex, no need for lxml
META_TAG = re.compile(ur'<meta[^>]+content=[^>]+>', re.U | re.I)
META_ATTR = re.compile(
    ur'(name|property|content)=(?:\'|\")(.*?)(?:\'|\")',
    re.U | re.I | re.S
)
TITLE = re.compile(ur'<title>(.*?)</title>', re.U | re.I | re.S)

UA = 'Mozilla/5.0 (compatible; Webparser)'


def parse_meta(content, link=None):
    """Parse og information from HTML content.

    :param content: HTML content to be parsed. unicode required.
    """
    head = content.split(u'</head>', 1)[0]
    pairs = {}

    def parse_pair(kv):
        name = kv.get(u'name')
        if not name:
            name = kv.get(u'property')
        if not name:
            return
        if name in pairs:
            return
        content = kv.get(u'content')
        if not content:
            return
        pairs[name] = content

    for text in META_TAG.findall(head):
        kv = META_ATTR.findall(text)
        if kv:
            parse_pair(dict(kv))

    rv = {}

    def get_og_value(key):
        for name in [u'og:%s' % key, u'twitter:%s' % key]:
            if name in pairs:
                rv[key] = pairs[name]

    for key in [u'title', u'image', u'description', u'url']:
        get_og_value(key)

    if u'twitter:creator' in pairs:
        rv[u'twitter'] = pairs[u'twitter:creator']

    if u'title' not in rv:
        m = TITLE.findall(head)
        if m:
            rv[u'title'] = m[0]

    if u'description' not in rv:
        desc = rv.get(u'description')
        if desc:
            rv[u'description'] = desc

    # format absolute link
    if link and u'image' in rv:
        rv[u'image'] = url_join(link, rv[u'image'])

    rv.update(parse_embed(pairs))

    for key in [u'title', u'description']:
        if rv.get(key):
            rv[key] = unescape(rv[key])
    return rv


def parse_embed(pairs):
    rv = {}
    if u'twitter:player' in pairs:
        rv['embed_url'] = pairs[u'twitter:player']
    if u'twitter:player:width' in pairs:
        rv['embed_width'] = pairs[u'twitter:player:width']
    if u'twitter:player:height' in pairs:
        rv['embed_height'] = pairs[u'twitter:player:height']
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


def fetch_parse(link):
    headers = {'User-Agent': UA}
    resp = requests.get(link, timeout=5, headers=headers)
    if resp.encoding == 'ISO-8859-1':
        resp.encoding = 'UTF-8'
    if resp.status_code != 200:
        return {u'error': u'status_code_error'}
    elif not resp.text:
        return {u'error': u'content_not_found'}
    return parse_meta(resp.text, link)
