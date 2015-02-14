# coding: utf-8

import datetime
from flask import Blueprint
from flask import jsonify
from sqlalchemy.exc import IntegrityError
from .base import require_oauth
from .base import cursor_query
from .errors import first_or_404, NotFound, APIException
from ..models import db, current_user
from ..models import User, Cafe, CafeMember

bp = Blueprint('api_cafes', __name__)


@bp.route('/cafes')
@require_oauth(login=False, cache_time=300)
def list_cafes():
    data = cursor_query(Cafe, 'desc')
    meta = {}
    meta['user_id'] = User.cache.get_dict({o.user_id for o in data})
    return jsonify(status='ok', data=data, meta=meta)


@bp.route('/cafes/<slug>')
@require_oauth(login=False, cache_time=300)
def view_cafe(slug):
    cafe = first_or_404(Cafe, slug=slug)
    data = dict(cafe)
    data['user'] = cafe.user
    return jsonify(status='ok', data=data)


@bp.route('/cafes/<slug>/users', methods=['POST'])
@require_oauth(login=True, scopes=['user:follow'])
def join_cafe(slug):
    cafe = first_or_404(Cafe, slug=slug)
    ident = (cafe.id, current_user.id)

    item = CafeMember.query.get(ident)
    if item and item.role != CafeMember.ROLE_VISITOR:
        return jsonify(status='ok')

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
    return jsonify(status='ok')


@bp.route('/cafes/<slug>/users', methods=['DELETE'])
@require_oauth(login=True, scopes=['user:follow'])
def leave_cafe(slug):
    cafe = first_or_404(Cafe, slug=slug)
    ident = (cafe.id, current_user.id)
    item = CafeMember.query.get(ident)

    if not item:
        raise NotFound('CafeMember')

    item.role = CafeMember.ROLE_VISITOR
    db.session.add(item)
    db.session.commit()
    return jsonify(status='ok')
