
from zerqu.models import Cafe


def iter_site_cafes():
    yield {
        "id": 1,
        "name": "Site",
        "slug": "site",
        "content": "Things about this site. This very site is something",
        "permission": 6,
        "user_id": 1,
        "style": {
            "base_color": "#42B983"
        }
    }

    yield {
        "id": 2,
        "name": "About",
        "slug": "about",
        "permission": 6,
        "user_id": 1,
        "style": {
            "logo_url": "https://avatars0.githubusercontent.com/u/290496"
        }
    }


def iter_data():
    for data in iter_site_cafes():
        yield Cafe(**data)
