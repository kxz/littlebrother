"""Tests for plain text title extraction."""


from twisted.trial.unittest import TestCase

from ..plugins.text import extractor
from .helpers import saved_response


class PlainTextTestCase(TestCase):
    def assert_title(self, filename, expected):
        finished = saved_response(filename)
        finished.addCallback(extractor.extract)
        finished.addCallback(self.assertEqual, expected)
        return finished

    def test_simple(self):
        return self.assert_title('text-simple', u'hello world')

    def test_bad_encoding(self):
        return self.assert_title('text-bad-encoding', u'hello world')
