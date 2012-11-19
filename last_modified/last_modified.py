import hashlib
import calendar
import datetime
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed, ImproperlyConfigured
from django.http import HttpResponseNotModified
from django.utils.http import http_date, parse_http_date_safe
from django.utils.importlib import import_module
from django.views.decorators.cache import patch_cache_control

DISABLE_LAST_MODIFIED_MIDDLEWARE = getattr(settings, 'DISABLE_LAST_MODIFIED_MIDDLEWARE', False)
LAST_MODIFIED_FUNC               = getattr(settings, 'LAST_MODIFIED_FUNC', None)

class LastModifiedMiddleware(object):
    def __init__(self):
        if DISABLE_LAST_MODIFIED_MIDDLEWARE:
            raise MiddlewareNotUsed

        self.last_modified_func = self.get_last_modified_func()

    def get_last_modified_func(self):
        """
        Return the function object defined by LAST_MODIFIED_FUNC.
        """
        path = LAST_MODIFIED_FUNC

        if path is None:
            raise ImproperlyConfigured("LAST_MODIFIED_FUNC has not been set.")

        i = path.rfind('.')
        module, attr = path[:i], path[i+1:]
        try:
            mod = import_module(module)
        except ImportError as e:
            raise ImproperlyConfigured('Error importing LAST_MODIFIED_FUNC %s: "%s"' % (module, e))
        try:
            func = getattr(mod, attr)
        except AttributeError as e:
            raise ImproperlyConfigured('Module "%s" does not define a "%s" function' % (module, attr))

        return func

    def _convert_to_timestamp(self, value):
        """
        Convert value to UNIX timestamp.
        """
        if isinstance(value, datetime.date):
            return calendar.timegm(value.utctimetuple())
        else:
            return int(value)

    @property
    def last_modified(self):
        value = self.last_modified_func()
        return self._convert_to_timestamp(value)

    @property
    def etag(self):
        value = http_date(self.last_modified)
        return '"%s"' % hashlib.md5(value).hexdigest()

    def _skip_cache_check(self, request):
        """
        Return True if we should skip the If-Modified-Since or
        If-None-Match checking.
        """
        # If a user is logged in, don't do If-Modified-Since or
        # If-None-Match checking.
        try:
            if request.user.is_authenticated():
                return True
        except AttributeError:
            pass

    def _if_modified_since(self, value):
        value = parse_http_date_safe(value)
        return self.last_modified <= value

    def _if_none_match(self, value):
        return value == self.etag

    ###########################################################################
    def process_request(self, request):
        """
        Perform If-Modified-Since and If-None-Match checking.
        """
        if self._skip_cache_check(request):
            return # bail here and continue on

        last_modified = request.META.get('HTTP_IF_MODIFIED_SINCE')
        etag = request.META.get('HTTP_IF_NONE_MATCH')

        if any([self._if_modified_since(last_modified),
                self._if_none_match(etag)]):
            return HttpResponseNotModified()

    def process_response(self, request, response):
        response['Last-Modified'] = http_date(self.last_modified)
        response['ETag'] = self.etag
        return response
