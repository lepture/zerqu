
import unittest
from zerqu import register_model
from zerqu.app import create_app
from zerqu.models import db


class TestCase(unittest.TestCase):
    def setUp(self):
        app = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'ZERQU_CACHE_TYPE': 'simple',
            'SECRET_KEY': 'secret',
        })
        app.testing = True

        register_model(app)

        self._ctx = app.app_context()
        self._ctx.push()

        db.create_all()
        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        db.drop_all()
        self._ctx.pop()
