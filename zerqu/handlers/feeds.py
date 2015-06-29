# coding: utf-8

from flask import Blueprint, request
from flask import render_template, abort, Response
from ..models import db, User, Cafe, Topic


bp = Blueprint('feeds', __name__)


def render_xml_template(template, **kwargs):
    xml = render_template(template, **kwargs)
    return Response(xml, content_type='application/atom+xml; charset=utf-8')


@bp.route('/sitemap.xml')
def sitemap():
    return render_xml_template('sitemap.xml')


@bp.route('/feed')
def site_feed():
    return render_xml_template('feed.xml')


@bp.route('/c/<slug>/feed')
def cafe_feed(slug):
    """Show one cafe. This handler is designed for SEO."""
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
    topic_users = User.cache.get_dict({o.user_id for o in topics})
    return render_xml_template(
        'feed.xml',
        cafe=cafe,
        topics=topics,
        topic_users=topic_users,
    )
