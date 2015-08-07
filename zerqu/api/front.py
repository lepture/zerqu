# coding: utf-8

from flask import jsonify
from flask import current_app, request
from .base import ApiBlueprint, require_oauth
from ..libs.renderer import markup
from ..versions import VERSION, API_VERSION

api = ApiBlueprint('')


@api.route('')
def index():
    config = current_app.config
    return jsonify(
        system='zerqu',
        version=VERSION,
        api_version=API_VERSION,
        site=config.get('SITE_NAME'),
        description=config.get('SITE_DESCRIPTION'),
        remote_addr=request.remote_addr,
    )


@api.route('preview', methods=['POST'])
@require_oauth(login=True)
def preview_text():
    data = request.get_json()
    text = data.get('text')
    if not text:
        return ''
    return markup(text)
