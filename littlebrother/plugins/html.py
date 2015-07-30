"""Title extractor for HTML files."""


import cgi
import re

from bs4 import BeautifulSoup
from twisted.internet.defer import inlineCallbacks, returnValue
from zope.interface import implements

from .. import ITitleExtractor, read_body, Redirect


#: Beautiful Soup attribute selector for ``<meta>`` refreshes.
META_REFRESH_ATTRS = {'http-equiv': re.compile('refresh', re.IGNORECASE),
                      'content': True}


class HTMLTitleExtractor(object):
    implements(ITitleExtractor)
    content_types = ('text/html', 'application/xhtml+xml')

    def __init__(self, parser='html.parser'):
        #: The maximum number of bytes this extractor will download.
        self.max_download_bytes = 65536
        #: The Beautiful Soup parser to use for this extractor.
        self.parser = parser
        #: The maximum delay a ``<meta>`` refresh can have and still be
        #: considered a soft redirect.  This avoids catching pages that
        #: automatically refresh themselves every minute or longer.
        self.max_refresh_delay = 15

    @inlineCallbacks
    def extract(self, response):
        # If the HTTP "Content-Type" header specifies an encoding, try
        # to use it to decode the document.
        params = cgi.parse_header(
            response.headers.getRawHeaders('Content-Type', [''])[0])[1]
        content = yield read_body(response, max_bytes=self.max_download_bytes)
        soup = BeautifulSoup(content, self.parser,
                             from_encoding=params.get('charset'))
        # Handle any <meta> refreshes.
        for refresh in soup('meta', attrs=META_REFRESH_ATTRS):
            seconds, params = cgi.parse_header(refresh['content'])
            try:
                seconds = int(seconds, 10)
            except ValueError:
                # Not a valid number; just pretend it's zero.
                seconds = 0
            if seconds <= self.max_refresh_delay and 'url' in params:
                returnValue(Redirect(params['url'].encode('utf-8')))
        if soup.title:
            # Join twice: once because soup.title.strings is an iterator
            # and once after splitting to coalesce whitespace.
            returnValue(u' '.join(u''.join(soup.title.strings).split()))
        returnValue(None)


extractor = HTMLTitleExtractor()
