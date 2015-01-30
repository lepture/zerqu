# coding: utf-8

from flask import Blueprint
from zerqu.libs import render_template


bp = Blueprint('front', __name__)


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
