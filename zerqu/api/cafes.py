# coding: utf-8

from flask import Blueprint
from flask import jsonify
from .base import require_oauth
from .base import cursor_query
from .errors import NotFound
from ..models import User, Cafe

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
    cafe = Cafe.cache.filter_first(slug=slug)
    if not cafe:
        raise NotFound('Cafe "%s"' % slug)
    data = dict(cafe)
    data['user'] = cafe.user
    return jsonify(status='ok', data=data)
