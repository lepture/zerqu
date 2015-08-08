# coding: utf-8

from markupsafe import escape
from flask import Blueprint
from flask import abort, Response
from flask import request, current_app
from zerqu.models import db, User, Cafe, Topic
from zerqu.libs.cache import cache, ONE_HOUR
from zerqu.libs.utils import xmldatetime, full_url
from zerqu.rec.timeline import get_all_topics

bp = Blueprint('feeds', __name__)


@bp.before_request
def hook_for_render():
    key = 'feed:xml:%s' % request.path
    xml = cache.get(key)
    if xml:
        return Response(xml, content_type='text/xml; charset=UTF-8')


@bp.route('/sitemap.xml')
def sitemap():
    return ''


@bp.route('/feed')
def site_feed():
    topics, _ = get_all_topics()
    title = current_app.config.get('SITE_NAME')
    web_url = full_url('front.home')
    self_url = full_url('.site_feed')
    xml = u''.join(yield_feed(title, web_url, self_url, topics))
    key = 'feed:xml:%s' % request.path
    cache.set(key, xml, ONE_HOUR)
    return Response(xml, content_type='text/xml; charset=UTF-8')


@bp.route('/c/<slug>/feed')
def cafe_feed(slug):
    """Show one cafe. This handler is designed for SEO."""
    cafe = Cafe.cache.first_or_404(slug=slug)
    if cafe.permission == Cafe.PERMISSION_PRIVATE:
        abort(404)

    q = db.session.query(Topic.id).filter_by(cafe_id=cafe.id)
    q = q.order_by(Topic.id.desc())
    topics = Topic.cache.get_many([i for i, in q.limit(50)])

    site_name = current_app.config.get('SITE_NAME')
    title = u'%s - %s' % (site_name, cafe.name)

    web_url = full_url('front.view_cafe', slug=slug)
    self_url = full_url('.cafe_feed', slug=slug)

    xml = u''.join(yield_feed(title, web_url, self_url, topics))
    key = 'feed:xml:{}'.format(slug)
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
