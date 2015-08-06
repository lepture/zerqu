# coding: utf-8

from flask import jsonify
from collections import defaultdict
from .base import ApiBlueprint
from .base import require_oauth, require_confidential
from .utils import int_or_raise
from ..models import db, User, current_user
from ..models import Cafe, CafeMember, Topic
from ..models.topic import topic_list_with_statuses
from ..forms import RegisterForm, UserProfileForm

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
    if current_user.id == user.id:
        cafe_ids = CafeMember.get_user_following_cafe_ids(user.id)
    else:
        cafe_ids = CafeMember.get_user_following_public_cafe_ids(user.id)

    cafes = Cafe.cache.get_many(cafe_ids)
    users = User.cache.get_dict({o.user_id for o in cafes})
    data = list(Cafe.iter_dict(cafes, user=users))
    return jsonify(data=data)


@api.route('/<username>/topics')
@require_oauth(login=False, cache_time=600)
def view_user_topics(username):
    cursor = int_or_raise('cursor', 0)
    count = int_or_raise('count', 20, 100)

    user = User.cache.first_or_404(username=username)
    q = db.session.query(Topic.id, Topic.cafe_id).filter_by(user_id=user.id)
    if cursor:
        q = q.filter(Topic.id < cursor)

    pairs = q.order_by(Topic.id.desc()).limit(count).all()
    cafe_topics = defaultdict(list)
    for tid, cid in pairs:
        cafe_topics[cid].append(tid)

    cafes = Cafe.cache.get_dict(cafe_topics.keys())
    if current_user.id != user.id:
        # filter private cafes
        for k in cafes:
            cafe = cafes[k]
            if cafe.permission == Cafe.PERMISSION_PRIVATE:
                cafe_topics.pop(cafe.id)
                cafes.pop(k)

    topic_ids = []
    for cid in cafe_topics:
        topic_ids.extend(cafe_topics[cid])

    topics = Topic.cache.get_many(topic_ids)
    users = {str(user.id): user}
    data = list(Topic.iter_dict(topics, cafe=cafes, user=users))
    data = topic_list_with_statuses(data, current_user.id)

    if len(pairs) < count:
        cursor = 0
    else:
        cursor = pairs[-1][0]
    return jsonify(data=data, cursor=cursor)


@api.route('/me')
@require_oauth(login=True)
def view_current_user():
    return jsonify(current_user)


@api.route('/me', methods=['PATCH'])
@require_oauth(login=True, scopes=['user:write'])
def update_current_user():
    user = User.query.get(current_user.id)
    form = UserProfileForm.create_api_form(user)
    form.populate_obj(user)
    with db.auto_commit():
        db.session.add(user)
    return jsonify(user)


@api.route('/me/email')
@require_oauth(login=True, scopes=['user:email'])
def view_current_user_email():
    return jsonify(email=current_user.email)
