# _*_ coding: utf-8 _*_

from django.conf import settings
from django.conf.urls.defaults import *

from views import commands, command_details

urlpatterns = patterns('',
   url(r'^command/$', commands, name="commands"),
   url(r'^command/(?P<app_name>[\w\.]+)/(?P<command_name>\w+)/$', command_details, name="command_details"),
   )