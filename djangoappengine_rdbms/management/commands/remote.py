from django.core.management import execute_from_command_line
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Runs a command with access to the remote App Engine production ' \
           'server (e.g. manage.py remote shell)'
    args = 'remotecommand'

    def run_from_argv(self, argv):
        argv = argv[:1] + argv[2:]
        execute_from_command_line(argv)
