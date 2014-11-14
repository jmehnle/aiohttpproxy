aiohttpproxy
============

Simple caching HTTP proxy based on the Python aiohttp asynchronous-I/O HTTP module.

Currently only GET requests to HTTP URLs are proxied.

Installation
------------

Install using your favorite Python packager:

    $ easy_install aiohttpproxy-0.0.1/
    $ pip install git+https://github.com/jmehnle/aiohttpproxy.git

Usage
-----

The proxy is controlled entirely from the command-line, with the following syntax:

    usage: aiohttpproxy [-h] [-l LEVEL] [--port PORT] --cache-path PATH
                        [--cache-max-size SIZE] [--cache-max-entries COUNT]
                        [--cache-max-age SECONDS]

    optional arguments:
      -h, --help            show this help message and exit
      -l LEVEL, --log-level LEVEL
                            Log level (critical, error, warning, info, debug)
      --port PORT           TCP port to listen on (default: 8080)
      --cache-path PATH     Cache directory
      --cache-max-size SIZE
                            Max total cache size in bytes
      --cache-max-entries COUNT
                            Max number of cache entries
      --cache-max-age SECONDS
                            Max age of cache entries

Sample invocation:

    $ mkdir /var/tmp/aiohttpproxy.cache
    $ aiohttpproxy --log-level info \
        --cache-path /var/tmp/aiohttpproxy.cache \
        --cache-max-size 1048576 --cache-max-entries 1000 --cache-max-age 60

... limits the number of cached responses to 1000 and their total content size to 1MB, and expires cache entries after 60 seconds.

Terminate the proxy with `Ctrl+C` or by sending SIGINT.

Copyright
---------

(C) 2014 Julian Mehnle <julian@mehnle.net>
