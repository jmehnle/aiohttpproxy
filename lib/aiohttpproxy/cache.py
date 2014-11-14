import os, os.path
import time
import hashlib
import collections
import logging
from contextlib import suppress

class CacheError(Exception): pass

class CacheSizeExceededError(CacheError): pass

class CacheEntry:
    @classmethod
    def filename(cls, key):
        return hashlib.sha1(bytes(key, 'utf-8')).hexdigest()

    def __init__(self, cache, key, metadata = None):
        self.cache    = cache
        self.key      = key
        self.metadata = metadata
        self.filename = os.path.join(cache.path, type(self).filename(key))

        # Initialize state:
        self.dirty()

    def dirty(self):
        self.__size = None
        self.__atime, self.__mtime = None, None

    @property
    def size(self):
        if self.__size is None:
            self.__size = os.stat(self.filename).st_size
        return self.__size

    @property
    def mtime(self):
        if self.__mtime is None:
            stat = os.stat(self.filename)
            self.__atime, self.__mtime = stat.st_atime, stat.st_mtime
        return self.__mtime

    @mtime.setter
    def mtime(self, value):
        self.__mtime = value
        os.utime(self.filename, (self.__atime, self.__mtime))

    def delete(self):
        os.remove(self.filename)

class LRUCache:
    def __init__(self, path, max_size = None, max_entries = None, max_age = None):
        path = str(path)
        if not os.path.isdir(path):
            raise ValueError('Cache path not a directory: {0}'.format(path))
        if not os.access(path, os.W_OK | os.X_OK):
            raise ValueError('Cache path is not writable: {0}'.format(path))

        logging.debug(
            'Creating cache at {0} with max size {1}, max entries {2}, max age {3}s'.format(
            path, max_size, max_entries, max_age))

        # Configuration:
        self.path        = path
        self.max_size    = max_size
        self.max_entries = max_entries
        self.max_age     = max_age

        # State:
        self.clear()

    def __getitem__(self, key):
        entry = self.entries[key]
        if self.max_age and time.time() > entry.mtime + self.max_age:
            del self[key]
            raise KeyError
        self.entries.move_to_end(key)  # Update access order.
        return entry

    def __setitem__(self, key, entry):
        with suppress(KeyError):
            del self[key]
        if entry.size > self.max_size:
            raise CacheSizeExceededError('Requested entry size ({0}) exceeds overall cache size ({1})'.format(entry.size, self.max_size))
        if (
            (self.max_entries and self.max_entries < len(self.entries) + 1)  or
            (self.max_size    and self.max_size    < self.size + entry.size)
        ):
            self.expire()
        while (
            (self.max_entries and self.max_entries < len(self.entries) + 1)  or
            (self.max_size    and self.max_size    < self.size + entry.size)
        ):
            self.discard_one()
        self.entries[key] = entry

    def __delitem__(self, key):
        entry = self.entries.pop(key)
        self.size = self.size - entry.size
        entry.delete()

    def __iter__(self):
        return self.entries.itervalues()

    def __contains__(self, key):
        return key in self.entries

    def new_entry(self, key, metadata = None, size = None):
        if size and size > self.max_size:
            raise CacheSizeExceededError('Requested entry size ({0}) exceeds overall cache size ({1})'.format(size, self.max_size))
        return CacheEntry(self, key, metadata)

    def clear(self):
        with suppress(AttributeError):
            for entry in self.entries.values():
                entry.delete()
        self.entries = collections.OrderedDict()
        self.size    = 0

    def expire(self):
        if self.max_age is None:
            return
        now = time.time()
        expired_entries = []
        for key, entry in self.entries.items():
            if now > entry.mtime + self.max_age:
                del self[key]
                expired_entries.append(entry)
        return expired_entries

    def discard_one(self):
        key, entry = next(iter(self.entries.items()))  # Determine LRU entry.
        del self[key]
        return entry

# vim:sw=2 sts=2
