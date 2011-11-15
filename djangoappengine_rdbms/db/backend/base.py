import re
import sys


from ...utils import appid, on_production_server
from .stubs import stub_manager

from django.db.backends import *
from django.db.backends.signals import connection_created
from django.db.backends.mysql.client import DatabaseClient
from django.db.backends.mysql.creation import DatabaseCreation
from introspection import DatabaseIntrospection
from django.db.backends.mysql.validation import DatabaseValidation
from django.utils.safestring import SafeString, SafeUnicode

# Raise exceptions for database warnings if DEBUG is on
from django.conf import settings


class DatabaseFeatures(BaseDatabaseFeatures):
    empty_fetchmany_value = ()
    update_can_self_select = False
    allows_group_by_pk = True
    related_fields_match_type = True
    allow_sliced_subqueries = False
    supports_forward_references = False
    supports_long_model_names = False
    supports_microsecond_precision = False
    supports_regex_backreferencing = False
    supports_date_lookup_using_string = False
    supports_timezones = False
    requires_explicit_null_ordering_when_grouping = True
    allows_primary_key_0 = False

    def _can_introspect_foreign_keys(self):
        "Confirm support for introspected foreign keys"
        cursor = self.connection.cursor()
        cursor.execute('CREATE TABLE INTROSPECT_TEST (X INT)')
        # This command is MySQL specific; the second column
        # will tell you the default table type of the created
        # table. Since all Django's test tables will have the same
        # table type, that's enough to evaluate the feature.
        cursor.execute('SHOW TABLE STATUS WHERE Name="INTROSPECT_TEST"')
        result = cursor.fetchone()
        cursor.execute('DROP TABLE INTROSPECT_TEST')
        return result[1] != 'MyISAM'

class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django.db.backends.mysql.compiler"

    def date_extract_sql(self, lookup_type, field_name):
        # http://dev.mysql.com/doc/mysql/en/date-and-time-functions.html
        if lookup_type == 'week_day':
            # DAYOFWEEK() returns an integer, 1-7, Sunday=1.
            # Note: WEEKDAY() returns 0-6, Monday=0.
            return "DAYOFWEEK(%s)" % field_name
        else:
            return "EXTRACT(%s FROM %s)" % (lookup_type.upper(), field_name)

    def date_trunc_sql(self, lookup_type, field_name):
        fields = ['year', 'month', 'day', 'hour', 'minute', 'second']
        format = ('%%Y-', '%%m', '-%%d', ' %%H:', '%%i', ':%%s') # Use double percents to escape.
        format_def = ('0000-', '01', '-01', ' 00:', '00', ':00')
        try:
            i = fields.index(lookup_type) + 1
        except ValueError:
            sql = field_name
        else:
            format_str = ''.join([f for f in format[:i]] + [f for f in format_def[i:]])
            sql = "CAST(DATE_FORMAT(%s, '%s') AS DATETIME)" % (field_name, format_str)
        return sql

    def date_interval_sql(self, sql, connector, timedelta):
        return "(%s %s INTERVAL '%d 0:0:%d:%d' DAY_MICROSECOND)" % (sql, connector,
                timedelta.days, timedelta.seconds, timedelta.microseconds)

    def drop_foreignkey_sql(self):
        return "DROP FOREIGN KEY"

    def force_no_ordering(self):
        """
        "ORDER BY NULL" prevents MySQL from implicitly ordering by grouped
        columns. If no ordering would otherwise be applied, we don't want any
        implicit sorting going on.
        """
        return ["NULL"]

    def fulltext_search_sql(self, field_name):
        return 'MATCH (%s) AGAINST (%%s IN BOOLEAN MODE)' % field_name

    def no_limit_value(self):
        # 2**64 - 1, as recommended by the MySQL documentation
        return 18446744073709551615L

    def quote_name(self, name):
        if name.startswith("`") and name.endswith("`"):
            return name # Quoting once is enough.
        return "`%s`" % name

    def random_function_sql(self):
        return 'RAND()'

    def sql_flush(self, style, tables, sequences):
        # NB: The generated SQL below is specific to MySQL
        # 'TRUNCATE x;', 'TRUNCATE y;', 'TRUNCATE z;'... style SQL statements
        # to clear all tables of all data
        if tables:
            sql = ['SET FOREIGN_KEY_CHECKS = 0;']
            for table in tables:
                sql.append('%s %s;' % (style.SQL_KEYWORD('TRUNCATE'), style.SQL_FIELD(self.quote_name(table))))
            sql.append('SET FOREIGN_KEY_CHECKS = 1;')

            # 'ALTER TABLE table AUTO_INCREMENT = 1;'... style SQL statements
            # to reset sequence indices
            sql.extend(["%s %s %s %s %s;" % \
                (style.SQL_KEYWORD('ALTER'),
                 style.SQL_KEYWORD('TABLE'),
                 style.SQL_TABLE(self.quote_name(sequence['table'])),
                 style.SQL_KEYWORD('AUTO_INCREMENT'),
                 style.SQL_FIELD('= 1'),
                ) for sequence in sequences])
            return sql
        else:
            return []

    def value_to_db_datetime(self, value):
        if value is None:
            return None

        # MySQL doesn't support tz-aware datetimes
        if value.tzinfo is not None:
            raise ValueError("MySQL backend does not support timezone-aware datetimes.")

        # MySQL doesn't support microseconds
        return unicode(value.replace(microsecond=0))

    def value_to_db_time(self, value):
        if value is None:
            return None

        # MySQL doesn't support tz-aware datetimes
        if value.tzinfo is not None:
            raise ValueError("MySQL backend does not support timezone-aware datetimes.")

        # MySQL doesn't support microseconds
        return unicode(value.replace(microsecond=0))

    def year_lookup_bounds(self, value):
        # Again, no microseconds
        first = '%s-01-01 00:00:00'
        second = '%s-12-31 23:59:59.99'
        return [first % value, second % value]

    def max_name_length(self):
        return 64





class DatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'mysql'
    operators = {
        'exact': '= %s',
        'iexact': 'LIKE %s',
        'contains': 'LIKE BINARY %s',
        'icontains': 'LIKE %s',
        'regex': 'REGEXP BINARY %s',
        'iregex': 'REGEXP %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE BINARY %s',
        'endswith': 'LIKE BINARY %s',
        'istartswith': 'LIKE %s',
        'iendswith': 'LIKE %s',
    }

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.server_version = None
        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations()
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = DatabaseValidation(self)

        self.remote_app_id = self.settings_dict.get('REMOTE_APP_ID', appid)
        self.domain = self.settings_dict.get('DOMAIN', 'appspot.com')
        self.remote_api_path = self.settings_dict.get('REMOTE_API_PATH', None)
        self.secure_remote_api = self.settings_dict.get('SECURE_REMOTE_API', True)
        remote = self.settings_dict.get('REMOTE', False)
        if on_production_server:
            remote = False
        if remote:
            stub_manager.setup_remote_stubs(self)
        else:
            stub_manager.setup_stubs(self)


    def _valid_connection(self):
        if self.connection is not None:
            try:
                self.connection.ping()
                return True
            except DatabaseError:
                self.connection.close()
                self.connection = None
        return False

    def _cursor(self):
        
        from google.appengine.api import rdbms
        if not self._valid_connection():
            self.connection = rdbms.connect(
                                instance=self.settings_dict["INSTANCE"], 
                                database=self.settings_dict["NAME"])
            connection_created.send(sender=self.__class__, connection=self)
        cursor = self.connection.cursor()

        return cursor

    def get_server_version(self):
        return '5.1'


    def _rollback(self):
        try:
            BaseDatabaseWrapper._rollback(self)
        except Database.NotSupportedError:
            pass