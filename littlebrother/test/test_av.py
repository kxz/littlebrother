"""Tests for title extraction with PyAV."""


from twisted.trial.unittest import TestCase

from .. import Redirect
from ..plugins.av import extractor
from .helpers import CassetteTestMixin


class AVTestCase(CassetteTestMixin, TestCase):
    extractor = extractor

    def test_mp3(self):
        return self.assert_title(
            'av/mp3',
            u'MP2/3 (MPEG audio layer 2/3) file containing MP3 (MPEG '
            u'audio layer 3) audio (5 sec, 40.6 KB)')

    def test_mp4_audio(self):
        return self.assert_title(
            'av/mp4-audio',
            u'QuickTime / MOV file containing H.264 / AVC / MPEG-4 AVC '
            u'/ MPEG-4 part 10 video and AAC (Advanced Audio Coding) '
            u'audio (5 sec, 115 KB)')

    def test_mp4_no_audio(self):
        return self.assert_title(
            'av/mp4-no-audio',
            u'QuickTime / MOV file containing H.264 / AVC / MPEG-4 AVC '
            u'/ MPEG-4 part 10 video (5 sec, 31.4 KB)')

    def test_webm_audio(self):
        return self.assert_title(
            'av/webm-audio',
            u'Matroska / WebM file containing On2 VP8 video and Vorbis '
            u'audio (5 sec, 121 KB)')

    def test_webm_no_audio(self):
        return self.assert_title(
            'av/webm-no-audio',
            u'Matroska / WebM file containing On2 VP8 video (5 sec, '
            u'116 KB)')
