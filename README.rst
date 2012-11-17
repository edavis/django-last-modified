django-last-modified
====================

django-last-modified is a collection of Django middleware to add
freshness and validation caching headers.

Summary
-------

``last_modified.middleware.CacheControlMiddleware`` adds
``Cache-Control`` and ``Expires`` HTTP headers to outgoing
responses. These headers tell private (e.g., browser) and public
(e.g., ISP) caches how long to consider their stored representations
as "fresh."

``last_modified.middleware.LastModifiedMiddleware`` sets
``Last-Modified`` and checks ``If-Modified-Since`` HTTP headers. These
headers save bandwidth by only transferring data when content on your
site has changed.

Installation
------------

1) ``$ pip install django-last-modified``

2) Add ``CacheControlMiddleware`` and ``LastModifiedMiddleware``
   (located in ``last_modified.middleware``) to ``MIDDLEWARE_CLASSES`` as
   appropriate.

Settings
--------

LAST_MODIFIED_FUNC
  String path to a function (e.g., ``path.to.module.function``) that
  is called to obtain the "last modified" value. Must return either a
  ``datetime``/``date`` object or a UNIX timestamp. *Default:* ``None``,
  must be defined.

CACHE_MAX_AGE
  Number of seconds stored representation is considered fresh for
  private caches. *Default:* 3600 seconds (one hour).

CACHE_SHARED_MAX_AGE
  Same as CACHE_MAX_AGE but for public caches. *Default:* Value of
  CACHE_MAX_AGE.

DISABLE_CACHE_CONTROL_MIDDLEWARE, DISABLE_LAST_MODIFIED_MIDDLEWARE
  Set to ``True`` to disable the respective middleware. Provided so
  you can toggle middleware off/on without having to tweak
  ``MIDDLEWARE_CLASSES``. *Default:* False.
