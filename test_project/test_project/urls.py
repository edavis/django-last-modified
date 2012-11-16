from django.conf.urls import patterns, include, url
from django.http import HttpResponse

def test_view(request):
    return HttpResponse('hello world')

urlpatterns = patterns(
    '',
    url(r'^test/$', test_view),
)
