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
from bottle import delete, get, post, put, run, template, Bottle, static_file
from os.path import expanduser
from . import WIKI_FILE, WIKI_DIR, WIKI_PORT, WIKI_HOST, gae_app
from collections import Counter
from collections import defaultdict
from .migration import load_wiki
from .model import *

if not gae_app:
	logging.basicConfig(filename=os.path.join(expanduser('~'), 'wiki.log'), level=logging.DEBUG)

MIME_TYPES = {'.css': 'text/css', '.js': 'application/javascript' }

logging.info('Using wiki file: %s and dir: %s', WIKI_FILE, WIKI_DIR)

_wiki = Wiki()


def new_load_wiki(wiki_dir):
	wiki = {}
	files = [f.replace('.md', '') for f in os.listdir(wiki_dir)]

	for f in files:
		wiki[f] = PostProxy(f)

	return wiki


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

		if not os.path.exists(WIKI_DIR):
			os.makedirs(WIKI_DIR)
			_wiki = load_wiki(WIKI_FILE)

		index = Index()
		init_index()
		initialized = True

	run(app=app, host=WIKI_HOST, port=WIKI_PORT, reloader=reloader)
