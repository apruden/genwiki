from __future__ import print_function

import httplib2
import os
from googleapiclient import discovery
from oauth2client import client
from oauth2client.contrib import appengine
from google.appengine.api import memcache
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload


CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secret_test.json')
SCOPES = 'https://www.googleapis.com/auth/drive'
APPLICATION_NAME = 'genwiki'

http = httplib2.Http(memcache)
decorator = appengine.oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope=SCOPES,
    message='missing secret')

_dev_key = None
_wiki_id = None
_service = None


def init(dev_key, wiki_id):
    global _dev_key
    global _wiki_id
    _dev_key = dev_key
    _wiki_id = wiki_id


def get_service():
    global _service
    if not _service:
        _service = discovery.build('drive', 'v3', developerKey=_dev_key, http=http)
    return _service


def get_files():
    results = get_service().files().list(
        q="'%s' in parents" % (_wiki_id,), pageSize=1000, fields='files(id,name,md5Checksum,properties)').execute(http=decorator.http())

    return [{'name': r['name'],
        'id': r['id']} for r in results.get('files', [])]


def get_file(name, id):
    import io
    download_service = discovery.build('drive', 'v3', developerKey=_dev_key, http=decorator.http())
    request = download_service.files().get_media(fileId=id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)
    return fh.read()


def upload_file(name, body, id=None):
    import StringIO
    output = StringIO.StringIO()
    output.write(body)
    media = MediaIoBaseUpload(output, mimetype='text/plain', chunksize=1024*1024, resumable=True)

    if not id:
        res = get_service().files().create(
                body={'name': name, 'parents': [_wiki_id]},media_body=media).execute(http=decorator.http())
    else:
        res = get_service().files().update(fileId=id, media_body=media).execute(http=decorator.http())

    return res


def delete_file(name, id):
    res = get_service().files().delete(fileId=id).execute(http=decorator.http())
