# -*- coding: utf-8
"""Tests for HTTP machinery."""


from twisted.internet.defer import Deferred, succeed
from twisted.internet.error import ConnectError
from twisted.python.failure import Failure
from twisted.trial.unittest import TestCase
from twisted.web.client import RedirectAgent, Response, ResponseFailed
from twisted.web.http_headers import Headers
from twisted.web.test.test_agent import (
    AbortableStringTransport, AgentTestsMixin, FakeReactorAndConnectMixin)

from .. import (TruncatingReadBodyProtocol, BlacklistingAgent,
                BlacklistedHost, TitleFetcher, Redirect)


class TruncatingReadBodyProtocolTestCase(TestCase):
    def assert_delivery(self, data, expected):
        finished = Deferred()
        finished.addCallback(self.assertEqual, expected)
        response = Response(('HTTP', 1, 1), 200, 'OK', Headers(),
                            AbortableStringTransport())
        protocol = TruncatingReadBodyProtocol(
            response.code, response.phrase, finished, max_bytes=8)
        response.deliverBody(protocol)
        response._bodyDataReceived(data)
        response._bodyDataFinished()
        return finished

    def test_complete(self):
        return self.assert_delivery('#' * 4, '#' * 4)

    def test_truncated(self):
        return self.assert_delivery('#' * 16, '#' * 8)


class BlacklistingAgentTestCase(AgentTestsMixin,
                                FakeReactorAndConnectMixin, TestCase):
    # <https://twistedmatrix.com/trac/ticket/4024>... one wishes.
    #
    # Based in part on `twisted.web.test.test_agent.RedirectAgentTests`.

    sample_hosts = ('localhost', '0.0.0.0', '10.0.0.1', '127.0.0.1',
                    '169.254.0.1', '172.16.0.1', '192.168.0.1')

    @staticmethod
    def resolve(hostname):
        if hostname == 'localhost':
            return succeed('127.0.0.1')
        elif hostname == 'foo.test':
            return succeed('8.8.8.8')
        return succeed(hostname)

    def makeAgent(self):
        return BlacklistingAgent(self.buildAgentForWrapperTest(self.reactor),
                                 resolve=self.resolve)

    def setUp(self):
        self.reactor = self.Reactor()
        self.agent = self.makeAgent()

    def test_no_blacklist(self):
        self.agent.request('GET', 'http://foo.test/')

    def assert_blacklist(self, method, uri):
        d = self.agent.request(method, uri)
        f = self.failureResultOf(d, BlacklistedHost)

    def test_blacklist(self):
        for protocol in ('http', 'https'):
            for host in self.sample_hosts:
                uri = '{}://{}/'.format(protocol, host)
                for method in ('GET', 'POST'):
                    self.assert_blacklist(method, uri)


class SoftRedirectExtractor(object):
    def __init__(self, target):
        self.target = target

    def extract(self, response):
        return succeed(Redirect(self.target))


class HostnameTagTestCase(AgentTestsMixin,
                          FakeReactorAndConnectMixin, TestCase):
    def makeAgent(self):
        return self.buildAgentForWrapperTest(self.reactor)

    def setUp(self):
        self.reactor = self.Reactor()
        self.agent = RedirectAgent(self.makeAgent())
        self.fetcher = TitleFetcher()
        self.fetcher.agent = self.agent
        self.connect(None)

    def test_no_redirect(self):
        finished = self.fetcher.fetch_title(
            'http://foo.test/', hostname_tag=True)
        request, result = self.protocol.requests.pop()
        response = Response._construct(('HTTP', 1, 1), 200, 'OK', Headers(),
                                       AbortableStringTransport(), request)
        result.callback(response)
        finished.addCallback(self.assertEqual, u'[foo.test] Unknown document')
        return finished

    def test_redirect_to_different_host(self):
        finished = self.fetcher.fetch_title(
            'http://foo.test/', hostname_tag=True)
        request, result = self.protocol.requests.pop()
        redirect_headers = Headers()
        redirect_headers.addRawHeader('Location', 'http://bar.test/')
        response = Response._construct(
            ('HTTP', 1, 1), 301, 'Moved Permanently', redirect_headers,
            AbortableStringTransport(), request)
        result.callback(response)
        request, result = self.protocol.requests.pop()
        response = Response._construct(('HTTP', 1, 1), 200, 'OK', Headers(),
                                       AbortableStringTransport(), request)
        result.callback(response)
        finished.addCallback(self.assertEqual,
                             u'[foo.test → bar.test] Unknown document')
        return finished

    def test_redirect_to_same_host(self):
        finished = self.fetcher.fetch_title(
            'http://foo.test/', hostname_tag=True)
        request, result = self.protocol.requests.pop()
        redirect_headers = Headers()
        redirect_headers.addRawHeader('Location', 'http://foo.test/bar')
        response = Response._construct(
            ('HTTP', 1, 1), 301, 'Moved Permanently', redirect_headers,
            AbortableStringTransport(), request)
        result.callback(response)
        request, result = self.protocol.requests.pop()
        response = Response._construct(('HTTP', 1, 1), 200, 'OK', Headers(),
                                       AbortableStringTransport(), request)
        result.callback(response)
        finished.addCallback(self.assertEqual, u'[foo.test] Unknown document')
        return finished

    def test_soft_redirect(self):
        self.fetcher.extractors = {
            'text/html': SoftRedirectExtractor(u'http://bar.test/')}
        finished = self.fetcher.fetch_title(
            'http://foo.test/', hostname_tag=True)
        request, result = self.protocol.requests.pop()
        redirect_headers = Headers()
        redirect_headers.addRawHeader('Content-Type', 'text/html')
        response = Response._construct(
            ('HTTP', 1, 1), 200, 'OK', redirect_headers,
            AbortableStringTransport(), request)
        result.callback(response)
        request, result = self.protocol.requests.pop()
        response = Response._construct(('HTTP', 1, 1), 200, 'OK', Headers(),
                                       AbortableStringTransport(), request)
        result.callback(response)
        finished.addCallback(self.assertEqual,
                             u'[foo.test → bar.test] Unknown document')
        return finished

    def test_tag_iri_to_uri(self):
        finished = self.fetcher.fetch_title(
            u'http://ドメイン名例.test/', hostname_tag=True)
        request, result = self.protocol.requests.pop()
        response = Response._construct(('HTTP', 1, 1), 200, 'OK', Headers(),
                                       AbortableStringTransport(), request)
        result.callback(response)
        finished.addCallback(self.assertEqual,
                             u'[ドメイン名例.test → xn--eckwd4c7cu47r2wf.test] '
                             u'Unknown document')
        return finished


