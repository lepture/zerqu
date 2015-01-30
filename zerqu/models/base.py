# coding: utf-8

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

Base = db.Model


class Base(db.Model):
    __abstract__ = True

    def __getitem__(self, key):
        return getattr(self, key)
