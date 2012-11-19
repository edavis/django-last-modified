import re
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings

CACHE_CONTROL_MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'last_modified.middleware.CacheControlMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

LAST_MODIFIED_MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',

    # session and auth before LastModifiedMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'last_modified.middleware.LastModifiedMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

@override_settings(MIDDLEWARE_CLASSES=CACHE_CONTROL_MIDDLEWARE_CLASSES)
class TestCacheControlMiddleware(TestCase):
    @override_settings(
        CACHE_MAX_AGE=100,
        CACHE_SHARED_MAX_AGE=150,
    )
    def test_cache_control_header_exists(self):
        response = self.client.get('/test/')
        self.assertTrue('Cache-Control' in response)

        cc = response['Cache-Control']
        self.assertTrue(re.search('s-maxage=%d' % settings.CACHE_SHARED_MAX_AGE, cc))
        self.assertTrue(re.search('max-age=%d' % settings.CACHE_MAX_AGE, cc))

    def test_expires_header_exists(self):
        response = self.client.get('/test/')
        self.assertTrue('Expires' in response)

@override_settings(MIDDLEWARE_CLASSES=LAST_MODIFIED_MIDDLEWARE_CLASSES)
class TestLastModifiedMiddleware(TestCase):
    def test_last_modified(self):
        response = self.client.get('/test/')
        self.assertEqual(response['Last-Modified'], 'Wed, 15 Feb 1989 15:30:34 GMT')

    def test_last_modified_with_auth(self):
        """
        If a user is logged in, don't return 'NOT MODIFIED.'
        """
        from django.contrib.auth.models import User
        User.objects.create_user('eric', 'ed@npri.org', 'foo')
        self.client.login(username='eric', password='foo')

        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/test/', HTTP_IF_MODIFIED_SINCE='Wed, 15 Feb 1989 15:30:34 GMT')
        self.assertEqual(response.status_code, 200)

    def test_if_modified_since(self):
        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/test/', HTTP_IF_MODIFIED_SINCE='Wed, 15 Feb 1989 15:30:34 GMT')
        self.assertEqual(response.status_code, 304)

        # one hour prior to what LAST_MODIFIED_FUNC returns
        response = self.client.get('/test/', HTTP_IF_MODIFIED_SINCE='Wed, 15 Feb 1989 14:30:34 GMT')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Last-Modified'], 'Wed, 15 Feb 1989 15:30:34 GMT')

@override_settings(MIDDLEWARE_CLASSES=LAST_MODIFIED_MIDDLEWARE_CLASSES)
class TestEtagMiddleware(TestCase):
    def setUp(self):
        # self.etag = hashlib.md5('Wed, 15 Feb 1989 15:30:34 GMT').hexdigest()
        self.etag = '"70c57237a51e9c6a572e8b2814c774e0"'

    def test_etag(self):
        response = self.client.get('/test/')
        self.assertEqual(response['ETag'], self.etag)

    def test_etag_if_none_match(self):
        # Correct ETag produces '304 NOT MODIFIED'
        response = self.client.get('/test/', HTTP_IF_NONE_MATCH=self.etag)
        self.assertEqual(response.status_code, 304)

        # Incorrect ETag produces '200 OK' and includes correct ETag
        response = self.client.get('/test/', HTTP_IF_NONE_MATCH='"foo"')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['ETag'], self.etag)

    def test_etag_with_auth(self):
        """
        If a user is logged in, don't return 'NOT MODIFIED.'
        """
        from django.contrib.auth.models import User
        User.objects.create_user('eric', 'ed@npri.org', 'foo')
        self.client.login(username='eric', password='foo')

        response = self.client.get('/test/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/test/', HTTP_IF_NONE_MATCH=self.etag)
        self.assertEqual(response.status_code, 200)
