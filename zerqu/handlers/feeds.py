# coding: utf-8

from markupsafe import escape
from flask import Blueprint
from flask import abort, Response
from flask import request, current_app, url_for
from ..models import db, User, Cafe, Topic
from ..libs.cache import cache, ONE_HOUR
from ..libs.utils import xmldatetime

bp = Blueprint('feeds', __name__)


@bp.route('/sitemap.xml')
def sitemap():
    return ''


@bp.route('/c/<slug>/feed')
def cafe_feed(slug):
    """Show one cafe. This handler is designed for SEO."""
    key = 'feed:xml:{}'.format(slug)
    xml = cache.get(key)
    if xml:
        return Response(xml, content_type='text/xml; charset=UTF-8')

    cafe = Cafe.cache.first_or_404(slug=slug)
    if cafe.permission == Cafe.PERMISSION_PRIVATE:
        abort(404)

    cursor = request.args.get('cursor', 0)
    try:
        cursor = int(cursor)
    except ValueError:
        cursor = 0

    q = db.session.query(Topic.id).filter_by(cafe_id=cafe.id)
    if cursor:
        q = q.filter(Topic.id < cursor)

    q = q.order_by(Topic.id.desc())
    topics = Topic.cache.get_many([i for i, in q.limit(50)])

    site_name = current_app.config.get('SITE_NAME')
    title = u'%s - %s' % (site_name, cafe.name)

    web_url = full_url('front.view_cafe', slug=slug)
    self_url = full_url('.cafe_feed', slug=slug)

    xml = u''.join(yield_feed(title, web_url, self_url, topics))
    cache.set(key, xml, ONE_HOUR)
    return Response(xml, content_type='text/xml; charset=UTF-8')


def yield_feed(title, web_url, self_url, topics):
    yield u'<?xml version="1.0" encoding="utf-8"?>\n'
    yield u'<feed xmlns="http://www.w3.org/2005/Atom">'
    yield u'<title><![CDATA[%s]]></title>' % title
    yield u'<link href="%s" />' % escape(web_url)
    yield u'<link href="%s" rel="self" />' % escape(self_url)
    yield u'<id><![CDATA[%s]]></id>' % web_url
    if topics:
        yield u'<updated>%s</updated>' % xmldatetime(topics[0].updated_at)
    users = User.cache.get_dict({o.user_id for o in topics})
    for topic in topics:
        for text in yield_entry(topic, users.get(topic.user_id)):
            yield text
    yield u'</feed>'


def yield_entry(topic, user):
    url = full_url('front.view_topic', tid=topic.id)
    yield u'<entry>'
    yield u'<id><![CDATA[%s]]></id>' % url
    yield u'<link href="%s" />' % escape(url)
    yield u'<title type="html"><![CDATA[%s]]></title>' % topic.title
    yield u'<updated>%s</updated>' % xmldatetime(topic.updated_at)
    yield u'<published>%s</published>' % xmldatetime(topic.created_at)

    yield u'<author>'
    if user:
        yield u'<name>%s</name>' % escape(user.username)
        url = full_url('front.view_user', username=user.username)
        yield u'<uri>%s</uri>' % url
    else:
        yield u'<name>Anonymous</name>'
    yield u'</author>'

    content = topic.get_html_content()
    yield u'<content type="html"><![CDATA[%s]]></content>' % content
    yield u'</entry>'


def full_url(endpoint, **kwargs):
    baseurl = current_app.config.get('SITE_URL')
    if baseurl:
        baseurl = baseurl.rstrip('/')
        urlpath = url_for(endpoint, **kwargs)
        return '%s%s' % (baseurl, urlpath)
    kwargs['_external'] = True
    return url_for(endpoint, **kwargs)
