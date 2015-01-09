import google.appengine.ext import ndb


class Post(ndb.Model):
	slug = ndb.StringProperty()
	body = ndb.BlobProperty()
	tags = ndb.StringProperty()
	created = ndb.StringProperty()
	modified = ndb.StringProperty()


class Wiki(object):
	def add_post(self, post):
		p = Post(**post.__dict__)
		p.put()

	def del_post(self, post):
		ndb.Key(Post, slug).delete()

	def get_post(self, slug):
		post = ndb.Key(Post, slug).get()
