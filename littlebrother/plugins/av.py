"""Title extractor for media files using PyAV."""


from __future__ import absolute_import, division
import os
import tempfile

import av
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.iweb import UNKNOWN_LENGTH
from zope.interface import implements

from .. import ITitleExtractor, read_body
from ..humanize import duration, filesize


class AVTitleExtractor(object):
    implements(ITitleExtractor)
    content_types = ('audio/mpeg', 'video/mp4',
                     'video/webm', 'video/x-matroska')

    def __init__(self):
        #: The maximum number of bytes this extractor will download.
        self.max_download_bytes = 4194304

    @inlineCallbacks
    def extract(self, response):
        with tempfile.NamedTemporaryFile() as f:
            content = yield read_body(response,
                                      max_bytes=self.max_download_bytes)
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
            try:
                container = av.open(f.name)
            except av.AVError:
                returnValue(None)
            returnValue(u'{} file containing {} ({}{})'.format(
                container.format.long_name,
                u' and '.join([s.long_name + ' ' + s.type
                               for s in container.streams]),
                duration(container.duration / av.time_base),
                (u'' if response.length is UNKNOWN_LENGTH
                     else u', ' + filesize(response.length))))


extractor = AVTitleExtractor()
