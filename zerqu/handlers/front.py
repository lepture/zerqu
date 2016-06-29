# coding: utf-8

import os
from flask import Blueprint, request, session, current_app, json
from flask import render_template, abort, redirect
from werkzeug.security import gen_salt
from zerqu.libs.cache import cache, ONE_HOUR
from zerqu.libs.utils import is_robot, xmldatetime
from zerqu.rec.timeline import get_all_topics
from zerqu.models import db, User, Cafe, Topic, CafeTopic, Comment


bp = Blueprint('front', __name__, template_folder='templates')
bp.add_app_template_filter(xmldatetime)


@bp.before_request
def manifest_hook():
    manifest_file = current_app.config.get('SITE_MANIFEST')
    if not manifest_file or not os.path.isfile(manifest_file):
        request.manifest = None
        return

    manifest_mtime = os.path.getmtime(manifest_file)
    latest = getattr(current_app, 'manifest_mtime', 0)
    if latest != manifest_mtime:
        current_app.manifest_mtime = manifest_mtime
        with open(manifest_file) as f:
            manifest = json.load(f)
            current_app.manifest = manifest

    request.manifest = getattr(current_app, 'manifest', None)


@bp.route('/')
def home():
    topics, _ = get_all_topics(0)
    topic_users = User.cache.get_dict({o.user_id for o in topics})
    topic_cafes = CafeTopic.get_topics_cafes([o.id for o in topics])
    return render_template(
        'front/index.html',
        topics=topics,
        topic_users=topic_users,
        topic_cafes=topic_cafes,
    )


@bp.route('/t/<int:tid>')
def view_topic(tid):
    """Show one topic. This handler is designed for SEO."""
    topic = Topic.cache.get_or_404(tid)
    user = User.cache.get(topic.user_id)

    q = db.session.query(CafeTopic.cafe_id).filter_by(topic_id=tid)
    cafes = Cafe.cache.get_many([i for i, in q])

    q = db.session.query(Comment.id).filter_by(topic_id=tid)
    comments = Comment.cache.get_many({i for i, in q.limit(100)})

    comment_users = User.cache.get_dict({o.user_id for o in comments})
    comment_count = Comment.cache.filter_count(topic_id=tid)

    return render_template(
        'front/topic.html',
        topic=topic,
        user=user,
        cafes=cafes,
        comments=comments,
        comment_users=comment_users,
        comment_count=comment_count,
    )


@bp.route('/c/')
def cafe_list():
    q = db.session.query(Cafe.id)
    q = q.order_by(Cafe.id.desc())
    cafes = Cafe.cache.get_many([i for i, in q.limit(100)])
    return render_template(
        'front/cafe_list.html',
        cafes=cafes,
    )


@bp.route('/c/<slug>')
def view_cafe(slug):
    """Show one cafe. This handler is designed for SEO."""
    cafe = Cafe.cache.first_or_404(slug=slug)
    q = db.session.query(CafeTopic.topic_id)
    q = q.filter_by(cafe_id=cafe.id, status=CafeTopic.STATUS_PUBLIC)
    q = q.order_by(CafeTopic.topic_id.desc()).limit(50)
    topics = Topic.cache.get_many([i for i, in q])
    topic_users = User.cache.get_dict({o.user_id for o in topics})
    return render_template(
        'front/cafe.html',
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
    return render_template(
        'front/user.html',
        user=user,
        topics=topics,
    )


@bp.route('/u/<path:name>')
@bp.route('/c/<path:name>')
@bp.route('/t/<path:name>')
@bp.route('/z/<path:name>')
def view_zerqu_app(name):
    """A helper URL router for anything else."""
    if is_robot():
        abort(403)
    return render_template('front/app.html')
