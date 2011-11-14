from django.core.management.commands.syncdb import Command as SyncdbCommand
from ...utils import appid, have_appserver
from django.db import connections
from ...db.base import DatabaseWrapper
from google.appengine.ext.testbed import Testbed
import sys

class Command(SyncdbCommand):
    def handle_noargs(self, **options):
        from google.appengine.tools import dev_appserver_main
        config = dev_appserver_main.DEFAULT_ARGS.copy()

        from google.appengine.tools import dev_appserver
        

        for connection in connections.all():
            if isinstance(connection, DatabaseWrapper):


                config.update({'mysql_host':'localhost'})
                config.update({'mysql_password':connection.settings_dict["PASSWORD"]})
                #args.update({'mysql_port':'localhost'})
                config.update({'mysql_user':connection.settings_dict["USER"]})
                
                #dev_appserver.SetupStubs('dev~' + appid, **config)
                dev_appserver.SetupStubs(appid, **config)


                from google.appengine.api import rdbms_mysqldb
                from google.appengine import api
                sys.modules['google.appengine.api.rdbms'] = rdbms_mysqldb
                api.rdbms = rdbms_mysqldb
                rdbms_mysqldb.SetConnectKwargs(host='localhost',
                                                user='root', passwd='root')
                rdbms_mysqldb.connect(database='')

                break

        
        super(Command,self).handle_noargs(**options)