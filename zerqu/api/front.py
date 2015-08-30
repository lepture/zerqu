# coding: utf-8

from flask import jsonify
from flask import current_app, request
from zerqu.models import current_user
from zerqu.libs.renderer import markup
from zerqu.libs.uploader import uploader
from zerqu.libs.errors import APIException
from zerqu.versions import VERSION, API_VERSION
from .base import ApiBlueprint, require_oauth

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


@api.route('upload', methods=['GET'])
@require_oauth(login=True)
def upload_form_data():
    data = uploader.create_form_data(
        current_user.id,
        request.args['content-type']
    )
    if data is None:
        raise APIException(description='Invalid content type')
    return jsonify(data)
