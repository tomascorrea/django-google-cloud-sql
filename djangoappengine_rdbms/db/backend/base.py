from django.db.backends.mysql.base import DatabaseWrapper as MysqlDatabaseWrapper

from django.db.backends.mysql.base import CursorWrapper



from ...utils import appid

class DatabaseWrapper(MysqlDatabaseWrapper):
    
    def __init__(self, *args, **kwargs):
        
        super(DatabaseWrapper,self).__init__(*args, **kwargs)


    def _cursor(self):
        from ...boot import setup_rdbms
        setup_rdbms()
        from google.appengine.api import rdbms
        conn = rdbms.connect(
                            instance=appid, 
                            database=self.settings_dict["NAME"])
        cursor = conn.cursor()
        return cursor

    def get_server_version(self):
        return '5.1'