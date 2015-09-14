"""Title extractor for image files using Pillow."""


from __future__ import division
from io import BytesIO

from PIL import Image
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.iweb import UNKNOWN_LENGTH
from zope.interface import implements

from .. import ITitleExtractor, read_body
from ..humanize import duration, filesize


class ImageTitleExtractor(object):
    implements(ITitleExtractor)
    content_types = ('image/png', 'image/gif', 'image/jpeg')

    def __init__(self):
        #: The maximum number of bytes this extractor will download.
        self.max_download_bytes = 65536

    @inlineCallbacks
    def extract(self, response):
        truncated = (response.length is UNKNOWN_LENGTH or
                     response.length > self.max_download_bytes)
        content = yield read_body(response, max_bytes=self.max_download_bytes)
        try:
            image = Image.open(BytesIO(content))
        except IOError:
            # The image content is invalid.  It might be our fault for
            # truncating the image too early.  Who knows?
            returnValue(None)
        image_type = 'image'
        image_duration = u''
        try:
            if getattr(image, 'is_animated', False):
                image_type = 'animation'
                if not truncated:
                    # Assume a GIF animation.
                    frame_duration = image.info.get('duration') / 1000
                    if frame_duration is not None:
                        image_duration = u', {}'.format(
                            duration(image.n_frames * frame_duration))
        except IOError:
            # Couldn't seek because of truncated image.
            pass
        returnValue(u'{} {} ({:n} \u00d7 {:n} pixels{}{})'.format(
            image.format, image_type,
            image.width, image.height, image_duration,
            (u'' if response.length is UNKNOWN_LENGTH
                 else u', ' + filesize(response.length))))


extractor = ImageTitleExtractor()
