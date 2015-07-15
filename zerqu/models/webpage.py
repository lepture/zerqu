
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy import String, Integer, DateTime
from .base import Base, JSON


class WebPage(Base):
    __tablename__ = 'zq_webpage'

    uuid = Column(String(34), primary_key=True)
    link = Column(String(400), nullable=False)
    title = Column(String(80))
    image = Column(String(256))
    description = Column(String(140))
    info = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    domain = Column(String(200))
    # first created by this user
    user_id = Column(Integer, nullable=False)
