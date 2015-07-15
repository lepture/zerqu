# coding: utf-8

from flask import Blueprint
from flask import render_template, abort
from ..libs.utils import is_robot, xmldatetime, full_url
from ..rec.timeline import get_all_topics
from ..models import db, User, Cafe, Topic, Comment


bp = Blueprint('front', __name__, template_folder='templates')
bp.add_app_template_filter(xmldatetime)


# @bp.before_request
def handle_app():
    if not is_robot():
        return render_template('front/app.html')


@bp.route('/')
def home():
    topics, _ = get_all_topics(0)
    topic_users = User.cache.get_dict({o.user_id for o in topics})
    topic_cafes = Cafe.cache.get_dict({o.cafe_id for o in topics})

    canonical_url = full_url('.home')
    return render_template(
        'front/index.html',
        canonical_url=canonical_url,
        topics=topics,
        topic_users=topic_users,
        topic_cafes=topic_cafes,
    )


@bp.route('/t/<int:tid>')
def view_topic(tid):
    """Show one topic. This handler is designed for SEO."""
    topic = Topic.cache.get_or_404(tid)
    cafe = Cafe.cache.get_or_404(topic.cafe_id)
    if cafe.permission == Cafe.PERMISSION_PRIVATE:
        abort(404)

    q = db.session.query(Comment.id).filter_by(topic_id=tid)
    comments = Comment.cache.get_many({i for i, in q.limit(100)})
    comment_users = User.cache.get_dict({o.user_id for o in comments})
    comment_count = Comment.cache.filter_count(topic_id=tid)

    canonical_url = full_url('.view_topic', tid=tid)
    return render_template(
        'front/topic.html',
        canonical_url=canonical_url,
        topic=topic,
        cafe=cafe,
        comments=comments,
        comment_users=comment_users,
        comment_count=comment_count,
    )


@bp.route('/c/')
def cafe_list():
    q = db.session.query(Cafe.id)
    q = q.filter(Cafe.permission != Cafe.PERMISSION_PRIVATE)
    q = q.order_by(Cafe.id.desc())
    cafes = Cafe.cache.get_many([i for i, in q.limit(100)])

    canonical_url = full_url('.cafe_list')
    return render_template(
        'front/cafe_list.html',
        canonical_url=canonical_url,
        cafes=cafes,
    )


@bp.route('/c/<slug>')
def view_cafe(slug):
    """Show one cafe. This handler is designed for SEO."""
    cafe = Cafe.cache.first_or_404(slug=slug)
    if cafe.permission == Cafe.PERMISSION_PRIVATE:
        abort(404)

    q = db.session.query(Topic.id).filter_by(cafe_id=cafe.id)
    q = q.order_by(Topic.id.desc())
    topics = Topic.cache.get_many([i for i, in q.limit(50)])
    topic_users = User.cache.get_dict({o.user_id for o in topics})

    canonical_url = full_url('.view_cafe', slug=slug)
    return render_template(
        'front/cafe.html',
        canonical_url=canonical_url,
        cafe=cafe,
        topics=topics,
        topic_users=topic_users,
    )


@bp.route('/u/<username>')
def view_user(username):
    user = User.cache.first_or_404(username=username)
    q = db.session.query(Topic.id).filter_by(user_id=user.id)
    q = q.order_by(Topic.id.desc())
    topics = Topic.cache.get_many([i for i, in q.limit(50)])

    canonical_url = full_url('.view_user', username=username)
    return render_template(
        'front/user.html',
        canonical_url=canonical_url,
        user=user,
        topics=topics,
    )
