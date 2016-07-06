from google.appengine.ext import ndb
from google.appengine.api import users
from .model import Post
import gdrive
import hashlib

def get_current_user():
    return users.get_current_user()


def get_login_url():
    return users.create_login_url()


class Settings(ndb.Model):
    repo = ndb.StringProperty()
    github_repo = ndb.StringProperty()
    github_key = ndb.StringProperty()
    gdrive_dev_key = ndb.StringProperty()
    gdrive_wiki_id = ndb.StringProperty()


class NdbPost(ndb.Model):
    slug = ndb.StringProperty()
    body = ndb.BlobProperty()
    tags = ndb.StringProperty(repeated=True)
    title = ndb.StringProperty()
    created = ndb.StringProperty()
    modified = ndb.StringProperty()
    checksum = ndb.StringProperty()
    gdrive_id = ndb.StringProperty()


def get_settings():
    settings = ndb.Key(Settings, 'default').get()
    if not settings:
        settings = Settings(id='default')
        settings.put()
    return settings


def update_settings(**kwargs):
    settings = Settings(id='default', **kwargs)
    settings.put()


def get_files():
    query = ndb.gql('SELECT slug, checksum, gdrive_id FROM NdbPost')
    return [r for r in query.iter()]


class Wiki(object):
    def add_post(self, post, update=False):
        ndb_post = ndb.Key(NdbPost, post.slug).get()
        if not ndb_post or update:
            gdrive_id = ndb_post.gdrive_id if ndb_post else None
            res = gdrive.upload_file('%s.md' % (post.slug,), post.body, gdrive_id)
            p = NdbPost(id=post.slug, checksum=hashlib.md5(post.body).hexdigest(), gdrive_id=res['id'], **post.__dict__)
            p.put()
        else:
            raise Exception('Post already exists: %r' % post.slug)

    def del_post(self, slug):
        gdrive.delete_file(slug)
        ndb.Key(NdbPost, slug).delete()

    def get_post(self, slug):
        post = ndb.Key(NdbPost, slug).get()
        if post:
            return Post(**post.to_dict())

    def find_all(self):
        return [Post(**post.to_dict()) for post in NdbPost.query().iter()]

    def index(self, gdrive_id, post):
        p = NdbPost(id=post.slug, gdrive_id=gdrive_id, checksum=hashlib.md5(post.body).hexdigest(), **post.__dict__)
        p.put()

    def unindex(self, slug):
        ndb.Key(NdbPost, slug).delete()

