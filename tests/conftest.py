import pytest

from zerqu import create_app
from zerqu.models import db
from fixtures import auth


@pytest.fixture()
def app(request):
    app = create_app({
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'OAUTH2_CACHE_TYPE': 'simple',
        'ZERQU_CACHE_TYPE': 'simple',
        'SECRET_KEY': 'secret',
    })
    app.testing = True
    ctx = app.app_context()
    ctx.push()

    db.init_app(app)
    db.create_all()
    auth.run()

    @request.addfinalizer
    def final():
        db.drop_all()
        ctx.pop()

    return app


@pytest.fixture()
def client(app):
    return app.test_client()
