
import base64
import unittest
from flask_oauthlib.utils import to_unicode, to_bytes
from zerqu import create_app
from zerqu.models import db, User, OAuthClient


def encode_base64(text):
    text = to_bytes(text)
    return to_unicode(base64.b64encode(text))


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

        self.app = app
        self.client = app.test_client()
        self.prepare_data()

    def tearDown(self):
        db.drop_all()
        self._ctx.pop()

    def prepare_data(self):
        users = [
            ('zerqu', 'zerqu@gmail.com', None, 10),
            ('test', 'test@gmail.com', 'test-password', 1),
        ]
        for username, email, password, status in users:
            user = User(username=username, email=email, status=status)
            if password:
                user.password = password
            db.session.add(user)
        db.session.commit()

        client = OAuthClient(
            user_id=1,
            name='iOS App',
            client_id='ios',
            client_secret='secret',
            is_confidential=True,
            _redirect_uris='http://localhost/oauth',
        )
        db.session.add(client)
        db.session.commit()
