from google.appengine.ext import ndb
from .model import Post

class NdbPost(ndb.Model):
    slug = ndb.StringProperty()
    body = ndb.BlobProperty()
    tags = ndb.StringProperty(repeated=True)
    title = ndb.StringProperty()
    created = ndb.StringProperty()
    modified = ndb.StringProperty()


class Wiki(object):
    def add_post(self, post):
        p = NdbPost(id=post.slug, **post.__dict__)
        p.put()

    def del_post(self, slug):
        ndb.Key(NdbPost, slug).delete()

    def get_post(self, slug):
        try:
            post = ndb.Key(NdbPost, slug).get()
            return Post(**post.to_dict())
        except Exception, e:
            print e

    def find_all(self):
        return [Post(**post.to_dict()) for post in NdbPost.query().iter()]
