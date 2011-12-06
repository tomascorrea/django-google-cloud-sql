from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from optparse import make_option

class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', default=None, help='Specifies the username for the superuser.'),
        make_option('--password', dest='password', default=None, help='Specifies the email address for the superuser.'),
        )

    help = "Change a user's password for django.contrib.auth."

    requires_model_validation = False


    def handle(self, *args, **options):
        
        try:
            u = User.objects.get(username=options['username'])
        except User.DoesNotExist:
            raise CommandError("user '%s' does not exist" % options['username'])

        print "Changing password for user '%s'" % u.username

        

        u.set_password(options['password'])
        u.save()

        return "Password changed successfully for user '%s'" % u.username
