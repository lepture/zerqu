# coding: utf-8

from flask.globals import _app_ctx_stack
from flask.templating import render_template as _render_template
from .utils import is_robot, is_mobile


def render_template(template_name, **context):
    if is_robot():
        return _render_template(template_name, **context)
    ctx = _app_ctx_stack.top
    if is_mobile():
        template = ctx.app.config.get('ZERQU_MOBILE_TEMPLATE')
    else:
        template = ctx.app.config.get('ZERQU_BROWSER_TEMPLATE')
    return _render_template(template, **context)
