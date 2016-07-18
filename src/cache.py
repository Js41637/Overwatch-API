try:
    from google.appengine.api import memcache
except:
    memcache = False


def get(key):
    if memcache:
        return memcache.get(key)
    else:
        return None


def set(key, data, expire):
    if memcache:
        memcache.set(key, data, expire)
