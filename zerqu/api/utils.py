# coding: utf-8

from flask import request
from ..models import db
from ..errors import APIException


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


def cursor_query(model, order_by='desc', filter_func=None):
    """Return a cursor query on the given model. The model must has id as
    the primary key.
    """
    before = int_or_raise('before')
    after = int_or_raise('after')
    count = int_or_raise('count', 20, 100)
    if before and after:
        desc = (
            'Parameters conflict, before and after should not appear '
            'at the same time.'
        )
        raise APIException(description=desc)

    query = db.session.query(model.id)
    if before:
        query = query.filter(model.id < before)
    elif after:
        query = query.filter(model.id > after)
    if filter_func:
        query = filter_func(query)

    if order_by == 'desc':
        query = query.order_by(model.id.desc())

    ids = [i for i, in query.limit(count)]
    data = model.cache.get_many(ids)

    cursor = {'key': 'id'}
    if len(data) < count:
        return data, cursor
    cursor['before'] = data[-1].id
    cursor['after'] = data[0].id
    return data, cursor


def pagination(total):
    page = int_or_raise('page', 1)
    if page < 1:
        raise APIException(description='page should be larger than 1')

    perpage = int_or_raise('perpage', 20, 100)
    if perpage < 10:
        raise APIException(description='perpage should be larger than 10')

    pages = int((total - 1) / perpage) + 1
    if page > pages:
        raise APIException(
            description='page should be smaller than total pages'
        )

    rv = {
        'total': total,
        'pages': pages,
        'page': page,
        'perpage': perpage,
        'prev': None,
        'next': None,
    }

    if page > 1:
        rv['prev'] = page - 1
    if page < pages:
        rv['next'] = page + 1
    return rv
