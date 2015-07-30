"""Test helpers."""


import os.path

from twisted.python.failure import Failure
from twisted.test.proto_helpers import StringTransport
from twisted.web.client import ResponseDone
from twisted.web._newclient import HTTPClientParser, Request
from twisted.web.http_headers import Headers


def saved_response(filename):
    """Parse the HTTP response serialized to *filename* and return a
    `Deferred` yielding a Twisted Web `Response` object."""
    request = Request('GET', '/', Headers(), None)
    parser = HTTPClientParser(request, lambda _: None)
    parser.makeConnection(StringTransport())
    finished = parser._responseDeferred
    response_path = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(response_path) as f:
        parser.dataReceived(f.read())
    parser.connectionLost(Failure(ResponseDone()))
    return finished
