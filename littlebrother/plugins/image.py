"""Title extractor for image files using Pillow."""


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from PIL import Image
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.iweb import UNKNOWN_LENGTH
from zope.interface import implements

from .. import ITitleExtractor, read_body
from ..humanize import filesize


class ImageTitleExtractor(object):
    implements(ITitleExtractor)
    content_types = ('image/png', 'image/gif', 'image/jpeg')

    def __init__(self):
        #: The maximum number of bytes this extractor will download.
        self.max_download_bytes = 65536

    @inlineCallbacks
    def extract(self, response):
        content = yield read_body(response, max_bytes=self.max_download_bytes)
        try:
            pbuffer = Image.open(StringIO(content))
        except IOError:
            # The image content is invalid.  It might be our fault for
            # truncating the image too early.  Who knows?
            returnValue(None)
        width, height = pbuffer.size
        format = pbuffer.format
        returnValue(u'{} image ({:n} \u00d7 {:n} pixels{})'.format(
            format, width, height,
            (u'' if response.length is UNKNOWN_LENGTH
                 else u', ' + filesize(response.length))))


extractor = ImageTitleExtractor()
