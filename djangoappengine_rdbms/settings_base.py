# Initialize App Engine SDK if necessary
try:
    from google.appengine.api import apiproxy_stub_map
except ImportError:
    from .boot import setup_env
    setup_env()

from djangoappengine_rdbms.utils import on_production_server, have_appserver

DEBUG = not on_production_server
TEMPLATE_DEBUG = DEBUG

ROOT_URLCONF = 'urls'

if on_production_server:
    EMAIL_BACKEND = 'djangoappengine_rdbms.mail.AsyncEmailBackend'
else:
    EMAIL_BACKEND = 'djangoappengine_rdbms.mail.EmailBackend'

# Specify a queue name for the async. email backend
EMAIL_QUEUE_NAME = 'default'

PREPARE_UPLOAD_BACKEND = 'djangoappengine_rdbms.storage.prepare_upload'
SERVE_FILE_BACKEND = 'djangoappengine_rdbms.storage.serve_file'
DEFAULT_FILE_STORAGE = 'djangoappengine_rdbms.storage.BlobstoreStorage'
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
FILE_UPLOAD_HANDLERS = (
    'djangoappengine_rdbms.storage.BlobstoreFileUploadHandler',
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'TIMEOUT': 0,
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

if not on_production_server:
    INTERNAL_IPS = ('127.0.0.1',)
