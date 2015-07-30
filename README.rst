Little Brother
==============

An HTTP document title extractor for Twisted Web.

Install it with::

    $ pip install littlebrother

Then, inside your Twisted code::

    import littlebrother

    def my_function(title):
        # do stuff with the returned title
        pass

    deferred = littlebrother.fetch_title('http://www.example.com/')
    deferred.addCallback(my_function)

You can also try Little Brother out directly from the command line::

    $ python -m littlebrother http://www.example.com/
    Example Domain

Report bugs and make feature requests on `Little Brother's GitHub
project page <https://github.com/kxz/littlebrother>`_.
