import yaml
from .model import *

class folded_unicode(unicode): pass

class literal_unicode(unicode): pass

def folded_unicode_representer(dumper, data):
	return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='>')

def literal_unicode_representer(dumper, data):
	return dumper.represent_scalar(u'tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(folded_unicode, folded_unicode_representer)
yaml.add_representer(literal_unicode, literal_unicode_representer)


def load_wiki(wiki_file):
	wiki = {}

	with file(wiki_file) as f:
		for p in yaml.load_all(f):
			p.pop('slug', None)
			post = Post(**p)
			post.save_new_post()
			wiki[post.slug] = PostProxy(post.slug)

	return wiki
