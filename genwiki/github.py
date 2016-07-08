import urllib, base64, json
from google.appengine.api import urlfetch


class GitClient(object):

    git_base = 'https://api.github.com'

    def __init__(self, owner, repo, token):
        self.owner = owner
        self.repo = repo
        self.token = token

    def get_repos(self, url, binary=False):
        url = url.lstrip('/')
        url = '%s/repos/%s/%s/%s?access_token=%s' % (self.git_base, self.owner, self.repo, url, self.token)
        res = urlfetch.fetch(url=url, method=urlfetch.GET)

        if binary:
            return res.content

        return json.loads(res.content)

    def post_repos(self, url, data):
        url = url.lstrip('/')
        url = '%s/repos/%s/%s/%s?access_token=%s' % (self.git_base, self.owner, self.repo, url, self.token)

        print '###### %s %s' % (url,data)

        res = urlfetch.fetch(url=url, payload=data, method=urlfetch.POST)

        print '>>>>%s>>>%s' % (res, res.content)

        return json.loads(res.content)

    def put_repos(self, url, data):
        url = url.lstrip('/')
        url = '%s/repos/%s/%s/%s?access_token=%s' % (self.git_base, self.owner, self.repo, url, self.token)
        res = urlfetch.fetch(url=url, payload=data, method=urlfetch.PUT)

        return json.loads(res.content)

    def delete_repos(self, url, data):
        url = url.lstrip('/')
        url = '%s/repos/%s/%s/%s?access_token=%s' % (self.git_base, self.owner, self.repo, url, self.token)
        res = urlfetch.fetch(url=url, method=urlfetch.DELETE)

        return json.loads(res.content)


    def get(self, url, binary=False):
        sep = '?' if '?' not in url else '&'
        res = urlfetch.fetch(url='%s%saccess_token=%s' % (url, sep, self.token), method=urlfetch.GET)

        if not binary:
            return json.loads(res.content)

        return res.content


_git = None


def init(github_key, github_repo):
    global _git
    owner, repo = github_repo.split('/')
    _git = GitClient(owner, repo, github_key)


def upload_file(name, body, id):
    url = '/contents/%s' % name
    data = {'content': base64.encodestring(body), 'message': 'created post'}

    if id:
        data['sha'] = id

    res = _git.put_repos(url, json.dumps(data))
    return {'id': res['content']['sha']}


def delete_file(name, id):
    url = '/contents/%s?message=%s&sha=%s' % (name, 'deleted file', id)
    _git.delete_repos(url)


def get_file(path):
    url = '/contents/%s' % path
    res = _git.get_repos(url)
    return base64.decodestring(res['content'])


def get_files():
    url = '/contents/'
    res = _git.get_repos(url)
    return [{'name': r['name'],
        'id': r['sha']} for r in res]


def get_commits():
    return _git.get_repos('/commits')


def _extract_zipped_files(site_zip):
    folder_name = site_zip.infolist()[0].filename
    return [(p.filename.replace(folder_name, ''),
        site_zip.read(p)) for p in site_zip.infolist() if p.file_size]


def download_commit(commit_id):
    res = _git.get_repos('/zipball/%s' % commit_id, binary=True)
    site_zip = zipfile.ZipFile(StringIO.StringIO(res), 'r')

    return _extract_zipped_files(site_zip)
