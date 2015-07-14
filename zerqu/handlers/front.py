# coding: utf-8

from flask import Blueprint, request
from flask import render_template, abort
from ..libs.utils import is_robot
from ..models import db, User, Cafe, Topic, Comment


bp = Blueprint('front', __name__, template_folder='templates')


# @bp.before_request
def handle_app():
    if not is_robot():
        return render_template('app.html')


@bp.route('/')
def home():
    return render_template('index.html')


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
    return render_template(
        'topic.html',
        topic=topic,
        cafe=cafe,
        comments=comments,
        comment_users=comment_users,
    )


@bp.route('/c/<slug>')
def view_cafe(slug):
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
    return render_template(
        'cafe.html',
        cafe=cafe,
        topics=topics,
        topic_users=topic_users,
    )


@bp.route('/u/<username>')
def view_user(username):
    user = User.cache.first_or_404(username=username)
    return render_template('user.html', user=user)
