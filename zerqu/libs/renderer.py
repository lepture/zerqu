
from flask import current_app
from werkzeug.utils import import_string


def markdown(text):
    # TODO
    return text


def html(text):
    # TODO
    return text


def markup(text):
    renderer = current_app.config.get('ZERQU_TEXT_RENDERER')
    if renderer == 'markdown':
        return markdown(text)

    if renderer == 'html':
        return html(text)

    func = import_string(renderer)
    return func(text)
