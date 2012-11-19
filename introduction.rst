Introduction to HTTP caching
============================

Initial request
---------------

Let's start with a simple request to your site after installing and
configuring django-last-modified::

    $ http -t example.com
    HTTP/1.1 200 OK
    Cache-Control: s-maxage=3600, max-age=3600
    Date: Sat, 17 Nov 2012 17:47:17 GMT
    ETag: "7caa2f5cdd0224d87e16137558ab871e"
    Expires: Sat, 17 Nov 2012 18:47:17 GMT
    Last-Modified: Fri, 16 Nov 2012 18:04:43 GMT

(Note: ``http`` comes from the `httpie
<http://pypi.python.org/pypi/httpie>`_ package.)

The first time a user -- let's call him Bob -- connects to your site,
django-last-modified adds four HTTP headers to his response:

- Cache-Control
- Expires
- Last-Modified
- ETag

The **Cache-Control** header tells Bob's browser cache how long to
consider its stored copy "fresh." In other words, how long to keep
serving the cached copy before it has to check with your server for a
newer copy. The **Expires** header contains the same information
("store for one hour") but formats it as a date to comply with old
caches that don't understand Cache-Control.

With Cache-Control and Expires set to one hour, that's how long Bob's
browser cache will keep serving him its stored copy without talking to
your server.

But what happens once that hour is up? This is where the
Last-Modified and ETag headers come in.

Validating the cached copy
--------------------------

Say it's been two hours and Bob wants to check out your site
again. Bob's browser knows it can't keep serving its cached copy -- it
could only do that for one hour -- so it has to check with your server
before doing anything. But this time, the request includes a special
header -- **If-Modified-Since** -- set to the value of **Last-Modified**
as returned during the very first request::

    $ http -t example.com If-Modified-Since:"Fri, 16 Nov 2012 18:04:43 GMT"
    HTTP/1.1 304 NOT MODIFIED
    Cache-Control: s-maxage=3600, max-age=3600
    Content-Length: 0
    Date: Sat, 17 Nov 2012 19:47:17 GMT
    ETag: "7caa2f5cdd0224d87e16137558ab871e"
    Expires: Sat, 17 Nov 2012 20:47:17 GMT
    Last-Modified: Fri, 16 Nov 2012 18:04:43 GMT

By including the If-Modified-Since header, Bob's browser is asking
your server, "Has there been any updates since we last talked?"

If there haven't been any updates, your server responds with "304 NOT
MODIFIED." This tells Bob's browser, "Nope, nothing new. Keep using
that cached copy but check back again in an hour." The nice thing
about this is it saves CPU cycles and bandwidth as no page is
generated or even transmitted.

How does django-last-modified know what to return for the
Last-Modified value? It uses the datetime/date object returned from
the function defined in LAST_MODIFIED_FUNC. So, for example, if your
site is a blog you could return the timestamp of your latest blog
post::

    # post/utils.py
    from post.models import Post
    def latest_timestamp():
        return Post.objects.latest('pub_date').pub_date

    # settings.py
    LAST_MODIFIED_FUNC = 'post.utils.latest_timestamp'

ETags
-----

So what are ETags?

An **ETag** is any value that changes when the content changes. In
django-last-modified, ETags are computed as the MD5 hexdigest of the
Last-Modified value.

ETags work the exact same as Last-Modified/If-Modified-Since except
the request header is called **If-None-Match**. If the ETag has
changed (i.e., there's a new value returned from LAST_MODIFIED_FUNC)
it will return fresh content along with the new ETag.

But why include ETags if Last-Modified/If-Modified-Since accomplish
the same thing? Well, it's been my experience that different browsers
send different request headers. By including both Last-Modified and
ETag and checking If-Modified-Since and If-None-Match, all your bases
are covered no matter what you get sent.

New content
-----------

But let's say there was some new content. In that case, it would go
something like this::

    $ http -t example.com If-Modified-Since:"Fri, 16 Nov 2012 18:04:43 GMT"
    HTTP/1.1 200 OK
    Cache-Control: s-maxage=3600, max-age=3600
    Date: Sat, 17 Nov 2012 19:47:17 GMT
    ETag: "d16fdf66ec8b71fbae2ff7be17a691bd"
    Expires: Sat, 17 Nov 2012 20:47:17 GMT
    Last-Modified: Sat, 17 Nov 2012 17:50:00 GMT

With this, your server is saying, "Yeah, there has been new
content. Get rid of that old cached copy and use this."

From here, the cycle would repeat. Bob's browser cache would use this
new copy for the next hour and once that hour is up checks with your
server.
