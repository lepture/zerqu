
import unittest
from zerqu import create_app
from zerqu.models import db
from fixtures import auth


class TestCase(unittest.TestCase):
    def setUp(self):
        app = create_app({
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'ZERQU_CACHE_TYPE': 'simple',
            'SECRET_KEY': 'secret',
        })
        app.testing = True
        self._ctx = app.app_context()
        self._ctx.push()

        db.init_app(app)
        db.create_all()
        auth.run()

        self.app = app
        self.client = app.test_client()

    def tearDown(self):
        db.drop_all()
        self._ctx.pop()
