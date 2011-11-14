from django.conf import settings
from django.core.management import call_command
from django.test.testcases import TestCase as BaseTestCasea
from django.db.models import loading

class TestCase(TestCase):
    '''
    Adds apps specified in `self.apps` to `INSTALLED_APPS` and
    performs a `syncdb` at runtime.
    '''

    apps = ()
    _source_installed_apps = ()

    def _pre_setup(self):
        super(AppTestCase, self)._pre_setup()

        if self.apps:
            self._source_installed_apps = settings.INSTALLED_APPS
            settings.INSTALLED_APPS = settings.INSTALLED_APPS + self.apps
            loading.cache.loaded = False
            call_command('syncdb', verbosity=0)

    def _post_teardown(self):
        super(AppTestCase, self)._post_teardown()

        if self._source_installed_apps:
            settings.INSTALLED_APPS = self._source_installed_apps
            self._source_installed_apps = ()
            loading.cache.loaded = False