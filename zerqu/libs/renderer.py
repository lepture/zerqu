
import re
from mistune import Renderer, Markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from flask import current_app
from markupsafe import escape
from werkzeug.utils import import_string
from jinja2.utils import urlize
try:
    import html5lib
    import html5lib.sanitizer
except ImportError:
    html5lib = None


class PrettyRenderer(Renderer):
    def link(self, link, title, content):
        html = '<a href="%s"' % link
        if title:
            html = '%s title="%s"' % (html, title)

        if '<figure><img' in content:
            return re.sub(r'(<img.*?>)', r'%s>\1</a>' % html, content)

        html = '%s>%s</a>' % (html, content)
        return html

    def image(self, link, title, alt_text):
        if not title:
            title = alt_text
        return (
            '<figure>'
            '<img src="%s" alt="%s">'
            '<figcaption>%s</figcaption>'
            '</figure>'
        ) % (link, alt_text, title)

    def paragraph(self, content):
        pattern = r'<figure>.*</figure>'
        if re.match(pattern, content):
            return content
        # a single image in this paragraph
        pattern = r'^<img[^>]+>$'
        if re.match(pattern, content):
            return '<figure>%s</figure>\n' % content
        return '<p>%s</p>\n' % content


class HighlightRenderer(PrettyRenderer):
    def block_code(self, text, lang):
        if not lang:
            text = text.strip()
            return u'<pre><code>%s</code></pre>\n' % escape(text)

        try:
            lexer = get_lexer_by_name(lang, stripall=True)
            formatter = HtmlFormatter(noclasses=False, linenos=False)
            return highlight(text, lexer, formatter)
        except:
            return '<pre class="%s"><code>%s</code></pre>\n' % (
                lang, escape(text)
            )


_code_md = Markdown(renderer=HighlightRenderer(escape=True, skip_style=True))
_text_md = Markdown(renderer=PrettyRenderer(escape=True, skip_style=True))


def markdown(s, code=True):
    if code:
        return _code_md.render(s)
    return _text_md.render(s)


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


if html5lib is None:
    def html(s):
        raise RuntimeError('Please install html5lib for "html" renderer')
else:
    _html_parser = html5lib.HTMLParser(
        tree=html5lib.treebuilders.getTreeBuilder('dom'),
        tokenizer=html5lib.sanitizer.HTMLSanitizer,
    )
    _html_walker = html5lib.getTreeWalker('dom')
    _html_serializer = html5lib.serializer.HTMLSerializer()

    def html(s):
        stream = _html_walker(_html_parser.parse(s))
        return u''.join(_html_serializer.serialize(stream)).strip()


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
