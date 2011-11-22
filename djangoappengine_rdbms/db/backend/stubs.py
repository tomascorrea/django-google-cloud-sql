from ...utils import appid, have_appserver, on_production_server
from google.appengine.ext.testbed import Testbed
from urllib2 import HTTPError, URLError
import logging
import time

REMOTE_API_SCRIPTS = (
    '$PYTHON_LIB/google/appengine/ext/remote_api/handler.py',
    'google.appengine.ext.remote_api.handler.application',
)

def auth_func():
    import getpass
    return raw_input('Login via Google Account (see note above if login fails): '), getpass.getpass('Password: ')

def rpc_server_factory(*args, ** kwargs):
    from google.appengine.tools import appengine_rpc
    kwargs['save_cookies'] = True
    return appengine_rpc.HttpRpcServer(*args, ** kwargs)

class StubManager(object):
    def __init__(self):
        self.testbed = Testbed()
        self.active_stubs = None
        self.pre_test_stubs = None

    def setup_stubs(self, connection):
        if self.active_stubs is not None:
            return
        if not have_appserver:
            self.setup_local_stubs(connection)

    def activate_test_stubs(self):
        if self.active_stubs == 'test':
            return
        self.testbed.activate()
        self.pre_test_stubs = self.active_stubs
        self.active_stubs = 'test'
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_taskqueue_stub()
        self.testbed.init_urlfetch_stub()
        self.testbed.init_user_stub()
        self.testbed.init_xmpp_stub()
        self.testbed.init_channel_stub()
        self.setup_local_rdbms(connection)

    def deactivate_test_stubs(self):
        if self.active_stubs == 'test':
            self.testbed.deactivate()
            self.active_stubs = self.pre_test_stubs

    def setup_local_stubs(self, connection):
        if self.active_stubs == 'local':
            return
        
        from google.appengine.tools import dev_appserver_main
        args = dev_appserver_main.DEFAULT_ARGS.copy()
        args.update(connection.settings_dict.get('DEV_APPSERVER_OPTIONS', {}))
        log_level = logging.WARNING
        logging.getLogger().setLevel(log_level)
        from google.appengine.tools import dev_appserver
        dev_appserver.SetupStubs('dev~' + appid, **args)
        self.setup_local_rdbms(connection)

        self.active_stubs = 'local'

    def setup_remote_stubs(self, connection):
        if self.active_stubs == 'remote':
            return
        
        self.setup_default_rdbms(connection)
        if not connection.remote_api_path:
            from ...utils import appconfig
            for handler in appconfig.handlers:
                if handler.script in REMOTE_API_SCRIPTS:
                    connection.remote_api_path = handler.url.split('(', 1)[0]
                    break
        server = '%s.%s' % (connection.remote_app_id, connection.domain)
        remote_url = 'https://%s%s' % (server, connection.remote_api_path)
        logging.info('Setting up remote_api for "%s" at %s' %
                     (connection.remote_app_id, remote_url))
        if not have_appserver:
            print('Connecting to remote_api handler.\n\n'
                  'IMPORTANT: Check your login method settings in the '
                  'App Engine Dashboard if you have problems logging in. '
                  'Login is only supported for Google Accounts.\n')
        from google.appengine.ext.remote_api import remote_api_stub
        remote_api_stub.ConfigureRemoteApi(None,
            connection.remote_api_path, auth_func, servername=server,
            secure=connection.secure_remote_api,
            rpc_server_factory=rpc_server_factory)
        retry_delay = 1
        while retry_delay <= 16:
            try:
                remote_api_stub.MaybeInvokeAuthentication()
            except HTTPError, e:
                if not have_appserver:
                    print 'Retrying in %d seconds...' % retry_delay
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                break
        else:
            try:
                remote_api_stub.MaybeInvokeAuthentication()
            except HTTPError, e:
                raise URLError("%s\n"
                               "Couldn't reach remote_api handler at %s.\n"
                               "Make sure you've deployed your project and "
                               "installed a remote_api handler in app.yaml. "
                               "Note that login is only supported for "
                               "Google Accounts. Make sure you've configured "
                               "the correct authentication method in the "
                               "App Engine Dashboard."
                               % (e, remote_url))
        logging.info('Now using the remote datastore for "%s" at %s' %
                     (connection.remote_app_id, remote_url))
        self.active_stubs = 'remote'


    def setup_local_rdbms(self, connection):
        
        from ...db.backend.base import DatabaseWrapper

        if isinstance(connection, DatabaseWrapper):
            from google.appengine.api import rdbms_mysqldb
            from google.appengine import api
            import sys

            # Store the defalt rdbms if i need to restore it
            from google.appengine.api import rdbms
            self._default_rdbms = rdbms
            sys.modules['google.appengine.api.rdbms'] = rdbms_mysqldb
            api.rdbms = rdbms_mysqldb
            rdbms_mysqldb.SetConnectKwargs(
                                            host=connection.settings_dict["HOST"],
                                            user=connection.settings_dict["USER"], 
                                            passwd=connection.settings_dict["PASSWORD"]
                                            )
            rdbms_mysqldb.connect(database='')

    def setup_default_rdbms(self,connection):
        if hasattr(self,"_default_rdbms"):
            import sys
            from google.appengine import api
            from google.appengine.api import rdbms
            sys.modules['google.appengine.api.rdbms'] = self._default_rdbms
            api.rdbms = self._default_rdbms


stub_manager = StubManager()
