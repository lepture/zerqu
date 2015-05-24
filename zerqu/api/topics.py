# coding: utf-8

from flask import request, jsonify
from markupsafe import escape
from .base import ApiBlueprint
from .base import require_oauth
from .utils import cursor_query, pagination
from ..errors import APIException, Conflict
from ..models import db, current_user, User
from ..models import Cafe, Topic, TopicLike, Comment, TopicRead
from ..forms import CommentForm
from ..libs import renderer

api = ApiBlueprint('topics')


@api.route('/statuses')
@require_oauth(login=False, cache_time=600)
def view_statuses():
    id_list = request.args.get('topics')
    if not id_list:
        raise APIException(description='Require parameter "topics" missing')
    try:
        tids = [int(i) for i in id_list.split(',')]
    except ValueError:
        raise APIException(
            description='Require int type on "topics" parameter'
        )
    user_id = None
    if current_user:
        user_id = current_user.id
    return jsonify(Topic.get_multi_statuses(tids, user_id))


@api.route('/<int:tid>')
@require_oauth(login=False, cache_time=600)
def view_topic(tid):
    topic = Topic.cache.get_or_404(tid)
    data = dict(topic)

    # /api/topic/:id?content=raw vs ?content=html
    content_format = request.args.get('content')
    if content_format == 'raw':
        data['content'] = escape(topic.content)
    else:
        data['content'] = renderer.markup(topic.content)

    data['user'] = dict(topic.user)
    data['cafe'] = dict(Cafe.cache.get(topic.cafe_id))
    user_id = None
    if current_user:
        user_id = current_user.id
    data.update(topic.get_statuses(user_id))
    return jsonify(data)


@api.route('/<int:tid>', methods=['POST'])
@require_oauth(login=True, scopes=['topic:write'])
def update_topic(tid):
    topic = Topic.cache.get(tid)
    return jsonify(topic)


@api.route('/<int:tid>/read', methods=['POST'])
@require_oauth(login=True)
def write_read_percent(tid):
    topic = Topic.cache.get_or_404(tid)
    read = TopicRead.query.get((topic.id, current_user.id))
    percent = request.get_json().get('percent')
    if not isinstance(percent, int):
        raise APIException(description='Invalid payload "percent"')
    if not read:
        read = TopicRead(topic_id=topic.id, user_id=current_user.id)
    read.percent = percent

    with db.auto_commit():
        db.session.add(read)
    return jsonify(percent=read.percent)


@api.route('/<int:tid>/comments')
@require_oauth(login=False, cache_time=600)
def view_topic_comments(tid):
    topic = Topic.cache.get_or_404(tid)
    data, cursor = cursor_query(
        Comment, lambda q: q.filter_by(topic_id=topic.id)
    )
    reference = {'user': User.cache.get_dict({o.user_id for o in data})}
    data = list(Comment.iter_dict(data, **reference))
    return jsonify(data=data, cursor=cursor)


@api.route('/<int:tid>/comments', methods=['POST'])
@require_oauth(login=True, scopes=['comment:write'])
def create_topic_comment(tid):
    topic = Topic.cache.get_or_404(tid)
    form = CommentForm.create_api_form()
    comment = form.create_comment(current_user.id, topic.id)
    rv = dict(comment)
    rv['user'] = dict(current_user)
    return jsonify(rv)


@api.route('/<int:tid>/likes')
@require_oauth(login=False, cache_time=600)
def view_topic_likes(tid):
    topic = Topic.cache.get_or_404(tid)

    total = TopicLike.cache.filter_count(topic_id=topic.id)
    pagi = pagination(total)
    perpage = pagi['perpage']
    offset = (pagi['page'] - 1) * perpage

    q = TopicLike.query.filter_by(topic_id=topic.id)
    items = q.order_by(TopicLike.created_at).offset(offset).limit(perpage)
    user_ids = [o.user_id for o in items]

    # make current user at the very first position of the list
    current_info = current_user and pagi['page'] == 1
    if current_info and current_user.id in user_ids:
        user_ids.remove(current_user.id)

    data = User.cache.get_many(user_ids)
    if current_info and TopicLike.cache.get((topic.id, current_user.id)):
        data.insert(0, current_user)
    return jsonify(data=data, pagination=pagi)


@api.route('/<int:tid>/likes', methods=['POST'])
@require_oauth(login=True)
def like_topic(tid):
    data = TopicLike.query.get((tid, current_user.id))
    if data:
        raise Conflict(description='You already liked it')

    topic = Topic.cache.get_or_404(tid)
    like = TopicLike(topic_id=topic.id, user_id=current_user.id)
    with db.auto_commit():
        db.session.add(like)
    return '', 204


@api.route('/<int:tid>/likes', methods=['DELETE'])
@require_oauth(login=True)
def unlike_topic(tid):
    data = TopicLike.query.get((tid, current_user.id))
    if not data:
        raise Conflict(description='You already unliked it')
    with db.auto_commit():
        db.session.delete(data)
    return '', 204
