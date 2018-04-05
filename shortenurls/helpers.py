from django.core.cache import cache


def get_memcached_value(key):
    """ Checking memcache for a specific key. Returns a cached object if any or None"""
    return cache.get(key)


def add_to_memcache(key, val):
    """ Adding new value to memcache. Returns True if successfully added, False otherwise"""
    success = cache.add(key, val)
    return success
