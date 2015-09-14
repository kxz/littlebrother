"""Test helpers."""


import os.path

from stenographer import CassetteAgent
from twisted.internet import reactor
from twisted.web.client import (ContentDecoderAgent, RedirectAgent,
                                Agent, GzipDecoder)


def cassette_path(name):
    """Return the full path of a cassette file in our fixtures."""
    return os.path.join(os.path.dirname(__file__),
                        'fixtures', 'cassettes', name + '.json')


class CassetteTestMixin(object):
    extractor = None

    def assert_title(self, cassette_name, expected):
        cassette_agent = CassetteAgent(Agent(reactor),
                                       cassette_path(cassette_name),
                                       preserve_exact_body_bytes=True)
        agent = ContentDecoderAgent(RedirectAgent(cassette_agent),
                                    [('gzip', GzipDecoder)])
        finished = agent.request(
            'GET', 'http://127.0.0.1:5000/{}'.format(cassette_name))
        finished.addCallback(self.extractor.extract)
        finished.addCallback(self.assertEqual, expected)
        finished.addBoth(cassette_agent.save)
        return finished
