django-last-modified
====================

.. image:: https://secure.travis-ci.org/edavis/django-last-modified.png
   :target: https://travis-ci.org/edavis/django-last-modified

django-last-modified is a collection of Django middleware to help
manage your caching setup.

If you're familiar with the following HTTP headers:

- Cache-Control
- Expires
- Last-Modified
- ETag
- If-Modified-Since
- If-None-Match

You can probably skip down to "Installation."

Otherwise, you can find a primer on HTTP caching located in
"introduction.rst" in this repository.

Installation
------------

1) ``$ pip install django-last-modified``

2) Add ``CacheControlMiddleware`` and ``LastModifiedMiddleware`` to
   MIDDLEWARE_CLASSES.

``CacheControlMiddleware`` adds the Cache-Control and Expires headers
to outgoing responses while ``LastModifiedMiddleware`` adds the
Last-Modified/ETag header and performs the
If-Modified-Since/If-None-Match checking.

Here's a recommended MIDDLEWARE_CLASSES order::

    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'last_modified.middleware.LastModifiedMiddleware',
        'last_modified.middleware.CacheControlMiddleware',
        # ... snip ...
    )

If a request is authenticated (i.e., the user has logged in) the
If-Modified-Since checking is skipped.

django-last-modified doesn't need to be added to INSTALLED_APPS.

Configuration
-------------

LAST_MODIFIED_FUNC
  String path to a function (e.g., 'path.to.module.function') that
  is called to obtain the "last modified" value. Must return either a
  datetime/date object or a UNIX timestamp. *Default:* None, must be
  defined.

CACHE_MAX_AGE
  Number of seconds stored representation is considered fresh for
  private caches. *Default:* 3600 seconds (one hour).

CACHE_SHARED_MAX_AGE
  Same as CACHE_MAX_AGE but for public caches. *Default:* Value of
  CACHE_MAX_AGE.

DISABLE_CACHE_CONTROL_MIDDLEWARE, DISABLE_LAST_MODIFIED_MIDDLEWARE
  Set to True to disable the respective middleware from being
  applied. Provided so you can toggle middleware off/on without having
  to tweak MIDDLEWARE_CLASSES. *Default:* False.

Doesn't Django already have this?
---------------------------------

Django has two features *like* this, but they're slightly different.

The `update and fetch
<https://docs.djangoproject.com/en/1.4/topics/cache/#the-per-site-cache>`_
cache middleware sets the Cache-Control, Expires, and Last-Modified
headers but in the process also stores the generated pages in the
server-side cache. The project I was working on had many thousand
"long-tail" pages that I didn't want/need polluting any caches.

There's also "`conditional view processing
<https://docs.djangoproject.com/en/1.4/topics/conditional-view-processing/>`_"
which is even closer to what I needed, but can only be applied on a
per-view basis while I needed the whole site covered.

In a nutshell, I wanted the whole site covered (like the cache
middleware does) but only generating HTTP headers and not involving
the server-side cache (like the conditional view processing).

Unable to find an existing app to do this, django-last-modified was
born.

LICENSE
-------

MIT
