from google.appengine.ext import ndb
from google.appengine.api import users
from .model import Post


def get_current_user():
    return users.get_current_user()


def get_login_url():
    return users.create_login_url()


class NdbPost(ndb.Model):
    slug = ndb.StringProperty()
    body = ndb.BlobProperty()
    tags = ndb.StringProperty(repeated=True)
    title = ndb.StringProperty()
    created = ndb.StringProperty()
    modified = ndb.StringProperty()


class Wiki(object):
    def add_post(self, post, update=False):
        if not self.get_post(post.slug) or update:
            p = NdbPost(id=post.slug, **post.__dict__)
            p.put()
        else:
            raise Exception('Post already exists: %r' % post.slug)

    def del_post(self, slug):
        ndb.Key(NdbPost, slug).delete()

    def get_post(self, slug):
        post = ndb.Key(NdbPost, slug).get()
        if post:
            return Post(**post.to_dict())

    def find_all(self):
        return [Post(**post.to_dict()) for post in NdbPost.query().iter()]
