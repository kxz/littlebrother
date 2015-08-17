"""Test helpers."""


import os.path

from stenographer import CassetteAgent
from twisted.web.client import (ContentDecoderAgent, RedirectAgent,
                                Agent, GzipDecoder)
from twisted.web.test.test_agent import (FakeReactorAndConnectMixin)


def cassette_path(name):
    """Return the full path of a cassette file in our fixtures."""
    return os.path.join(os.path.dirname(__file__),
                        'fixtures', 'cassettes', name + '.json')


class CassetteTestMixin(FakeReactorAndConnectMixin):
    extractor = None

    def setUp(self):
        self.reactor = self.Reactor()
        self.agent = self.buildAgentForWrapperTest(self.reactor)
        self.connect(None)

    def assert_title(self, cassette_name, expected):
        agent = ContentDecoderAgent(
            RedirectAgent(CassetteAgent(self.agent,
                                        cassette_path(cassette_name))),
            [('gzip', GzipDecoder)])
        finished = agent.request(
            'GET', 'http://127.0.0.1:5000/{}'.format(cassette_name))
        finished.addCallback(self.extractor.extract)
        finished.addCallback(self.assertEqual, expected)
        return finished
