from django.core.management import find_management_module, find_commands, load_command_class
from django.core.management.base import handle_default_options
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponsePermanentRedirect, HttpResponseRedirect

from django.template import Context, loader, RequestContext
from forms import CommandArgsForm
import StringIO
from management.decorators import redirect_stderr_stdout
import sys
from utils import on_production_server
from django.http import Http404
from django.core.urlresolvers import reverse
from django.utils.functional import wraps

# Some commands need to be excludes beacause I can not implement those or does no make sense like run server
EXCLUDED_COMMANDS = ['runserver','deploy','remote','dbshell','startapp','startproject','compilemessages','runfcgi','shell','makemessages']

OVERWRITE_COMMANDS = ['django.contrib.auth:changepassword',]


def only_admin(view):

    @wraps(view)
    def inner(*args, **kwargs):
        if on_production_server:
            from google.appengine.api import users
            if not users.get_current_user():
                return HttpResponseRedirect(users.create_login_url(reverse("commands")))
            else:
                if users.is_current_user_admin():
                    return view(*args, **kwargs)
                
            raise Http404("User is not admin")
        else:
            return view(*args, **kwargs)

    return inner


@only_admin
def commands(request):


    template = loader.get_template('djangoappengine_rdbms/commands.html')

    _commands = {}
    #import debugger; debugger.pdb().set_trace()
    for app_name in settings.INSTALLED_APPS + ["django.core"]:
        try:
            command_names = find_commands(find_management_module(app_name))
            for command_name in command_names:
                if command_name not in EXCLUDED_COMMANDS:
                    if "%s:%s" % (app_name, command_name) not in OVERWRITE_COMMANDS:
                        _commands[command_name] = {'command_name':command_name,'app_name':app_name}
        except ImportError:
            pass

    #import debugger; debugger.pdb().set_trace()
    
    _commands = _commands.values()
    _commands.sort(key=lambda x: x['command_name'])
    context = {'commands':_commands}
    return HttpResponse(template.render(RequestContext(request,context)))

            
@only_admin
def command_details(request, app_name, command_name):

    command = load_command_class(app_name, command_name)
    template = loader.get_template('djangoappengine_rdbms/command_details.html')
    #
    
    stdout = StringIO.StringIO()
    stderr = StringIO.StringIO()
    



    @redirect_stderr_stdout(stdout=stdout,stderr=stderr)            
    def _execute_command(command, command_name, stdout, stderr, argv):

        parser = command.create_parser("manage.py", command_name)
        options, argss = parser.parse_args(argv.split())
        handle_default_options(options)
        options.__dict__["stdout"] = stdout
        options.__dict__["stderr"] = stderr
        options.__dict__['interactive'] = False
        #import debugger; debugger.pdb().set_trace()
        try:
            return command.execute(*argss, **options.__dict__)
        except SystemExit, e:
            pass
        except Exception, e:
            stderr.write(e)




    if request.POST:
        form = CommandArgsForm(request.POST, command=command)
        if form.is_valid():
            ret = _execute_command(command, command_name, stdout=stdout, stderr=stderr, argv = form.cleaned_data.get("args"))

    else:
        form = CommandArgsForm(command=command)

    stdout.seek(0)
    stderr.seek(0)
    #import debugger; debugger.pdb().set_trace()
    context = { 'command':command,
                'command_name':command_name, 
                'app_name':app_name,
                'form':form,
                'stdout':stdout.read(),
                'stderr':stderr.read(),
                }
    return HttpResponse(template.render(RequestContext(request,context)))