# coding: utf-8

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

Base = db.Model


def getitem(self, key):
    return getattr(self, key)


Base.__getitem__ = getitem
