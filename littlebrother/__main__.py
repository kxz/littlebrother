"""Command line entry points."""


import argparse
from itertools import imap
import sys

from twisted.internet import reactor
from twisted.internet.defer import DeferredList

from . import fetch_title


def print_and_exit(results):
    """Print each result and stop the reactor."""
    for success, value in results:
        if success:
            print value.encode('utf-8')
        else:
            value.printTraceback()
    reactor.stop()


def main():
    """Main command line entry point."""
    parser = argparse.ArgumentParser(
        description='Fetch a URI or series of URIs and print a title '
                    'or summary for each.',
        epilog='If no URIs are passed on the command line, they are '
               'read from standard input, one per line.')
    parser.add_argument(
        'uris', metavar='URI', nargs='*', help='URI to fetch')
    args = parser.parse_args()
    uris = args.uris or imap(lambda x: x.strip(), sys.stdin)
    finished = DeferredList([fetch_title(uri) for uri in uris])
    finished.addCallback(print_and_exit)
    reactor.run()


if __name__ == '__main__':
    main()
