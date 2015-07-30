"""Title extractor for plain text files."""


import cgi

from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from .. import ITitleExtractor, read_body


class PlainTextTitleExtractor(object):
    implements(ITitleExtractor)
    content_types = ('text/plain',)

    def __init__(self):
        #: The default text encoding if none is sent by the server.
        self.default_encoding = 'utf-8'
        #: The maximum number of bytes this extractor will download.
        self.max_download_bytes = 8192

    @inlineCallbacks
    def extract(self, response):
        # If the HTTP "Content-Type" header specifies an encoding, try
        # to use it to decode the document.
        params = cgi.parse_header(
            response.headers.getRawHeaders('Content-Type', [''])[0])[1]
        encoding = params.get('charset', self.default_encoding)
        content = yield read_body(response, max_bytes=self.max_download_bytes)
        try:
            decoded = content.decode(encoding, 'replace')
        except LookupError:  # someone gave us a bad encoding name
            decoded = content.decode(self.default_encoding, 'replace')
        returnValue(decoded.splitlines()[0])


extractor = PlainTextTitleExtractor()
