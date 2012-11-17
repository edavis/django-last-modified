django-last-modified enables you to do this::

    $ http -t example.com
    HTTP/1.1 200 OK
    Date: Sat, 17 Nov 2012 17:47:17 GMT
    Cache-Control: s-maxage=3600, max-age=3600
    Expires: Sat, 17 Nov 2012 18:47:17 GMT
    Last-Modified: Fri, 16 Nov 2012 18:04:43 GMT

The first time a user -- let's call him Bob -- connects to your site,
django-last-modified adds three HTTP headers to his response:
Cache-Control, Expires, and Last-Modified.

The Cache-Control header tells Bob's browser cache how long to
consider its stored copy "fresh." In other words, how long to keep
serving the cached copy before it has to check with your server for
a newer copy.

The Expires header is just another way of expressing the Cache-Control
information. It's included for completeness even though Cache-Control
has largely superceded it.

With Cache-Control and Expires set to one hour, that's how long Bob's
browser cache will keep serving him its stored copy without talking to
your server.

But what happens once that hour is up? This is where the Last-Modified
header comes in.

Say it's been two hours and Bob wants to check out your site
again. Bob's browser knows it can't keep serving its cached copy -- it
could only do that for an hour -- so it has to check with your server
before doing anything. But this time, it includes a special header --
If-Modified-Since -- set to the value of Last-Modified as returned
during the very first request::

    $ http -t example.com If-Modified-Since:"Fri, 16 Nov 2012 18:04:43 GMT"
    HTTP/1.1 304 NOT MODIFIED
    Date: Sat, 17 Nov 2012 19:47:17 GMT
    Last-Modified: Fri, 16 Nov 2012 18:04:43 GMT
    Content-Length: 0
    Date: Sat, 17 Nov 2012 20:47:17 GMT
    Cache-Control: s-maxage=3600, max-age=3600

By including the If-Modified-Since header, Bob's browser is asking
your server, "Has there been any updates since we last talked?"

If there haven't been any updates, your server responds with "304 NOT
MODIFIED." This tells Bob's browser, "Nope, nothing new. Keep using
that cached copy but check back again in an hour." The nice thing
about this is it saves CPU cycles and bandwidth as no page is
generated or even transmitted.

But let's say there was some new content. In that case, it would go
something like this::

    $ http -t example.com If-Modified-Since:"Fri, 16 Nov 2012 18:04:43 GMT"
    HTTP/1.1 200 OK
    Date: Sat, 17 Nov 2012 19:47:17 GMT
    Last-Modified: Sat, 17 Nov 2012 17:30:00 GMT
    Date: Sat, 17 Nov 2012 20:47:17 GMT
    Cache-Control: s-maxage=3600, max-age=3600

With this, your server is saying, "Yeah, there has been new
content. Get rid of that old cached copy and use this."

From here, the cycle would repeat. Bob's browser cache would use this
new copy for the next hour and once that hour is up checks with your
server.
