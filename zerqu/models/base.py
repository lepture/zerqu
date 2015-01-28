# coding: utf-8

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(db.Model):
    def __getitem__(self, key):
        return getattr(self, key)
