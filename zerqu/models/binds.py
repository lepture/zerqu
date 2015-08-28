
import re
import time
from sqlalchemy import event
from zerqu.libs.utils import run_task
from zerqu.libs.cache import execute_pipeline
from .topic import Topic, TopicStat, TopicLike, TopicRead
from .topic import Comment, CommentLike
from .notification import Notification
from .user import User


def bind_events():

    @event.listens_for(Comment, 'after_insert')
    def record_add_comment(mapper, conn, target):
        run_task(_record_add_comment, target)

    @event.listens_for(TopicLike, 'after_insert')
    def record_like_topic(mapper, conn, target):
        run_task(_record_like_topic, target)

    @event.listens_for(TopicRead, 'after_insert')
    def record_read_topic(mapper, conn, target):
        run_task(_record_read_topic, target)

    @event.listens_for(CommentLike, 'after_insert')
    def record_like_comment(mapper, conn, target):
        run_task(_record_like_comment, target)


def _record_add_comment(comment):
    topic = Topic.cache.get(comment.topic_id)
    if not topic:
        return

    with execute_pipeline():
        # update topic stat
        stat = TopicStat(topic.id)
        stat.increase('comments')
        stat['timestamp'] = time.time()

        if topic.user_id != comment.user_id:
            Notification(topic.user_id).add(
                comment.user_id,
                Notification.CATEGORY_COMMENT,
                comment.topic_id,
                comment_id=comment.id,
            )

        names = re.findall(r'(?:^|\s)@([0-9a-z]+)', comment.content)
        for username in set(names):
            user = User.cache.filter_first(username=username)
            if user.id in (comment.user_id, topic.user_id):
                continue

            Notification(user.id).add(
                comment.user_id,
                Notification.CATEGORY_MENTION,
                comment.topic_id,
                comment_id=comment.id,
            )


def _record_like_topic(like):
    topic = Topic.cache.get(like.topic_id)
    if not topic:
        return
    TopicStat(topic.id).increase('likes')

    if topic.user_id != like.user_id:
        Notification(topic.user_id).add(
            like.user_id,
            Notification.CATEGORY_LIKE_TOPIC,
            like.topic_id,
        )


def _record_read_topic(read):
    TopicStat(read.topic_id).increase('reads')


def _record_like_comment(like):
    comment = Comment.cache.get(like.comment_id)
    if not comment:
        return
    if comment.user_id != like.user_id:
        Notification(comment.user_id).add(
            like.user_id,
            Notification.CATEGORY_LIKE_COMMENT,
            comment.topic_id,
            comment_id=like.comment_id,
        )
