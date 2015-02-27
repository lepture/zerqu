# coding: utf-8

import datetime
from functools import wraps
from flask import Blueprint
from flask import jsonify
from sqlalchemy.exc import IntegrityError
from .base import require_oauth
from .base import cursor_query, pagination
from .errors import first_or_404, NotFound, APIException, Denied
from ..models import db, current_user
from ..models import User, Cafe, CafeMember, Topic, Comment, TopicLike

bp = Blueprint('api_cafes', __name__)


def check_cafe_permission(cafe):
    if cafe.user_id == current_user.id:
        return True
    ident = (cafe.id, current_user.id)
    data = CafeMember.cache.get(ident)
    if data and data.role in (CafeMember.ROLE_MEMBER, CafeMember.ROLE_ADMIN):
        return data
    raise Denied('cafe "%s"' % cafe.slug)


def protect_cafe(f):
    @wraps(f)
    def decorated(slug):
        cafe = first_or_404(Cafe, slug=slug)
        if cafe.permission == Cafe.PERMISSION_PRIVATE:
            @wraps(f)
            def wrapped():
                check_cafe_permission(cafe)
                return f(cafe)
            return require_oauth(login=True, cache_time=300)(wrapped)()
        return require_oauth(login=False, cache_time=600)(f)(cafe)
    return decorated


@bp.route('')
@require_oauth(login=False, cache_time=300)
def list_cafes():
    data, cursor = cursor_query(Cafe, 'desc')
    reference = {'user_id': User.cache.get_dict({o.user_id for o in data})}
    return jsonify(data=data, reference=reference, cursor=cursor)


@bp.route('/<slug>')
@require_oauth(login=False, cache_time=300)
def view_cafe(slug):
    cafe = first_or_404(Cafe, slug=slug)
    data = dict(cafe)
    data['user'] = cafe.user
    return jsonify(data)


@bp.route('/<slug>/users', methods=['POST'])
@require_oauth(login=True, scopes=['user:subscribe'])
def join_cafe(slug):
    cafe = first_or_404(Cafe, slug=slug)
    ident = (cafe.id, current_user.id)

    item = CafeMember.query.get(ident)
    if item and item.role != CafeMember.ROLE_VISITOR:
        return '', 204

    if item:
        item.created_at = datetime.datetime.utcnow()
    else:
        item = CafeMember(cafe_id=cafe.id, user_id=current_user.id)

    if cafe.user_id == current_user.id:
        item.role = CafeMember.ROLE_ADMIN
    elif cafe.permission == cafe.PERMISSION_PRIVATE:
        item.role = CafeMember.ROLE_APPLICANT
    else:
        item.role = CafeMember.ROLE_SUBSCRIBER

    try:
        db.session.add(item)
        db.session.commit()
    except IntegrityError:
        raise APIException(error_code='duplicate_request')
    return '', 204


@bp.route('/<slug>/users', methods=['DELETE'])
@require_oauth(login=True, scopes=['user:subscribe'])
def leave_cafe(slug):
    cafe = first_or_404(Cafe, slug=slug)
    ident = (cafe.id, current_user.id)
    item = CafeMember.query.get(ident)

    if not item:
        raise NotFound('CafeMember')

    item.role = CafeMember.ROLE_VISITOR
    db.session.add(item)
    db.session.commit()
    return '', 204


@bp.route('/<slug>/users')
@protect_cafe
def list_cafe_users(cafe):
    total = CafeMember.cache.filter_count(cafe_id=cafe.id)
    pagi = pagination(total)
    perpage = pagi['perpage']
    offset = (pagi['page'] - 1) * perpage

    q = CafeMember.query.filter_by(cafe_id=cafe.id)
    items = q.order_by(CafeMember.user_id).offset(offset).limit(perpage).all()
    user_ids = [o.user_id for o in items]
    users = User.cache.get_dict(user_ids)
    data = list(_itermembers(items, users))
    return jsonify(data=data, pagination=pagi)


def _itermembers(items, users):
    for o in items:
        key = str(o.user_id)
        if key in users:
            rv = dict(o)
            rv['user'] = users[key]
            yield rv


@bp.route('/<slug>/topics')
@protect_cafe
def list_cafe_topics(cafe):
    data, cursor = cursor_query(Topic, 'desc', cafe_id=cafe.id)
    reference = {'user_id': User.cache.get_dict({o.user_id for o in data})}

    tids = {o.id for o in data}
    likes = TopicLike.topic_like_counts(tids)
    comments = Comment.topic_comment_counts(tids)

    rv = []

    for o in data:
        item = dict(o)
        item['like_count'] = likes.get(o.id, 0)
        item['comment_count'] = comments.get(o.id, 0)
        rv.append(item)

    return jsonify(data=rv, reference=reference, cursor=cursor)
