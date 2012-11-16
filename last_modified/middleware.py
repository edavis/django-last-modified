import time
import calendar
import datetime
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed, ImproperlyConfigured
from django.http import HttpResponseNotModified
from django.utils.http import http_date, parse_http_date_safe
from django.utils.importlib import import_module
from django.views.decorators.cache import patch_cache_control

DISABLE_LAST_MODIFIED_MIDDLEWARE = getattr(settings, 'DISABLE_LAST_MODIFIED_MIDDLEWARE', False)
DISABLE_CACHE_CONTROL_MIDDLEWARE = getattr(settings, 'DISABLE_CACHE_CONTROL_MIDDLEWARE', False)
LAST_MODIFIED_FUNC               = getattr(settings, 'LAST_MODIFIED_FUNC', None)
CACHE_MAX_AGE                    = getattr(settings, 'CACHE_MAX_AGE', 3600) # one hour
CACHE_SHARED_MAX_AGE             = getattr(settings, 'CACHE_SHARED_MAX_AGE', CACHE_MAX_AGE)

class CacheControlMiddleware(object):
    def __init__(self):
        if DISABLE_CACHE_CONTROL_MIDDLEWARE:
            raise MiddlewareNotUsed

    def process_response(self, request, response):
        """
        Add 'Cache-Control' and 'Expires' HTTP headers to responses.

        CACHE_MAX_AGE tells the user's browser how many seconds it can
        serve the cached representation without having to check with the
        origin server.

        CACHE_SHARED_MAX_AGE is the same as CACHE_MAX_AGE, but it applies
        to public caches.

        The 'Expires' HTTP header is added for completeness, though
        'Cache-Control' has been adopted pretty much everywhere and is the
        HTTP/1.1 standard.
        """
        params = dict(
            max_age = CACHE_MAX_AGE,
            s_maxage = CACHE_SHARED_MAX_AGE,
        )
        patch_cache_control(response, **params)
        response['Expires'] = http_date(time.time() + CACHE_MAX_AGE)
        return response

class BaseModifiedMiddleware(object):
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

class IfModifiedSinceMiddleware(BaseModifiedMiddleware):
    """
    Middleware for checking the 'If-Modified-Since' header.
    """
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

        if if_modified_since is not None:
            if_modified_since = parse_http_date_safe(if_modified_since)

        if if_modified_since is not None:
            if self.last_modified <= if_modified_since:
                return HttpResponseNotModified()

class LastModifiedMiddleware(BaseModifiedMiddleware):
    """
    Middleware for setting the 'Last-Modified' header.
    """
    def process_response(self, request, response):
        response['Last-Modified'] = http_date(self.last_modified)
        return response
