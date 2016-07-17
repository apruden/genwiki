from google.appengine.ext import ndb
from google.appengine.api import users
from .model import Post
#import gdrive as data
#import github as data
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
    data_id = ndb.StringProperty()


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
    query = ndb.gql('SELECT slug, data_id FROM NdbPost')
    return [r for r in query.iter()]


class NullData(object):
    def init(*args, **kwargs):
        pass

    def get_file(*args, **kwargs):
        pass

    def get_files(*args, **kwargs):
        pass

    def delete_file(*args, **kwargs):
        pass

    def upload_file(*args, **kwargs):
        pass


data = NullData()


class Wiki(object):
    def add_post(self, post, update=False):
        ndb_post = ndb.Key(NdbPost, post.slug).get()

        if not ndb_post or update:
            data_id = ndb_post.data_id if ndb_post else None
            res = data.upload_file('%s.md' % (post.slug,), post.serialize(), data_id)
            p = NdbPost(id=post.slug, data_id=res.get('id') if res else None, **post.__dict__)
            p.put()
        else:
            raise Exception('Post already exists: %r' % post.slug)

    def del_post(self, slug):
        post = ndb.Key(NdbPost, slug).get()
        if post:
            data.delete_file('%s.md' % slug, post.data_id)
            ndb.Key(NdbPost, slug).delete()

    def get_post(self, slug):
        post = ndb.Key(NdbPost, slug).get()
        if post:
            return Post(**post.to_dict())

    def find_all(self):
        return [Post(**post.to_dict()) for post in NdbPost.query().iter()]

    def index(self, data_id, post):
        p = NdbPost(id=post.slug, data_id=data_id, **post.__dict__)
        p.put()

    def unindex(self, slug):
        ndb.Key(NdbPost, slug).delete()
