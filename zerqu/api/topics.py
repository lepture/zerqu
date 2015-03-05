# coding: utf-8

from flask import Blueprint
from flask import request, jsonify
from .base import require_oauth, get_or_404
from .errors import APIException, NotFound
from ..models import db, current_user
from ..models import Cafe, Topic, TopicLike, Comment, TopicRead

bp = Blueprint('api_topics', __name__)


@bp.route('/statuses')
@require_oauth(login=False)
def statuses():
    id_list = request.args.get('topics')
    if not id_list:
        raise APIException(description='Require parameter "topics" missing')
    try:
        tids = map(int, id_list.split(','))
    except ValueError:
        raise APIException(
            description='Require int type on "topics" parameter'
        )

    rv = {}
    likes = TopicLike.topics_like_counts(tids)
    comments = Comment.topics_comment_counts(tids)
    reading = TopicRead.topics_read_counts(tids)

    for tid in tids:
        tid = str(tid)
        rv[tid] = {
            'like_count': likes.get(tid, 0),
            'comment_count': comments.get(tid, 0),
            'read_count': reading.get(tid, 0),
        }

    if not current_user:
        return jsonify(rv)

    liked = TopicLike.topics_liked_by_user(current_user.id, tids)
    reads = TopicRead.topics_read_by_user(current_user.id, tids)
    for tid in tids:
        tid = str(tid)
        item = liked.get(tid)
        if item:
            rv[tid]['liked_by_me'] = item.created_at
        item = reads.get(tid)
        if item:
            rv[tid]['read_by_me'] = item.percent

    return jsonify(rv)


@bp.route('/<int:tid>')
@require_oauth(login=False, cache_time=600)
def view_topic(tid):
    topic = get_or_404(Topic, tid)

    data = dict(topic)

    cafe = Cafe.cache.get(topic.cafe_id)

    data['cafe'] = dict(cafe)
    data['feature_type'] = cafe.feature

    # TODO: render content
    data['content'] = topic.content
    data['user'] = dict(topic.user)
    data['like_count'] = TopicLike.cache.filter_count(topid_id=tid)
    data['comment_count'] = Comment.cache.filter_count(topid_id=tid)

    if current_user:
        if TopicLike.cache.get((tid, current_user.id)):
            data['liked_by_me'] = True
        else:
            data['liked_by_me'] = False

    return jsonify(data)


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
