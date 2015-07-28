# coding: utf-8

from flask import jsonify
from .base import ApiBlueprint
from .base import require_oauth, require_confidential
from ..models import db, User, current_user
from ..models import Cafe, CafeMember, Topic
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
