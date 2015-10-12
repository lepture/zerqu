# coding: utf-8

from flask import jsonify
from zerqu.models import db, User, current_user
from zerqu.models import Cafe, CafeMember, Topic
from zerqu.models import Notification
from zerqu.models import iter_items_with_users
from zerqu.models.topic import topic_list_with_statuses
from zerqu.forms import RegisterForm, UserProfileForm
from .base import ApiBlueprint
from .base import require_oauth, require_confidential
from .utils import int_or_raise, get_pagination_query

api = ApiBlueprint('users')


@api.route('', methods=['POST'])
@require_confidential
def create_user():
    form = RegisterForm.create_api_form()
    user = form.create_user()
    return jsonify(user), 201


@api.route('')
@require_oauth(login=False, cache_time=300)
def list_users():
    q = User.query.filter(User.role >= 0).order_by(User.reputation.desc())
    data = q.limit(100).all()
    return jsonify(data=data)


@api.route('/<username>')
@require_oauth(login=False, cache_time=600)
def view_user(username):
    user = User.cache.first_or_404(username=username)
    return jsonify(user)


@api.route('/<username>/cafes')
@require_oauth(login=False, cache_time=600)
def view_user_cafes(username):
    user = User.cache.first_or_404(username=username)
    cafe_ids = CafeMember.get_user_following_cafe_ids(user.id)
    cafes = Cafe.cache.get_many(cafe_ids)
    data = list(iter_items_with_users(cafes))
    return jsonify(data=data)


@api.route('/<username>/topics')
@require_oauth(login=False, cache_time=600)
def view_user_topics(username):
    cursor = int_or_raise('cursor', 0)
    count = int_or_raise('count', 20, 100)

    user = User.cache.first_or_404(username=username)
    q = db.session.query(Topic.id)
    q = q.filter(Topic.status != Topic.STATUS_DRAFT)
    q = q.filter_by(user_id=user.id)
    if cursor:
        q = q.filter(Topic.id < cursor)

    q = q.order_by(Topic.id.desc()).limit(count).all()
    topic_ids = [i for i, in q]
    if not topic_ids:
        return jsonify(data=[], cursor=0)

    topics = Topic.cache.get_many(topic_ids)
    data = list(iter_items_with_users(topics, {str(user.id): user}))
    data = topic_list_with_statuses(data, current_user.id)

    if len(topic_ids) < count:
        cursor = 0
    else:
        cursor = topics[-1].id
    return jsonify(data=data, cursor=cursor)


@api.route('/me')
@require_oauth(login=True)
def view_current_user():
    return jsonify(current_user)


@api.route('/me', methods=['POST', 'PATCH'])
@require_oauth(login=True, scopes=['user:write'])
def update_current_user():
    user = User.query.get(current_user.id)
    form = UserProfileForm.create_api_form(user)
    form.populate_obj(user)
    with db.auto_commit():
        db.session.add(user)
    return jsonify(dict(user))


@api.route('/me/email')
@require_oauth(login=True, scopes=['user:email'])
def view_current_user_email():
    return jsonify(email=current_user.email)


@api.route('/me/notification')
@require_oauth(login=True)
def view_notification():
    page, perpage = get_pagination_query()
    items, pagination = Notification(current_user.id).paginate(page, perpage)
    data = Notification.process_notifications(items)
    return jsonify(data=data, pagination=dict(pagination))


@api.route('/me/notification', methods=['DELETE'])
@require_oauth(login=True)
def clear_notification():
    Notification(current_user.id).flush()
    return '', 204


@api.route('/me/notification/count')
@require_oauth(login=True)
def view_notification_count():
    count = Notification(current_user.id).count()
    return jsonify(count=count)
