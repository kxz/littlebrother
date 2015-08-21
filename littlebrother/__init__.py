"""Little Brother, an HTTP document title extractor for Twisted Web."""


import cgi
from collections import namedtuple
import sys
from urlparse import urljoin, urlparse

import ipaddress
from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.internet.protocol import Protocol, connectionDone
from twisted.plugin import IPlugin, getPlugins
from twisted.python.failure import Failure
from twisted.web.client import (URI, IAgent, Agent, ContentDecoderAgent,
                                RedirectAgent, GzipDecoder, ResponseFailed)
from twisted.web.error import InfiniteRedirection
from twisted.web.iweb import UNKNOWN_LENGTH
from zope.interface import implements, Attribute

from . import plugins
from .humanize import filesize


#
# HTTP response body truncation
#

class TruncatingReadBodyProtocol(Protocol):
    """A protocol that collects data sent to it up to a maximum of
    *max_bytes*, then discards the rest."""

    def __init__(self, status, message, finished, max_bytes=None):
        self.status = status
        self.message = message
        self.finished = finished
        self.data_buffer = []
        self.remaining = max_bytes or sys.maxsize

    def dataReceived(self, data):
        if self.remaining > 0:
            to_buffer = data[:self.remaining]
            self.data_buffer.append(to_buffer)
            self.remaining -= len(to_buffer)
        if self.remaining <= 0:
            self.transport.loseConnection()

    def connectionLost(self, reason=connectionDone):
        if not self.finished.called:
            self.finished.callback(''.join(self.data_buffer))


def read_body(response, max_bytes=None):
    """Return a `Deferred` yielding at most *max_bytes* bytes from the
    body of a Twisted Web *response*, or the whole body if *max_bytes*
    is `None`."""
    finished = Deferred()
    response.deliverBody(TruncatingReadBodyProtocol(
        response.code, response.phrase, finished, max_bytes))
    return finished


#
# Host blacklisting
#

class BlacklistedHost(Exception):
    """Raised when a `BlacklistingAgent` attempts to request a
    blacklisted resource."""

    def __init__(self, hostname, ip):
        self.hostname = hostname
        self.ip = ip

    def __str__(self):
        return 'host {} corresponds to blacklisted IP {}'.format(
            self.hostname, self.ip)


class BlacklistingAgent(object):
    """An `~twisted.web.client.Agent` wrapper that forbids requests to
    loopback, private, and internal IP addresses."""
    implements(IAgent)

    def __init__(self, agent, resolve=None):
        self.agent = agent
        self.resolve = resolve or reactor.resolve

    @inlineCallbacks
    def request(self, method, uri, headers=None, bodyProducer=None):
        """Issue a request to the server indicated by *uri*."""
        hostname = urlparse(uri).hostname
        ip_str = yield self.resolve(hostname)
        # `ipaddress` takes a Unicode string and I don't really care to
        # handle `UnicodeDecodeError` separately.
        ip = ipaddress.ip_address(ip_str.decode('ascii', 'replace'))
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise BlacklistedHost(hostname, ip)
        response = yield self.agent.request(method, uri, headers, bodyProducer)
        returnValue(response)


#
# Plugin interfaces and helper classes
#

#: Returned by title extractors to indicate a "soft" redirect, such as
#: an HTML ``<meta>`` refresh.  The *location* parameter indicates the
#: new URL to fetch.
Redirect = namedtuple('Redirect', ['location'])


class ITitleExtractor(IPlugin):
    """A plugin that can retrieve the title of a given Web document."""

    content_types = Attribute("""An iterable containing the MIME content
        types that this title extractor supports, such as ``('text/xml',
        'image/gif')``.""")

    def extract(self, response):
        """Given a Twisted Web *response*, return a Unicode string
        containing the extracted title, a `Redirect` object pointing at
        a new URL from which to fetch a document title, or a `Deferred`
        yielding either."""


#
# Object-oriented API
#

default_extractors = {}
for extractor in getPlugins(ITitleExtractor, plugins):
    for content_type in extractor.content_types:
        default_extractors[content_type] = extractor


class TitleFetcher(object):
    """Does exactly what it says on the tin."""

    def __init__(self):
        #: The Twisted Web `Agent` used to make HTTP requests.
        self.agent = ContentDecoderAgent(
            RedirectAgent(BlacklistingAgent(Agent(reactor))),
            [('gzip', GzipDecoder)])
        #: A dictionary of extractors enabled for this fetcher.
        self.extractors = default_extractors
        #: The maximum number of "soft" redirects to follow per request.
        self.max_soft_redirects = 2

    @inlineCallbacks
    def fetch_title(self, uri, hostname_tag=False):
        """Fetch the document at *uri* and return a `Deferred` yielding
        the document title or summary as a Unicode string.

        If *hostname_tag* is true, prefix the extracted title with the
        hostname of the initially requested URI, as well as the hostname
        of the final URI if it differs due to redirects."""
        title = None
        response = None
        for _ in xrange(self.max_soft_redirects):
            last_response = response
            response = yield self.agent.request('GET', uri)
            response.setPreviousResponse(last_response)
            content_type = cgi.parse_header(
                response.headers.getRawHeaders('Content-Type', [''])[0])[0]
            if content_type in self.extractors:
                extractor = self.extractors[content_type]
                extracted = yield extractor.extract(response)
                if isinstance(extracted, Redirect):
                    uri = urljoin(uri, extracted.location)
                    continue
                title = extracted
            # The only case where we'd want to loop again is when the
            # response returned is a soft redirect.
            break
        else:
            raise ResponseFailed([Failure(InfiniteRedirection(
                599, 'Too many soft redirects', location=uri))])
        if title is None:
            title = u'{} document'.format(content_type or u'Unknown')
            if response.length is not UNKNOWN_LENGTH:
                title += u' ({})'.format(filesize(response.length))
        if hostname_tag:
            initial = URI.fromBytes(uri).host
            final = URI.fromBytes(response.request.absoluteURI).host
            if initial == final:
                tag = initial
            else:
                tag = u'{} \u2192 {}'.format(initial, final)
            title = u'[{}] {}'.format(tag, title)
        returnValue(title)


#
# Convenience methods
#

fetcher = None
def get_fetcher():
    """Return a default `TitleFetcher`."""
    global fetcher
    if fetcher is None:
        fetcher = TitleFetcher()
    return fetcher


def fetch_title(*args, **kwargs):
    return get_fetcher().fetch_title(*args, **kwargs)
fetch_title.__doc__ = TitleFetcher.fetch_title.__doc__