class FriendlyErrorTestCase(AgentTestsMixin,
                            FakeReactorAndConnectMixin, TestCase):
    def makeAgent(self):
        return self.buildAgentForWrapperTest(self.reactor)

    def setUp(self):
        self.reactor = self.Reactor()
        self.agent = RedirectAgent(self.makeAgent())
        self.fetcher = TitleFetcher()
        self.fetcher.agent = self.agent
        self.connect(None)

    def test_infinite_hard_redirection(self):
        finished = self.fetcher.fetch_title(
            u'http://foo.test/', hostname_tag=True, friendly_errors=True)
        while self.protocol.requests:
            request, result = self.protocol.requests.pop()
            redirect_headers = Headers()
            redirect_headers.addRawHeader('Location', 'http://foo.test/')
            response = Response._construct(
                ('HTTP', 1, 1), 301, 'Moved Permanently', redirect_headers,
                AbortableStringTransport(), request)
            result.callback(response)
        finished.addCallback(self.assertEqual,
                             u'[foo.test] Encountered too many redirects.')
        return finished

    def test_infinite_soft_redirection(self):
        self.fetcher.extractors = {
            'text/html': SoftRedirectExtractor(u'http://foo.test/')}
        finished = self.fetcher.fetch_title(
            u'http://foo.test/', hostname_tag=True, friendly_errors=True)
        while self.protocol.requests:
            request, result = self.protocol.requests.pop()
            redirect_headers = Headers()
            redirect_headers.addRawHeader('Content-Type', 'text/html')
            response = Response._construct(
                ('HTTP', 1, 1), 200, 'OK', redirect_headers,
                AbortableStringTransport(), request)
            result.callback(response)
        finished.addCallback(self.assertEqual,
                             u'[foo.test] Encountered too many redirects.')
        return finished

    def test_response_failed(self):
        finished = self.fetcher.fetch_title(
            u'http://foo.test/', hostname_tag=True, friendly_errors=True)
        _, result = self.protocol.requests.pop()
        result.errback(Failure(ResponseFailed([])))
        finished.addCallback(
            self.assertEqual,
            u'[foo.test] Received incomplete response from server.')

    def test_connect_error(self):
        finished = self.fetcher.fetch_title(
            u'http://foo.test/', hostname_tag=True, friendly_errors=True)
        _, result = self.protocol.requests.pop()
        result.errback(Failure(ConnectError()))
        finished.addCallback(
            self.assertEqual,
            u'[foo.test] Could not connect to server.')

    def test_blacklisted_host(self):
        finished = self.fetcher.fetch_title(
            u'http://foo.test/', hostname_tag=True, friendly_errors=True)
        _, result = self.protocol.requests.pop()
        result.errback(Failure(BlacklistedHost('foo.test', '127.0.0.1')))
        finished.addCallback(
            self.assertEqual,
            u'[foo.test] Could not connect to server.')

    def test_errback_when_disabled(self):
        finished = self.fetcher.fetch_title(
            u'http://foo.test/', hostname_tag=True, friendly_errors=False)
        _, result = self.protocol.requests.pop()
        result.errback(Failure(ResponseFailed([])))
        return self.assertFailure(finished, ResponseFailed)

    def test_errback_on_unrecognized_failure(self):
        finished = self.fetcher.fetch_title(
            u'http://foo.test/', hostname_tag=True, friendly_errors=False)
        _, result = self.protocol.requests.pop()
        result.errback(Failure(ValueError()))
        return self.assertFailure(finished, ValueError)
