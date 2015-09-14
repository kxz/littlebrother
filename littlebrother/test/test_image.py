"""Tests for title extraction with Pillow."""


from twisted.trial.unittest import TestCase

from .. import Redirect
from ..plugins.image import extractor
from .helpers import CassetteTestMixin


class ImageTestCase(CassetteTestMixin, TestCase):
    extractor = extractor

    def test_gif(self):
        return self.assert_title(
            'image/gif',
            u'GIF image (70 \u00d7 46 pixels, 4.08 KB)')

    def test_gif_animated(self):
        return self.assert_title(
            'image/gif-animated',
            u'GIF animation (80 \u00d7 60 pixels, 5 sec, 41.3 KB)')

    def test_gif_animated_truncated(self):
        return self.assert_title(
            'image/gif-animated-truncated',
            u'GIF animation (640 \u00d7 480 pixels, 939 KB)')

    def test_gif_animated_truncated_first_frame(self):
        return self.assert_title(
            'image/gif-animated-truncated-first-frame',
            u'GIF image (1920 \u00d7 1080 pixels, 5.89 MB)')

    def test_png(self):
        return self.assert_title(
            'image/png',
            u'PNG image (70 \u00d7 46 pixels, 6.97 KB)')
