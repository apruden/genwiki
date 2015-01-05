import os
import ConfigParser

def safe_config_get(config, section, option, default):
	if config.has_section(section) and config.has_option(section, option):
		return config.get(section, option)

	return default

gae_app = bool(os.environ.get('SERVER_SOFTWARE'))

if not gae_app:
	config = ConfigParser.RawConfigParser()
	config.read(os.path.join(os.path.expanduser('~'), '.genwikirc'))

	WIKI_FILE = safe_config_get(config, 'wiki', 'file', os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wiki.yaml'))
	WIKI_DIR = safe_config_get(config, 'wiki', 'dir', os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wiki_dir'))
	WIKI_HOST = 'localhost'
	WIKI_PORT = int(safe_config_get(config, 'wiki', 'port', 8088))
else:
	WIKI_FILE = None
	WIKI_DIR = None
	WIKI_HOST = None
	WIKI_PORT = None
