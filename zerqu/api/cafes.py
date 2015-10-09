# coding: utf-8

import datetime

from flask import current_app
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError

from zerqu.libs.errors import NotFound, Denied, InvalidAccount, Conflict
from zerqu.models import db, current_user
from zerqu.models import User, Cafe, CafeMember, Topic
from zerqu.models.topic import topic_list_with_statuses
from zerqu.forms import CafeForm, TopicForm
from .base import ApiBlueprint
from .base import require_oauth, oauth_ratelimit, cache_response
from .utils import cursor_query, pagination_query

api = ApiBlueprint('cafes')


def get_and_protect_cafe(slug, scopes=None):
    cafe = Cafe.cache.first_or_404(slug=slug)
    if cafe.permission != Cafe.PERMISSION_PRIVATE:
        if scopes is None:
            oauth_ratelimit(False, scopes=None)
        else:
            oauth_ratelimit(True, scopes=scopes)
        return cafe

    if scopes is None:
        scopes = []
    scopes.append('cafe:private')
    oauth_ratelimit(True, scopes=scopes)

    if cafe.user_id == current_user.id:
        return cafe

    ident = (cafe.id, current_user.id)
    data = CafeMember.cache.get(ident)
    if data and data.role in (CafeMember.ROLE_MEMBER, CafeMember.ROLE_ADMIN):
        return cafe
    raise Denied('cafe "%s"' % cafe.slug)


@api.route('')
@require_oauth(login=False, cache_time=300)
def list_cafes():
    data, cursor = cursor_query(Cafe)
    users = User.cache.get_dict({o.user_id for o in data})
    data = list(Cafe.iter_dict(data, user=users))

    if not current_user or request.args.get('cursor'):
        return jsonify(data=data, cursor=cursor)

    cafe_ids = CafeMember.get_user_following_cafe_ids(current_user.id)
    following = Cafe.cache.get_many(cafe_ids)
    users = User.cache.get_dict({o.user_id for o in following})
    following = list(Cafe.iter_dict(following, user=users))
    return jsonify(following=following, data=data, cursor=cursor)


@api.route('', methods=['POST'])
@require_oauth(login=True, scopes=['cafe:write'])
def create_cafe():
    role = current_app.config.get('ZERQU_CAFE_CREATOR_ROLE')
    if current_user.role < role:
        raise Denied('creating cafe')
    form = CafeForm.create_api_form()
    cafe = form.create_cafe(current_user.id)
    return jsonify(cafe), 201


@api.route('/<slug>')
@require_oauth(login=False, cache_time=300)
def view_cafe(slug):
    cafe = Cafe.cache.first_or_404(slug=slug)
    data = dict(cafe)
    data['user'] = cafe.user

    if current_user:
        user_id = current_user.id
        m = CafeMember.cache.get((cafe.id, user_id))
        if m:
            data['membership'] = dict(m)

        permission = {
            'read': cafe.has_read_permission(user_id, m),
            'write': cafe.has_write_permission(user_id, m),
            'admin': cafe.has_admin_permission(user_id, m),
        }
    else:
        permission = {}

    data['permission'] = permission
    return jsonify(data)


@api.route('/<slug>', methods=['POST'])
@require_oauth(login=True, scopes=['cafe:write'])
def update_cafe(slug):
    cafe = Cafe.cache.first_or_404(slug=slug)

    if cafe.user_id != current_user.id:
        ident = (cafe.id, current_user.id)
        data = CafeMember.cache.get(ident)
        if not data or data.role != CafeMember.ROLE_ADMIN:
            raise Denied('cafe "%s"' % cafe.slug)

    form = CafeForm.create_api_form(obj=cafe)
    cafe = form.update_cafe(cafe, current_user.id)
    return jsonify(cafe)


@api.route('/<slug>/users', methods=['POST'])
@require_oauth(login=True, scopes=['user:subscribe'])
def join_cafe(slug):
    cafe = Cafe.cache.first_or_404(slug=slug)
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
        with db.auto_commit():
            db.session.add(item)
    except IntegrityError:
        raise Conflict(description='You already joined the cafe')
    return '', 204


@api.route('/<slug>/users', methods=['DELETE'])
@require_oauth(login=True, scopes=['user:subscribe'])
def leave_cafe(slug):
    cafe = Cafe.cache.first_or_404(slug=slug)
    ident = (cafe.id, current_user.id)
    item = CafeMember.query.get(ident)

    if not item:
        raise NotFound('CafeMember')

    item.role = CafeMember.ROLE_VISITOR
    with db.auto_commit():
        db.session.add(item)
    return '', 204


@api.route('/<slug>/users')
@cache_response(600)
def list_cafe_users(slug):
    cafe = get_and_protect_cafe(slug)
    members, pagination = pagination_query(
        CafeMember, CafeMember.user_id, cafe_id=cafe.id
    )
    user_ids = [o.user_id for o in members]
    users = User.cache.get_dict(user_ids)

    data = []
    for item in members:
        key = str(item.user_id)
        if key in users:
            rv = dict(item)
            rv['user'] = dict(users[key])
            data.append(rv)

    admin_ids = CafeMember.get_cafe_admin_ids(cafe.id)
    admin_ids.add(cafe.user_id)
    admins = User.cache.get_many(admin_ids)
    return jsonify(admins=admins, data=data, pagination=dict(pagination))


@api.route('/<slug>/topics')
@cache_response(600)
def list_cafe_topics(slug):
    cafe = get_and_protect_cafe(slug)
    data, p = pagination_query(Topic, 'id', cafe_id=cafe.id)
    reference = {'user': User.cache.get_dict({o.user_id for o in data})}
    data = list(Topic.iter_dict(data, **reference))
    data = topic_list_with_statuses(data, current_user.id)
    return jsonify(data=data, pagination=dict(p))


@api.route('/<slug>/topics', methods=['POST'])
def create_cafe_topic(slug):
    cafe = get_and_protect_cafe(slug, ['topic:write'])

    if not current_user.is_active:
        raise InvalidAccount(description='Your account is not active')

    if cafe.permission == Cafe.PERMISSION_PUBLIC:
        CafeMember.get_or_create(cafe.id, current_user.id)
    elif cafe.permission != Cafe.PERMISSION_PRIVATE:
        if not cafe.has_write_permission(current_user.id):
            raise Denied('creating topic in this cafe')

    form = TopicForm.create_api_form()
    topic = form.create_topic(cafe.id, current_user.id)
    data = dict(topic)
    data['user'] = dict(current_user)
    data['content'] = topic.html
    return jsonify(data), 201
