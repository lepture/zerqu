
import unittest
from zerqu import register_base
from zerqu.app import create_app
from zerqu.models import db

DATABASE = 'postgresql://postgres@localhost/testing'


class TestCase(unittest.TestCase):
    def setUp(self):
        app = create_app({
            'SQLALCHEMY_DATABASE_URI': DATABASE,
            'ZERQU_CACHE_TYPE': 'simple',
            'OAUTH_CACHE_TYPE': 'simple',
            'RATE_LIMITER_TYPE': 'cache',
            'SECRET_KEY': 'secret',
        })
        app.testing = True

        register_base(app)

        self._ctx = app.app_context()
        self._ctx.push()

        db.drop_all()
        db.create_all()
        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        self._ctx.pop()
