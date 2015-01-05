import os
import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(os.path.join(os.path.expanduser('~'), '.genwikirc'))

WIKI_FILE = config.get('wiki', 'file') or os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wiki.yaml')
WIKI_DIR = config.get('wiki', 'dir') or os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wiki_dir')
WIKI_HOST = 'localhost'
WIKI_PORT = int(config.get('wiki', 'port') or 8088)

