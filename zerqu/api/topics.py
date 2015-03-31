# coding: utf-8

from flask import Blueprint
from flask import request, jsonify
from .base import require_oauth, get_or_404, pagination
from ..errors import APIException, Conflict
from ..models import db, current_user, User
from ..models import Cafe, Topic, TopicLike, Comment, TopicRead

bp = Blueprint('api_topics', __name__)


@bp.route('/statuses')
@require_oauth(login=False, cache_time=600)
def view_statuses():
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
@require_oauth(login=True, scopes=['topic:write'])
def update_topic(tid):
    topic = Topic.cache.get(tid)
    return jsonify(topic)


@bp.route('/<int:tid>/read', methods=['POST'])
@require_oauth(login=True)
def write_read_percent(tid):
    topic = get_or_404(Topic, tid)
    read = TopicRead.query.get((topic.id, current_user.id))
    percent = request.get_json().get('percent')
    if not isinstance(percent, int):
        raise APIException(description='Invalid payload "percent"')
    if not read:
        read = TopicRead(topic_id=topic.id, user_id=current_user.id)
    read.percent = percent
    db.session.add(read)
    db.session.commit()
    return jsonify(percent=read.percent)


@bp.route('/<int:tid>/comments')
@require_oauth(login=False)
def view_topic_comments(tid):
    return ''


@bp.route('/<int:tid>/comments', methods=['POST'])
@require_oauth(login=True, scopes=['comment:write'])
def create_topic_comments(tid):
    return ''


@bp.route('/<int:tid>/likes')
@require_oauth(login=False, cache_time=600)
def view_topic_likes(tid):
    topic = get_or_404(Topic, tid)

    total = TopicLike.cache.filter_count(topic_id=topic.id)
    pagi = pagination(total)
    perpage = pagi['perpage']
    offset = (pagi['page'] - 1) * perpage

    q = TopicLike.query.filter_by(topic_id=topic.id)
    items = q.order_by(TopicLike.created_at).offset(offset).limit(perpage)
    user_ids = [o.user_id for o in items]

    current_info = current_user and pagi['page'] == 1
    if current_info and current_user.id in user_ids:
        user_ids.remove(current_user.id)

    data = User.cache.get_many(user_ids)
    if current_info and TopicLike.cache.get((topic.id, current_user.id)):
        data.insert(0, current_user)
    return jsonify(data=data, pagination=pagi)


@bp.route('/<int:tid>/likes', methods=['POST'])
@require_oauth(login=True)
def like_topic(tid):
    data = TopicLike.query.get((tid, current_user.id))
    if data:
        raise Conflict(description='You already liked it')

    topic = get_or_404(Topic, tid)
    db.session.add(TopicLike(topic_id=topic.id, user_id=current_user.id))
    db.session.commit()
    return '', 204


@bp.route('/<int:tid>/likes', methods=['DELETE'])
@require_oauth(login=True)
def unlike_topic(tid):
    data = TopicLike.query.get((tid, current_user.id))
    if not data:
        raise Conflict(description='You already unliked it')
    db.session.delete(data)
    db.session.commit()
    return '', 204
