"""Tests for human-readable data presentations."""


from twisted.trial.unittest import TestCase

from ..humanize import duration, filesize


class DurationTestCase(TestCase):
    def test_instant(self):
        self.assertEqual(duration(0), 'less than 1 sec')
        self.assertEqual(duration(0.5), 'less than 1 sec')

    def test_seconds(self):
        self.assertEqual(duration(1), '1 sec')
        self.assertEqual(duration(59), '59 sec')

    def test_minutes(self):
        self.assertEqual(duration(60), '1 min')
        self.assertEqual(duration(61), '1 min 1 sec')
        self.assertEqual(duration(1800), '30 min')
        self.assertEqual(duration(3599), '59 min 59 sec')

    def test_hours(self):
        self.assertEqual(duration(3600), '1 hr')
        self.assertEqual(duration(3601), '1 hr 1 sec')
        self.assertEqual(duration(3660), '1 hr 1 min')
        self.assertEqual(duration(3661), '1 hr 1 min 1 sec')
        self.assertEqual(duration(7777), '2 hr 9 min 37 sec')


class FileSizeTestCase(TestCase):
    def test_unprefixed(self):
        self.assertEqual(filesize(1), '1 B')

    def test_prefixed(self):
        self.assertEqual(filesize(1000), '1 KB')
        self.assertEqual(filesize(1024), '1.02 KB')
        self.assertEqual(filesize(1000000), '1 MB')
        self.assertEqual(filesize(2097152), '2.1 MB')
        self.assertEqual(filesize(1000000000), '1 GB')
        self.assertEqual(filesize(5555555555), '5.56 GB')
        self.assertEqual(filesize(999999999999), '1 TB')
        self.assertEqual(filesize(1000000000000), '1 TB')
        self.assertEqual(filesize(1000000000000000), '1 EB')
        self.assertEqual(filesize(1000000000000000000), '1 PB')
        self.assertEqual(filesize(1000000000000000128), '1 PB')
        self.assertEqual(filesize(1000000000000000000000), '1 ZB')
        self.assertEqual(filesize(1000000000000000000000000), '1 YB')
