
import random
import loremipsum
from zerqu.models import Topic, TopicLike, Comment


def iter_user_topics():
    print('Creating topics')
    for i in range(1024):
        title = loremipsum.generate_sentence()[2]
        paragraphs = loremipsum.generate_paragraphs(random.randint(3, 7))
        content = '\n\n'.join(p[2] for p in paragraphs)
        yield {
            "id": i,
            "title": title,
            "content": content,
            "cafe_id": random.randint(1, 50),
            "user_id": random.randint(1, 500),
        }


def iter_topic_likes():
    print('Creating topics likes')
    for i in range(2000):
        yield {
            "topic_id": random.randint(1, 1000),
            "user_id": random.randint(2, 1000),
        }


def iter_comments():
    print('Creating comments')
    for i in range(2400):
        yield {
            "id": i,
            "topic_id": random.randint(1, 964),
            "user_id": random.randint(2, 1024),
            "content": loremipsum.generate_paragraph()[2]
        }


def iter_data():
    for data in iter_user_topics():
        yield Topic(**data)

    for data in iter_topic_likes():
        yield TopicLike(**data)

    for data in iter_comments():
        yield Comment(**data)
