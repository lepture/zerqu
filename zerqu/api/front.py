# coding: utf-8

from flask import jsonify
from flask import Blueprint
from ..versions import VERSION, API_VERSION

bp = Blueprint('api_base', __name__)


@bp.route('')
def index():
    return jsonify(system='zerqu', version=VERSION, api_version=API_VERSION)
