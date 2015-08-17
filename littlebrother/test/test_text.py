"""Tests for plain text title extraction."""


from twisted.trial.unittest import TestCase

from ..plugins.text import extractor
from .helpers import CassetteTestMixin


class PlainTextTestCase(CassetteTestMixin, TestCase):
    extractor = extractor

    def test_simple(self):
        return self.assert_title('text/simple', u'hello world')

    def test_bad_encoding(self):
        return self.assert_title('text/bad-encoding', u'hello world')
