# coding: utf-8

from flask import Blueprint
from flask import jsonify
from .base import require_oauth
from .errors import APIException, NotFound
from ..models import db, current_user
from ..models import Topic, TopicLike

bp = Blueprint('api_topics', __name__)


@bp.route('/<int:tid>')
@require_oauth(login=False, cache_time=600)
def view_topic(tid):
    topic = Topic.cache.get(tid)
    return jsonify(topic)


@bp.route('/<int:tid>', methods=['POST'])
@require_oauth(login=True)
def update_topic(tid):
    topic = Topic.cache.get(tid)
    return jsonify(topic)


@bp.route('/<int:tid>/comments')
@require_oauth(login=False)
def view_topic_comments(tid):
    return ''


@bp.route('/<int:tid>/comments', methods=['POST'])
@require_oauth(login=True)
def create_topic_comments(tid):
    return ''


@bp.route('/<int:tid>/likes')
@require_oauth(login=False)
def view_topic_likes(tid):
    return ''


@bp.route('/<int:tid>/likes', methods=['POST'])
@require_oauth(login=True)
def like_topic(tid):
    data = TopicLike.query.get((tid, current_user.id))
    if data:
        raise APIException(description='You already liked it')

    topic = Topic.cache.get(tid)
    if not topic:
        raise NotFound('Topic')

    db.session.add(TopicLike(topic_id=topic.id, user_id=current_user.id))
    db.session.commit()
    return '', 204


@bp.route('/<int:tid>/likes', methods=['DELETE'])
@require_oauth(login=True)
def unlike_topic(tid):
    data = TopicLike.query.get((tid, current_user.id))
    if not data:
        raise APIException(description='You already unliked it')
    db.session.delete(data)
    db.session.commit()
    return '', 204
