
import re
from mistune import Renderer, Markdown
from flask import current_app
from markupsafe import escape
from werkzeug.utils import import_string
from jinja2.utils import urlize
try:
    import html5lib
except ImportError:
    html5lib = None


_md = Markdown(renderer=Renderer(escape=True, skip_style=True))


def markdown(s):
    # TODO: highlight
    return _md.render(s)


def html(s):
    if html5lib is None:
        raise RuntimeError('Please install html5lib for "html" renderer')
    # TODO
    return s


RE_NEWLINES = re.compile(r'\r\n|\r')
RE_LINE_SPLIT = re.compile(r'\n{2,}')


def _process_text(s):
    s = escape(s)
    s = urlize(s)
    return s.replace('\n', '<br>')


def text(s):
    s = RE_NEWLINES.sub('\n', s)
    paras = RE_LINE_SPLIT.split(s)
    paras = ['<p>%s</p>' % _process_text(p) for p in paras]
    return ''.join(paras)


def markup(s):
    renderer = current_app.config.get('ZERQU_TEXT_RENDERER')
    if renderer == 'markdown':
        return markdown(s)

    if renderer == 'html':
        return html(s)

    if renderer == 'text':
        return renderer

    func = import_string(renderer)
    return func(s)
