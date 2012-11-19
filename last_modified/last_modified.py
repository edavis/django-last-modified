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

    ###########################################################################
    def process_request(self, request):
        """
        Compare 'If-Modified-Since' to the last modified time.

        The goal of this is to quickly return HttpResponseNotModified
        if the value in 'If-Modified-Since' is greater than or equal
        to the last modified datetime.
        """
        # request.user only exists when auth middleware is active. If
        # we can't find request.user, everyone is non-authenticated.
        try:
            # If request comes from an authenticated user, skip the rest
            if request.user.is_authenticated():
                return
        except AttributeError:
            pass

        if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE')
        if_none_match = request.META.get('HTTP_IF_NONE_MATCH')

        if if_modified_since is not None:
            if_modified_since = parse_http_date_safe(if_modified_since)

        if if_modified_since is not None:
            if self.last_modified <= if_modified_since:
                return HttpResponseNotModified()

        if if_none_match is not None:
            if if_none_match == self.etag:
                return HttpResponseNotModified()

    def process_response(self, request, response):
        response['Last-Modified'] = http_date(self.last_modified)
        response['ETag'] = self.etag
        return response
