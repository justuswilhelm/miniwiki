"""."""
from urllib.parse import parse_qs, unquote_plus
import os
from html import escape
LRE = __import__('re').compile(r'[A-Z][a-z]+[A-Z][a-zA-Z]+')
t = {
    "i": "<h1>Index</h1><ul>{}</ul><a href='/e'>New</a>".format,
    "u": "<li><a href='/w?{y}'>{y}</a></li>".format,
    "e": """<h1>{y}</h1><p>{c}</p><a href='/e?{y}'>Edit</a><br><a
    href='/dl?{y}'>Delete</a><br><a href='/'>Back</a>""".format,
    "f": """<form method='post'><input name='y'value='{y}'{e}><br><textarea
    name='c'>{c}</textarea><br><button type='submit'>OK</button></form>"""
    .format,
    "o": "<h1>Updated</h1><a href='/w?{}'>Back</a><br><a href='/'>Home</a>"
    .format,
    "d": "<h1>Deleted</h1><a href='/'>Home</a>".format}
k = __import__('redis').Redis.from_url(os.environ['REDIS_URL'])
v = """<!doctype html><html><head><meta charset='UTF-8'><link rel="stylesheet"
href="https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css">
<title>Wiki</title></head><body><div class="container">{}</div></body></html>
""".format


def b(m, p):
    """Create wiki entry dict."""
    return {'m': m, 'p': p}


def i(r, y):
    """Show index."""
    entries = (t['u'](y=y.decode())for y in sorted(k.keys(), reverse=True))
    return v(t['i']("".join(entries)))


def st(r, y):
    """Store wiki entry and redirect to entry page."""
    if "y"in r["p"]and"c"in r["p"] and LRE.fullmatch(r["p"]["y"][0]):
        k.set(escape(r["p"]["y"][0]), escape(r['p']['c'][0]))
        return v(t['o'](y))
    return e(b('GET', r['p']), y)


def e(r, y):
    """Show wiki entry form and allow storing via POST."""
    if r['m'] == 'GET':
        y = escape(y)
        if y in k:
            return v(t['f'](y=y, e='readonly', c=k[y].decode()))
        return v(t['f'](y=y, e='', c=''))
    return st(r, y)


def dl(r, y):
    """Delete a wiki entry."""
    if y in k:
        return k.delete(y) and t['d']()
    return i(r, y)


def w(r, y):
    """Show a wiki entry."""
    if y in k:
        c = " ".join(
            '<a href="/w?{s}">{s}</a>'.format(s=s) if LRE.fullmatch(s) else s
            for s in k[y].decode().split(' ')).replace('\r', '<br>')
        return v(t['e'](y=y, c=c))
    return e(r, y)


routes = {'/': i, '/w': w, '/e': e, '/dl': dl}


def app(v, sr):
    """Return a WSGI compatible response."""
    qs = unquote_plus(v['QUERY_STRING'])
    rq = b(v['REQUEST_METHOD'], parse_qs(v['wsgi.input'].read().decode()))
    sr('200', [('Content-type', 'text/html')])
    yield routes[v['PATH_INFO']](rq, qs).encode()
