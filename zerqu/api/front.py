# coding: utf-8

from flask import jsonify
from .base import ApiBlueprint
from ..versions import VERSION, API_VERSION

api = ApiBlueprint('/')


@api.route('')
def index():
    return jsonify(system='zerqu', version=VERSION, api_version=API_VERSION)
