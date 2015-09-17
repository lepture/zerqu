# coding: utf-8

from flask import Blueprint, request, session, current_app
from flask import render_template, abort, redirect
from werkzeug.security import gen_salt
from zerqu.libs.cache import cache, ONE_HOUR
from zerqu.libs.utils import is_robot, xmldatetime
from zerqu.rec.timeline import get_all_topics
from zerqu.models import db, User, Cafe, Topic, Comment


bp = Blueprint('front', __name__, template_folder='templates')
bp.add_app_template_filter(xmldatetime)


def render(template, **kwargs):
    key = 'front:page:%s' % request.path
    content = render_template(template, **kwargs)
    cache.set(key, content, timeout=ONE_HOUR)
    return render_content(content)


def render_content(content):
    use_app = session.get('app')

    base_url = current_app.config.get('SITE_CANONICAL_URL')
    if not base_url:
        base_url = current_app.config.get('SITE_URL')

    if base_url:
        link = '%s%s' % (base_url.rstrip('/'), request.path)
    else:
        link = request.base_url

    extra_head = ['<meta property="og:url" content="%s">' % link]
    twitter = current_app.config.get('SITE_TWITTER')
    if twitter:
        extra_head.append(
            '<meta name="twitter:site" content="@%s" />' % twitter
        )

    extra_head.append('<link rel="canonical" href="%s">' % link)

    if base_url:
        schema = (
            '<script type="application/ld+json">'
            '{"@context":"http://schema.org","@type":"WebSite",'
            '"name":"%s","url":"%s"}'
            '</script>'
        ) % (current_app.config.get('SITE_NAME'), base_url)
        extra_head.append(schema)

    if not is_robot() and use_app != 'no':
        token = gen_salt(16)
        session['token'] = token
        script = '<script>location.href="/app?token=%s"</script>' % token
        extra_head.append(script)

    return content.replace(u'</head>', u''.join(extra_head) + u'</head>')


@bp.before_request
def hook_for_render():
    use_app = session.get('app')

    if not is_robot() and use_app == 'yes':
        return render_template('front/app.html')

    key = 'front:page:%s' % request.path
    content = cache.get(key)
    if content:
        return render_content(content)


@bp.route('/app')
def run_app():
    if is_robot():
        abort(404)

    referrer = request.referrer
    store = session.pop('token', None)
    token = request.args.get('token')
    if referrer and store and token and store == token:
        session['app'] = 'yes'
        return redirect(referrer)

    if not referrer:
        return redirect('/')

    if not store:
        return 'Please Enable Cookie'

    session['app'] = 'no'
    return redirect(referrer)


@bp.route('/')
def home():
    topics, _ = get_all_topics(0)
    topic_users = User.cache.get_dict({o.user_id for o in topics})
    topic_cafes = Cafe.cache.get_dict({o.cafe_id for o in topics})
    return render(
        'front/index.html',
        topics=topics,
        topic_users=topic_users,
        topic_cafes=topic_cafes,
    )


@bp.route('/t/<int:tid>')
def view_topic(tid):
    """Show one topic. This handler is designed for SEO."""
    topic = Topic.cache.get_or_404(tid)
    cafe = Cafe.cache.get_or_404(topic.cafe_id)
    if cafe.permission == Cafe.PERMISSION_PRIVATE:
        abort(404)

    q = db.session.query(Comment.id).filter_by(topic_id=tid)
    comments = Comment.cache.get_many({i for i, in q.limit(100)})
    comment_users = User.cache.get_dict({o.user_id for o in comments})
    comment_count = Comment.cache.filter_count(topic_id=tid)

    return render(
        'front/topic.html',
        topic=topic,
        cafe=cafe,
        comments=comments,
        comment_users=comment_users,
        comment_count=comment_count,
    )


@bp.route('/c/')
def cafe_list():
    q = db.session.query(Cafe.id)
    q = q.filter(Cafe.permission != Cafe.PERMISSION_PRIVATE)
    q = q.order_by(Cafe.id.desc())
    cafes = Cafe.cache.get_many([i for i, in q.limit(100)])
    return render(
        'front/cafe_list.html',
        cafes=cafes,
    )


@bp.route('/c/<slug>')
def view_cafe(slug):
    """Show one cafe. This handler is designed for SEO."""
    cafe = Cafe.cache.first_or_404(slug=slug)
    if cafe.permission == Cafe.PERMISSION_PRIVATE:
        abort(404)

    q = db.session.query(Topic.id).filter_by(cafe_id=cafe.id)
    q = q.order_by(Topic.id.desc())
    topics = Topic.cache.get_many([i for i, in q.limit(50)])
    topic_users = User.cache.get_dict({o.user_id for o in topics})
    return render(
        'front/cafe.html',
        cafe=cafe,
        topics=topics,
        topic_users=topic_users,
    )


@bp.route('/u/<username>')
def view_user(username):
    user = User.cache.first_or_404(username=username)
    q = db.session.query(Topic.id).filter_by(user_id=user.id)
    q = q.order_by(Topic.id.desc())
    topics = Topic.cache.get_many([i for i, in q.limit(50)])
    return render(
        'front/user.html',
        user=user,
        topics=topics,
    )


@bp.route('/u/<path:name>')
@bp.route('/c/<path:name>')
@bp.route('/t/<path:name>')
@bp.route('/z/<path:name>')
def view_zerqu_app(name):
    """A helper URL router for anything else."""
    if is_robot():
        abort(403)
    return render_template('front/app.html')
