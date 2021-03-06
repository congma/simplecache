# vim: spell spelllang=en
"""
simplecache -- implementing cached methods using cachetools, with particular
interest in the methods that takes a numpy.ndarray argument.

This little module is built on top of cachetools
<http://pythonhosted.org/cachetools/>.  We provide an alternative to
cachetools.cachedmethod by the method decorator factory ``memoized()'', with
the particular target of a method that takes a numpy.ndarray argument.  It is
adapted from the implementation of cachetools.cachedmethod().  The original
cachetools package is developed by Thomas Kemmer (c) and is available as
MIT-Licensed free software, available from GitHub
<https://github.com/tkem/cachetools/> or PyPI.

Currently, it only supports methods with the definition signature of

    def method(self, arrayarg, *args, **kwargs):

where arrayarg is expected to be a numpy.ndarray instance, and it is this
argument that will be used to derive a key for cache access.  Class methods or
static methods are currently not supported.

For your class to benefit from this memoization decorator, it must first
inherit from our ArrayMethodCacheMixin class alongside with its other parent
classes.  After that, you can use the memoized() function to create decorators
that decorate your methods.  For example:
>>> import numpy
>>> class A(ArrayMethodCacheMixin, object):
...     v = 4.2
... 
...     @memoized()
...     def frob(self, array):
...         '''Docstring for method frob is preserved.'''
...         # Lengthy, expensive, and phony calculations...
...         tmp = array.copy()
...         p = numpy.outer(array, array)
...         for i in xrange(1000000):
...             tmp += numpy.dot(p, array)
...         return tmp + self.v
... 
...     @memoized(cachetype=cachetools.LFUCache, cachesize=2)
...     def spam(self, array, blah=5.0):
...         f = self.frob(array)
...         return numpy.dot(f, f + blah * self.v)

After that, you can interactively test the effect of memoization by
instantiating A:
>>> ta = A()
>>> x = numpy.array([1., 2., 3.])
>>> numpy.set_printoptions(precision=1)

The following call, when first invoked, will hang for a while:
>>> print ta.frob(x)    # doctest: +NORMALIZE_WHITESPACE
[ 14000005.2  28000006.2  42000007.2]

But subsequent calls with the same argument will be very fast:
>>> print ta.frob(x)    # doctest: +NORMALIZE_WHITESPACE
[ 14000005.2  28000006.2  42000007.2]

At this moment, if you wish, you can access the actual cache via the
_cachedict attribute, but manual handling of the cache is not recommended.
>>> ta._cachedict       # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
{'frob': LRUCache(..., maxsize=64, currsize=1)}

After the first call to ta.spam(), it will have its own cache, too:
>>> print "%.1f" % ta.spam(x)
2744002861600508.0
>>> items = ta._cachedict.items()
>>> items.sort()
>>> print items         # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
[('frob', LRUCache(..., maxsize=64, currsize=1)), ('spam', LFUCache(...))]

Docstring of the decorated method is preserved as-is:
>>> print ta.frob.__doc__
Docstring for method frob is preserved.

Author: Cong Ma <cong.ma@obspm.fr>, (c) 2015.  See the file COPYING.
"""


import functools
import cachetools


def keyfcn_default(array):
    """Default key function on an numpy.ndarray argument.  This should "work"
    most of the time but is expensive for large arrays.
    """
    return array.tostring()


def memoized(cachetype=cachetools.LRUCache, cachesize=64,
             keyfcn=keyfcn_default, *cargs, **ckwargs):
    """Decorator-factory that returns a decorator suitable for methods of a
    class that inherits ArrayMethodCacheMixin.

    Optional arguments that fine-tunes the creation of method caches:
        cachetype: Type of cache -- I'd recommend the cache types from the
                   cachetools package.  It can actually be None, which means no
                   caching should be present.  This is probably only useful for
                   testing.
        cachesize: Size of cache.  The value of this argument will be the one
                   passed to the value of cachetype as the latter's first call
                   argument.  If the value of cachetype doesn't take a size
                   parameter this way, things may break.  This is the
                   convention followed by cachetools.  Except when cachetype is
                   None, then this argument is ignored.
        keyfcn: Key function to be applied to the array argument that is passed
                as the first mandatory argument of the method to be decorated.
        *cargs, **ckwargs: extra parameters to be passed to the value of
                           cachetype for instantiating the actual cache
                           instance.
    """
    if cachetype is None:
        # Do nothing, return identity decorator.
        return lambda x: x

    def decorator(arraymethod):
        """Method decorator to be returned by the enclosing factory function.
        """
        # Create the wrapper around the underlying method call.  This wrapper
        # does the memoization using the cache just
        # retrieve-if-absent-create'd.
        mname = arraymethod.__name__

        @functools.wraps(arraymethod)
        def wrapper(self, arrayarg, *args, **kwargs):
            """The actual wrapper that intercepts the method call arguments,
            performs the caching, and returns the result to caller.
            """
            # If no cache yet, create cache for this method.
            try:
                # _cachedict is keyed by the method names, rather than the
                # unwrapped method objects themselves, although the latter is
                # possible.  We choose the former because this helps debugging
                # better.  The original method, once wrapped, could be hard to
                # access by a Python name, although one can still enumerate
                # _cachedict's keys.  Our choice works, because
                # functools.wraps() ensures conservation of names.
                cache = self._cachedict[mname]
            except KeyError:
                cache = cachetype(cachesize, *cargs, **ckwargs)
                self._cachedict[mname] = cache
            argkey = keyfcn(arrayarg)
            try:
                return cache[argkey]
            except KeyError:
                # Cache miss, compute and store the return value.
                pass
            retval = arraymethod(self, arrayarg, *args, **kwargs)
            try:
                cache[argkey] = retval
            except ValueError:
                # Value probably too large, ignore and pass through.
                pass
            return retval
        return wrapper
    return decorator


class ArrayMethodCacheMixin(object):
    """Mix-in class that only creates an attribute to access the caches in the
    instance during initialization.

    Classes that inherits this mix-in can super()-delegate the __init__()
    method so that things happen automatically.
    """
    def __init__(self, *args, **kwargs):
        """Create the container for the method caches in this instance (self).
        """
        self._cachedict = {}


if __name__ == "__main__":
    import doctest
    doctest.testmod()
