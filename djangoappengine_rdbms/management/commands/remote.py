from django.core.management import execute_from_command_line
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Runs a command with access to the remote App Engine production ' \
           'server (e.g. manage.py remote shell)'
    args = 'remotecommand'

    def run_from_argv(self, argv):
        import pdb; pdb.set_trace()
        from django.db import connections
        from ...db.backend.base import DatabaseWrapper
        from ...db.backend.stubs import stub_manager
        for connection in connections.all():
            if isinstance(connection, DatabaseWrapper):
                stub_manager.setup_remote_stubs(connection)
                break
        argv = argv[:1] + argv[2:]
        
        execute_from_command_line(argv)
