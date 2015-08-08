# coding: utf-8

from flask import request

from zerqu.libs.errors import APIException
from zerqu.libs.utils import Pagination
from zerqu.models import db


def int_or_raise(key, value=0, maxvalue=None):
    try:
        num = int(request.args.get(key, value))
        if maxvalue is not None and num > maxvalue:
            return maxvalue
        return num
    except ValueError:
        raise APIException(
            description='Require int type on %s parameter' % key
        )


def cursor_query(model, filter_func=None):
    """Return a cursor query on the given model. The model must has id as
    the primary key.
    """
    cursor = int_or_raise('cursor', 0)
    count = int_or_raise('count', 20, 100)
    query = db.session.query(model.id)
    desc = request.args.get('order') != 'asc'

    if cursor and desc:
        query = query.filter(model.id < cursor)
    elif cursor and not desc:
        query = query.filter(model.id > cursor)
    if filter_func:
        query = filter_func(query)

    if desc:
        query = query.order_by(model.id.desc())
    else:
        query = query.order_by(model.id.asc())

    ids = [i for i, in query.limit(count)]
    data = model.cache.get_many(ids)

    if len(data) < count:
        return data, 0

    cursor = data[-1].id
    return data, cursor


def pagination_query(model, key, **filters):
    page = int_or_raise('page', 1)
    if page < 1:
        raise APIException(description='page should be larger than 1')

    perpage = int_or_raise('perpage', 20, 100)
    if perpage < 10:
        raise APIException(description='perpage should be larger than 10')

    total = model.cache.filter_count(**filters)
    rv = Pagination(total, page, perpage)

    if page == 1 and rv.pages == 0:
        return [], rv

    if page > rv.pages:
        raise APIException(
            description='page should be smaller than total pages'
        )

    if not isinstance(key, str):
        q = model.query.filter_by(**filters).order_by(key)
        return rv.fetch(q), rv

    order_key = request.args.get('key', key)
    desc = request.args.get('order') != 'asc'
    if not hasattr(model, order_key):
        order_key = key

    field = getattr(model, order_key)
    if desc:
        field = field.desc()

    if hasattr(model, 'id'):
        q = db.session.query(model.id).filter_by(**filters).order_by(field)
        ids = [i for i, in rv.fetch(q)]
        data = model.cache.get_many(ids)
    else:
        q = model.query.filter_by(**filters).order_by(field)
        data = rv.fetch(q)
    return data, rv
