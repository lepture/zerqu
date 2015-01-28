# coding: utf-8

from flask import Blueprint
from flask import request
from zerqu.libs import render_template


bp = Blueprint('front', __name__)


@bp.route('/')
def home():
    return render_template('index.html')


@bp.route('/session', methods=['POST', 'DELETE'])
def account():
    if request.method == 'POST':
        return 'login'
    return 'logout'
