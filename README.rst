django-last-modified
====================

django-last-modified is a collection of Django middleware to add
freshness and validation caching headers.

``last_modified.middleware.CacheControlMiddleware`` adds
``Cache-Control`` and ``Expires`` HTTP headers to outgoing
responses. These headers tell private (e.g., browser) and public
(e.g., ISP) caches how long to consider their stored representations
as "fresh."

``last_modified.middleware.LastModifiedMiddleware`` sets
``Last-Modified`` and checks ``If-Modified-Since`` HTTP headers. These
headers save bandwidth by only transferring data when content on your
site has changed.
