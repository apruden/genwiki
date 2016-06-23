import bottle
import datetime
import copy
import codecs
import difflib
import re
import itertools
import os
import sys
import signal
import time
import logging
import ConfigParser
import zipfile
from bottle import delete, get, post, put, run, template, Bottle, static_file, request, install, redirect
from os.path import expanduser
from . import WIKI_FILE, WIKI_DIR, WIKI_PORT, WIKI_HOST, gae_app
from collections import Counter
from collections import defaultdict
from .migration import load_wiki
from .model import *


class BinderPlugin:
    api = 2

    def apply(self, callback, route_ctx):
        def wrapper(*args, **url_args):
            action_kwargs = {}
            action_kwargs.update(url_args)

            if bottle.request.query:
                action_kwargs.update(bottle.request.query)

            if isinstance(bottle.request.json, dict):
                action_kwargs.update(bottle.request.json)

            return callback(**action_kwargs)

        return wrapper


app = Bottle()
app.install(BinderPlugin())


if gae_app:
    import gae
    _wiki = gae.Wiki()
    def is_authenticated():
        user = gae.get_current_user()
        return bool(user and user.email() in ['alex.prudencio@gmail.com', 'test@example.com'])

    def get_login_url():
        return gae.get_login_url()
else:
    _wiki = Wiki()
    logging.basicConfig(filename=os.path.join(expanduser('~'), 'wiki.log'), level=logging.DEBUG)
    def is_authenticated():
        return True


def authenticated(callback):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return redirect(get_login_url())
        return callback(*args, **kwargs)
    return wrapper


app.install(authenticated)


MIME_TYPES = {'.css': 'text/css', '.js': 'application/javascript' }


logging.info('Using wiki file: %s and dir: %s', WIKI_FILE, WIKI_DIR)


def new_load_wiki(wiki_dir):
    wiki = {}
    files = [f.replace('.md', '') for f in os.listdir(wiki_dir)]

    for f in files:
        wiki[f] = PostProxy(f)

    return wiki


@app.get('/')
def index():
    if not gae_app:
        import pkg_resources
        return template(pkg_resources.resource_stream('genwiki', 'templates/index.html').read())
    return template('genwiki/templates/index.html')

@app.get('/static/<path:path>')
def static_resources(path):
    from email.utils import formatdate
    import pkg_resources

    if bottle.request.headers.get('If-Modified-Since'):
        bottle.response.status = 304
        return

    bottle.response.headers['Last-Modified'] = formatdate(timeval=None, localtime=False, usegmt=True)
    bottle.response.headers['Content-Type'] = MIME_TYPES.get(os.path.splitext(path)[1], 'text/plain')

    return pkg_resources.resource_stream('genwiki', 'static/%s' % path).read()

@app.get('/posts')
def get_posts(offset=0, limit=10):
    res = [{'title': p.title, 'slug': p.slug, 'created': p.created, 'modified': p.modified} for p in sorted(_wiki.find_all(), reverse=True)]
    return {'posts': res}

@app.get('/posts/:post_id')
def show_post(post_id):
    post = _wiki.get_post(post_id)
    return copy.copy(post.__dict__)

@app.get('/search')
def search(q=None, limit=20, offset=0):
    limit, offset, matches = int(limit), int(offset), []

    if not q:
        matches = [{'title': p.title, 'post_id': p.slug} for p in sorted(_wiki.find_all(), reverse=True)]
        matches = matches[offset:offset+limit]
        return {'matches' : matches}

    found = index.search(q)

    for f in found:
        post = _wiki.get_post(f)
        matches.append({'post_id': post.slug,
            'title' : post.title,
            'ratio': 1 if q in found else 0})

    return {'matches' : matches}

@app.post('/posts')
def create_post(title, body, tags=[]):
    tags = [str(t).strip() for t in tags if t]
    post = _wiki.get_post(Post.build_slug(title))

    if post:
        raise HTTPError(status=409)

    created = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    post = Post(title=title, body=body, tags=tags, created=created)
    _wiki.add_post(post)

    return post.__dict__

@app.put('/posts/:post_id')
def update_post(post_id, title, body, tags=[]):
    tags = [str(t).strip() for t in tags if t]
    post = _wiki.get_post(post_id)

    if not post:
        raise HTTPError(status=404)

    modified=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    body_lines = [l.rstrip() for l in body.split('\n')]

    post = Post(title=title, body='\n'.join(body_lines), tags=tags, created=post.created, modified=modified)

    if post.slug != post_id:
        wiki.del_post(post_id)

    _wiki.add_post(post)

    return post.__dict__


@app.delete('/posts/:post_id')
def delete_post(post_id):
    _wiki.del_post(post_id)


@app.post('/wiki/import')
def do_import():
    uploaded = request.files.get('upload')
    site_zip = zipfile.ZipFile(uploaded.file,'r')
    posts = _extract_zipped_files(site_zip)
    [_wiki.add_post(post) for post in posts]


def _extract_zipped_files(site_zip):
    def _build_post(data):
        tmp = {}
        body = []
        header = False

        for line in data.split('\n'):
            if line == '<!---':
                header = True
            elif line == '--->':
                header = False
            elif header:
                (k,v) = [v.strip() for v in line.split('=')]
                tmp[k] = v
            else:
                body.append(line)

        tmp['body'] = ''.join(body)

        return Post(**tmp)

    return [_build_post(site_zip.read(p)) for p in site_zip.infolist() if p.file_size]



index = None
initialized = False


def init_index():
    for p in _wiki.find_all():
        index.put(p.slug, p.body)


def main(reloader=False, path=None):
    '''Runs the wiki locally'''
    global _wiki, WIKI_FILE, index, initialized

    if not initialized:
        if path:
            WIKI_FILE = path

        if not gae_app and not os.path.exists(WIKI_DIR):
            os.makedirs(WIKI_DIR)
            _wiki = load_wiki(WIKI_FILE)

        index = Index()
        init_index()
        initialized = True

    run(app=app, host=WIKI_HOST, port=WIKI_PORT, reloader=reloader)
