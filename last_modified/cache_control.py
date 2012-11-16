import time
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.http import http_date
from django.views.decorators.cache import patch_cache_control

DISABLE_CACHE_CONTROL_MIDDLEWARE = getattr(settings, 'DISABLE_CACHE_CONTROL_MIDDLEWARE', False)
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
