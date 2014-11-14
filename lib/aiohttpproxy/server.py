import io
import os, os.path
import logging
import time
import asyncio
import aiohttp
import aiohttp.server
import urllib.parse
import json
from contextlib import suppress

import aiohttpproxy
from aiohttpproxy import cache

class ProxyRequestHandler(aiohttp.server.ServerHttpProtocol):
    def __init__(self, cache = None):
        super(ProxyRequestHandler, self).__init__()
        self.cache = cache

    @asyncio.coroutine
    def handle_request(self, message, payload):
        now = time.time()

        url = message.path
        url_parsed = urllib.parse.urlparse(url)

        logging.info('{0} {1}'.format(message.method, url))

        if message.method == 'GET' and url == '/ping':
            # Generate pong.
            logging.info('Ping, Pong.')
            yield from self.send_pong_response(200, message.version)
            return

        if message.method != 'GET' or url_parsed.scheme.lower() != 'http':
            # Only GET method and http: scheme supported.
            logging.info('Refusing non-GET/HTTP request: {0}'.format(url))
            yield from self.send_response(501, message.version)
            return

        if self.cache:
            try:
                cache_entry = self.cache[url]
            except KeyError:
                cache_entry = None

        serve_from_cache = self.cache and     bool(cache_entry)
        store_in_cache   = self.cache and not bool(cache_entry)

        if serve_from_cache:
            cache_metadata = cache_entry.metadata
            cache_file     = open(cache_entry.filename, 'rb')
            logging.debug('Serving response from cache (filename = {0}, age = {1:.3}s).'.format(
                cache_entry.filename, now - cache_entry.mtime))

            response = cache_metadata['response']
        else:
            # Execute request and cache response:
            logging.debug('Executing request.')

            response = yield from aiohttp.request('GET', url, headers = message.headers)
            response_content = response.content

        if store_in_cache:
            with suppress(ValueError):
                size = int(response.headers['Content-Length'])
            try:
                cache_metadata = { 'response': response }
                cache_entry    = self.cache.new_entry(url, cache_metadata, size)
                cache_file     = open(cache_entry.filename, 'wb')
                logging.debug('Storing response in cache (filename = {0}).'.format(
                    cache_entry.filename))
            except cache.CacheSizeExceededError:
                # Do not cache responses larger than cache size.
                store_in_cache = False
                logging.debug('Not caching response exceeding overall cache size ({0} > {1}).'.format(
                    size, self.cache.max_size))

        proxy_response = aiohttp.Response(
            self.writer, response.status, http_version = response.version)
        proxy_response.add_headers(*response.headers.items())
        proxy_response.send_headers()

        try:
            while True:
                if serve_from_cache:
                    chunk = cache_file.read(io.DEFAULT_BUFFER_SIZE)
                else:
                    chunk = yield from response_content.read(io.DEFAULT_BUFFER_SIZE)
                if not chunk:
                    break
                proxy_response.write(chunk)
                if store_in_cache:
                    cache_file.write(chunk)

            yield from proxy_response.write_eof()

        finally:
            if serve_from_cache or store_in_cache:
                cache_file.close()
            if store_in_cache:
                self.cache[url] = cache_entry

    @asyncio.coroutine
    def send_response(self, status, http_version, headers = None, text = b''):
        response = aiohttp.Response(self.writer, status, http_version = http_version)
        if isinstance(headers, list):
            for name, value in headers:
                response.add_header(name, value)
        response.add_header('Content-Length', str(len(text)))
        response.send_headers()
        response.write(text)
        yield from response.write_eof()

    @asyncio.coroutine
    def send_pong_response(self, status, http_version):
        response_text = json.dumps(
            {
                'version': aiohttpproxy.__version__
            },
            indent = 4
        ).encode('ascii')
        yield from self.send_response(status, http_version, text = response_text)

# vim:sw=4 sts=4
