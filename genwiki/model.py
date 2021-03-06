import codecs
import os
import re
import json
from . import WIKI_DIR
from collections import defaultdict


def _get_filename(slug):
    return os.path.join(WIKI_DIR, '%s.md' % (slug,))


class Index(object):
    def __init__(self):
        self.texts, self.words = {}, set()
        self.finvindex = defaultdict(set)

    def update_index(self, doc_id, words):
        for w in words:
            self.finvindex[w].add((doc_id, self.texts[doc_id].index(w)))

    def put(self, doc_id, content):
        self.remove(doc_id)
        txt = filter(None, map(lambda x: re.sub('[^a-z0-9]', '', x.lower()), filter(lambda w: len(w) > 3, content.split())))
        self.texts[doc_id] = txt
        self.update_index(doc_id, set(txt))

    def remove(self, doc_id):
        for k, v in self.finvindex.items():
            to_delete = []
            for w in v:
                if w[0] == doc_id:
                    to_delete.append(w)

            for t in to_delete:
                v.remove(t)

    def term_search(self, terms):
        if not set(terms).issubset(set(self.finvindex.keys())):
            return set()

        return reduce(set.intersection,
                (set(x[0] for x in txtindx)
                    for term, txtindx in self.finvindex.items()
                    if term in terms),
                set(self.texts.keys()))

    def search(self, phrase):
        import difflib

        wordsinphrase = phrase.strip().split()

        tmp = []

        for w in wordsinphrase:
            r = difflib.get_close_matches(w, self.finvindex.keys(), cutoff=0.8)
            if r:
                tmp.append(r[0])
            else:
                tmp.append(w)

        wordsinphrase = tmp

        if not set(wordsinphrase).issubset(set(self.finvindex.keys())):
            return set()

        if len(wordsinphrase) < 2:
            firstword, otherwords = wordsinphrase[0], wordsinphrase[1:]
        else:
            firstword, otherwords = wordsinphrase[0], []

        found = []

        for txt in self.term_search(wordsinphrase):
            for firstindx in (indx for t,indx in self.finvindex[firstword] if t == txt):
                if all((txt, firstindx+1 + otherindx) in self.finvindex[otherword]
                        for otherindx, otherword in enumerate(otherwords)):
                    found.append(txt)

        return found


class Post(object):
    def __init__(self, title, body, created=None, modified=None, tags=None, **kwargs):
        self.title = str(title).strip()
        self.body = str(body.strip()) if body else None
        self.slug = str(Post.build_slug(self.title))
        self.tags = filter(None, tags.split(',') if isinstance(tags, basestring) else tags if tags else [])
        self.created = str(created) if created else None
        self.modified = str(modified) if modified else None

    def __cmp__(self, other):
        if not other:
            return -1

        return (int(self.created > other.created) or -1) if self.created != other.created else 0

    def serialize(self):
        buf = ['<!---']
        for k, v in self.__dict__.items():
            if k not in ['body', 'slug', 'tags']:
                buf.append('='.join((str(k), str(v))))
            elif k == 'tags':
                buf.append('%s=%s' % (k, ','.join(self.tags)))
        buf.append('--->')
        buf.append(self.body)

        return '\n'.join(buf)

    @staticmethod
    def build_slug(title):
        return re.sub(r'[\.!,;/\?#\ ]+', '-', title).strip().lower()

    @staticmethod
    def build(data, title=None):
        tmp = {}
        body = []
        header = False

        for line in data.split('\n'):
            if line == '<!---':
                header = True
            elif line == '--->':
                header = False
            elif header:
                (k, v) = [v.strip() for v in line.split('=')]
                tmp[k] = v

            body.append(line)

        tmp['body'] = '\n'.join(body)

        if not tmp.get('title'):
            tmp['title'] = ' '.join(title.replace('.md', '').split('-'))

        return Post(**tmp)


class PostProxy(object):
    def __init__(self, slug):
        self.slug = slug
        self.post = None

    def __getattr__(self, name):
        if not self.post:
            with codecs.open(_get_filename(self.slug), 'r', 'utf8') as f:
                self.post = Post.build(f.read())

        if name == 'body' and not getattr(self.post, 'body', None):
            with codecs.open(os.path.join(WIKI_DIR, '%s.md' % (self.slug,)), 'r', 'utf8') as f:
                self.post.body = f.read()

        return getattr(self.post, name)


class Wiki(object):
    def add_post(self, post):
        self._save_post(post)

    def del_post(self, post):
        os.remove(_get_filename(post.slug))

    def get_post(self, slug):
        if os.path.exists(_get_filename(slug)):
            with codecs.open(_get_filename(slug), 'r', 'utf8') as f:
                return Post.build(f.read())

    def find_all(self):
        return [PostProxy(f.replace('.md', '')) for f in os.listdir(WIKI_DIR)]

    def _save_post(self, post):
        with codecs.open(_get_filename(post.slug), 'w', 'utf8') as f:
            tmp = post.__dict__.items()
            body = tmp.pop('body', '')
            f.write('<!---\n%s\n--->\n' % '\n'.join(['%s = %s' % (k, v) for k,v in tmp.items()]))
            f.write(post.body)
