
import random
from zerqu.models import Cafe

TYPEWRITER = (
    "https://d262ilb51hltx0.cloudfront.net/max/1600/"
    "1*TI7VtPCCe6bPi9xc-k_W1w.jpeg"
)


def iter_site_cafes():
    yield {
        "id": 1,
        "name": "Site",
        "slug": "site",
        "content": "Things about this site. This very site is something",
        "permission": 6,
        "status": 9,
        "user_id": 1,
        "style": {
            "color": "#42B983",
            "cover": TYPEWRITER
        }
    }

    yield {
        "id": 2,
        "name": "About",
        "slug": "about",
        "content": (
            "This site is created by lepture, view his blog: "
            "http://lepture.com"
        ),
        "permission": 6,
        "status": 9,
        "user_id": 1,
        "style": {
            "logo": "https://avatars0.githubusercontent.com/u/290496"
        }
    }


def iter_user_cafes():
    names = []
    with open('/usr/share/dict/words', 'rb') as f:
        for word in f:
            word = word.strip()
            if 4 < len(word) < 8:
                names.append(word)

    def pick_name():
        first = random.choice(names)
        last = random.choice(names)
        return '%s %s' % (first, last)

    for i in range(3, 68):
        name = pick_name()
        slug = name.replace(' ', '-').lower()
        color = (
            random.randint(0, 256),
            random.randint(0, 256),
            random.randint(0, 256),
        )
        yield {
            "id": i,
            "name": name,
            "slug": slug,
            "permission": random.choice([0, 3, 6, 9]),
            "status": random.choice([0, 1, 6]),
            "user_id": random.randint(1, 1024),
            "style": {
                "color": 'rgb(%d, %d, %d)' % color
            }
        }


def iter_data():
    for data in iter_site_cafes():
        yield Cafe(**data)
    for data in iter_user_cafes():
        yield Cafe(**data)
