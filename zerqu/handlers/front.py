# coding: utf-8

from flask import Blueprint
from flask import render_template
from zerqu.libs.utils import is_robot


bp = Blueprint('front', __name__)


@bp.before_request
def handle_app():
    if not is_robot():
        return render_template('app.html')


@bp.route('/')
def home():
    return render_template('index.html')


@bp.route('/t/<int:uid>')
def topic(uid):
    """Show one topic. This handler is designed for SEO."""
    return render_template('topic.html')


@bp.route('/c/<slug>')
def cafe(slug):
    """Show one cafe. This handler is designed for SEO."""
    return render_template('cafe.html')
