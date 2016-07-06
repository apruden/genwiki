import httplib2
import pickle
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
import gdrive
import webapp2
import jinja2
import gae
from os.path import expanduser
from . import WIKI_FILE, WIKI_DIR, WIKI_PORT, WIKI_HOST, gae_app
from collections import Counter
from collections import defaultdict
from .migration import load_wiki
from .model import *
from googleapiclient import discovery
from oauth2client import client
from oauth2client.contrib import appengine
from google.appengine.api import memcache


_settings = gae.get_settings()

gdrive.init(_settings.gdrive_dev_key, _settings.gdrive_wiki_id)

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    autoescape=True,
    extensions=['jinja2.ext.autoescape'])


app = webapp2.WSGIApplication([(gdrive.decorator.callback_path, gdrive.decorator.callback_handler())])


def pascal_case(name):
    return ''.join([part.capitalize() for part in name.split('_')])


def extract_params(f):
    def wrapper(handler, *args, **kwargs):
        kwargs.update(handler.request.params)
        if handler.request.headers.get('content-type') == 'application/json':
            kwargs.update(json.loads(handler.request.body))
        res = f(handler, *args, **kwargs)
        if res:
            res = json.dumps(res) if isinstance(res, dict) else str(res)
            handler.response.write(res)
    return wrapper


def handler_factory(f, method):
    name = '%sHandler' % pascal_case(f.__name__)
    m = { method: extract_params(f)}
    return name, type(name, (webapp2.RequestHandler,), m)


def _build_decorator(route, method):
    def wrapper(f):
        if route not in _routes:
            name, cls = handler_factory(f, method)
            app.router.add(webapp2.Route(route, handler=cls))
            _routes[route] = cls
        else:
            setattr(_routes[route], method, extract_params(f))
        return f
    return wrapper


_routes = {}


def get(route):
    return _build_decorator(route, 'get')

def post(route):
    return _build_decorator(route, 'post')


def put(route):
    return _build_decorator(route, 'put')


def delete(route):
    return _build_decorator(route, 'delete')


def index_new(added):
    for p in added:
        tmp = gdrive.get_file(p[2])
        _wiki.index(p[2], Post.build(tmp))


def delete_removed(removed):
    for p in removed:
        _wiki.unindex(p[0])


@get('/sync')
@gdrive.decorator.oauth_required
def sync_files(handler):
    current = {(f['name'].replace('.md', ''), f['md5Checksum'], f['id']) for f in gdrive.get_files()}
    saved = {(f.slug, f.checksum, f.gdrive_id) for f in gae.get_files()}
    removed = saved - current
    delete_removed(removed)
    added = current - saved
    index_new(added)


if gae_app:
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
        if not is_authenticated() and not callback.func_name == 'do_import':
            return redirect(get_login_url())
        return callback(*args, **kwargs)
    return wrapper


MIME_TYPES = {'.css': 'text/css', '.js': 'application/javascript' }

logging.info('Using wiki file: %s and dir: %s', WIKI_FILE, WIKI_DIR)


def new_load_wiki(wiki_dir):
    wiki = {}
    files = [f.replace('.md', '') for f in os.listdir(wiki_dir)]

    for f in files:
        wiki[f] = PostProxy(f)

    return wiki


@get('/')
@gdrive.decorator.oauth_required
def index(handler):
    template = JINJA_ENVIRONMENT.get_template('templates/index.html')
    handler.response.write(template.render())


@get('/posts')
@gdrive.decorator.oauth_required
def get_posts(handler, offset=0, limit=10):
    res = [{'title': p.title, 'slug': p.slug, 'created': p.created, 'modified': p.modified} for p in sorted(_wiki.find_all(), reverse=True)]
    return {'posts': res}


@get('/posts/<post_id>')
@gdrive.decorator.oauth_required
def show_post(handler, post_id):
    post = _wiki.get_post(post_id)
    return copy.copy(post.__dict__)


@get('/search')
@gdrive.decorator.oauth_required
def search(handler, q=None, limit=20, offset=0):
    limit, offset, matches = int(limit), int(offset), []

    if not q:
        matches = [{'title': p.title, 'post_id': p.slug} for p in sorted(_wiki.find_all(), reverse=True)]
        matches = matches[offset : offset+limit]
        return {'matches' : matches}

    found = index.search(q)

    for f in found:
        post = _wiki.get_post(f)
        matches.append({'post_id': post.slug,
            'title' : post.title,
            'ratio': 1 if q in found else 0})

    return {'matches' : matches}


@post('/_settings')
def update_settings(handler, **kwargs):
    gae.update_settings(**kwargs)


@post('/posts')
@gdrive.decorator.oauth_required
def create_post(handler, title, body, tags=[]):
    tags = [str(t).strip() for t in tags if t]
    post = _wiki.get_post(Post.build_slug(title))

    if post:
        raise HTTPError(status=409)

    created = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    post = Post(title=title, body=body, tags=tags, created=created)
    _wiki.add_post(post)

    return post.__dict__

@put('/posts/<post_id>')
@gdrive.decorator.oauth_required
def update_post(handler, post_id, title, body, tags=[]):
    tags = [str(t).strip() for t in tags if t]
    post = _wiki.get_post(post_id)

    if not post:
        raise HTTPError(status=404)

    modified=datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    body_lines = [l.rstrip() for l in body.split('\n')]

    post = Post(title=title, body='\n'.join(body_lines), tags=tags, created=post.created, modified=modified)

    if post.slug != post_id:
        wiki.del_post(post_id)

    _wiki.add_post(post, update=True)

    return post.__dict__


@delete('/posts/<post_id>')
@gdrive.decorator.oauth_required
def delete_post(post_id):
    _wiki.del_post(post_id)


@post('/wiki/import')
@gdrive.decorator.oauth_required
def do_import():
    uploaded = request.files.get('upload')
    site_zip = zipfile.ZipFile(uploaded.file,'r')
    posts = _extract_zipped_files(site_zip)
    for post in posts:
        try:
            _wiki.add_post(post)
        except Exception, e:
            print 'ignoring: %s' % e

def _extract_zipped_files(site_zip):
    def _build_post(data):
        return Post.build(data)

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


