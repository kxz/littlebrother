"""Tests for HTML title extraction."""


from twisted.trial.unittest import TestCase

from .. import Redirect
from ..plugins.html import extractor
from .helpers import saved_response


class HTMLTestCase(TestCase):
    def assert_title(self, filename, expected):
        finished = saved_response(filename)
        finished.addCallback(extractor.extract)
        finished.addCallback(self.assertEqual, expected)
        return finished

    def test_simple(self):
        return self.assert_title('html-simple', u'hello world')

    def test_meta_refresh(self):
        return self.assert_title('html-meta-refresh',
                                 Redirect('http://foo.test/'))

    def test_meta_refresh_long(self):
        return self.assert_title('html-meta-refresh-long', u'hello world')
