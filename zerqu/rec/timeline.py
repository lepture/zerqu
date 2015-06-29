# coding: utf-8

import random
from zerqu.models import db, Topic, Cafe, CafeMember
# TODO: use redis to calculate popularity


def get_timeline_topics(cursor=None, user_id=None, count=20):
    if user_id:
        cafe_ids = get_following_cafe_ids(user_id)
    else:
        cafe_ids = get_promoted_cafe_ids()

    if len(cafe_ids) < 10:
        # random sample some public cafes
        q = db.session.query(Cafe.id)
        q = q.filter_by(permission=Cafe.PERMISSION_PUBLIC)
        choices = {cafe_id for cafe_id, in q}
        if len(choices) > 8:
            cafe_ids = set(random.sample(choices, 6)) | cafe_ids
        else:
            cafe_ids = choices | cafe_ids
    return get_cafe_topics(cafe_ids, cursor, count)


def get_all_topics(cursor=None, count=20):
    cafe_ids = get_all_cafe_ids()
    return get_cafe_topics(cafe_ids, cursor, count)


def get_following_cafe_ids(user_id):
    q = db.session.query(Cafe.id).filter_by(status=Cafe.STATUS_OFFICIAL)
    official = {cafe_id for cafe_id, in q}
    following = CafeMember.get_user_following_cafe_ids(user_id)
    q = db.session.query(Cafe.id).filter_by(user_id=user_id)
    mine = {cafe_id for cafe_id, in q}
    return official | following | mine


def get_promoted_cafe_ids():
    statuses = [Cafe.STATUS_OFFICIAL, Cafe.STATUS_VERIFIED]
    q = db.session.query(Cafe.id).filter(Cafe.status.in_(statuses))
    q = q.filter(Cafe.permission != Cafe.PERMISSION_PRIVATE)
    return {cafe_id for cafe_id, in q}


def get_all_cafe_ids():
    q = db.session.query(Cafe.id)
    q = q.filter(Cafe.permission != Cafe.PERMISSION_PRIVATE)
    return {cafe_id for cafe_id, in q}


def get_cafe_topics(cafe_ids, cursor=None, count=20):
    q = db.session.query(Topic.id).filter(Topic.cafe_id.in_(cafe_ids))
    if cursor:
        q = q.filter(Topic.id < cursor)

    q = q.order_by(Topic.id.desc()).limit(count)
    topic_ids = [i for i, in q]
    topics = Topic.cache.get_many(topic_ids)
    if len(topics) < count:
        return topics, 0
    return topics, topics[-1].id
