"""`appengine_config` gets loaded when starting a new application instance."""
import vendor, os

vendor.add('lib')

# workaround for permissions error on dev environment
if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
    import imp
    import os.path
    from google.appengine.tools.devappserver2.python import sandbox

    sandbox._WHITE_LIST_C_MODULES += ['_ssl', '_socket']
    psocket = os.path.join(os.path.dirname(os.__file__), 'socket.py')
    imp.load_source('socket', psocket)
