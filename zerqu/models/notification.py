# coding: utf-8

import datetime
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import SmallInteger, Integer

from .base import Base, JSON


class Notification(Base):
    __tablename__ = 'zq_notification'

    STATUS_NEW = 1
    STATUS_READ = 0

    CATEGORY_COMMENT = 1
    CATEGORY_MENTION = 2

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    sender_id = Column(Integer)

    status = Column(SmallInteger, default=STATUS_NEW, index=True)
    category = Column(SmallInteger)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    info = Column(JSON)

    __reference__ = {'sender': 'sender_id'}
