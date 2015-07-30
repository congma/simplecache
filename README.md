`simplecache` -- implementing cached methods using `cachetools`, with
particular interest in the methods that takes a `numpy.ndarray` argument.

---

This little module is built on top of
[`cachetools`](http://pythonhosted.org/cachetools/ "cachetools").  We provide
an alternative to cachetools.cachedmethod by the method decorator factory
`memoized`, with the particular target of a method that takes a `numpy.ndarray`
argument.  It is adapted from the implementation of
[`cachetools.cachedmethod`](http://pythonhosted.org/cachetools/#cachetools.cachedmethod).
The original cachetools package is developed by Thomas Kemmer (c) and is
available as MIT-Licensed free software, available from
[GitHub](https://github.com/tkem/cachetools/ "cachetools repo") or PyPI.

Currently, it only supports methods with the definition signature of
```python
    def method(self, arrayarg, *args, **kwargs):
```
where `arrayarg` is expected to be a `numpy.ndarray` instance, and it is this
argument that will be used to derive a key for cache access.  Class methods or
static methods are currently not supported.

For your class to benefit from this memoization decorator, it must first
inherit from our `ArrayMethodCacheMixin` class alongside with its other parent
classes.  After that, you can use the `memoized` function to create decorators
that decorate your methods.  For example:
```python
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
```

After that, you can interactively test the effect of memoization by
instantiating `A`:
```python
>>> ta = A()
>>> x = numpy.array([1., 2., 3.])
>>> numpy.set_printoptions(precision=1)
```

The following call, when first invoked, will hang for a while:
```python
>>> print ta.frob(x)    # doctest: +NORMALIZE_WHITESPACE
[ 14000005.2  28000006.2  42000007.2]
```

But subsequent calls with the same argument will be very fast:
```python
>>> print ta.frob(x)    # doctest: +NORMALIZE_WHITESPACE
[ 14000005.2  28000006.2  42000007.2]
```

At this moment, if you wish, you can access the actual cache via the
`_cachedict` attribute, but manual handling of the cache is not recommended.
```python
>>> ta._cachedict       # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
{'frob': LRUCache(..., maxsize=64, currsize=1)}
```

After the first call to `ta.spam()`, it will have its own cache, too:
```python
>>> print "%.1f" % ta.spam(x)
2744002861600508.0
>>> ta._cachedict       # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
{'frob': LRUCache(..., maxsize=64, currsize=1), 'spam': LFUCache(...)}
```

---

Please see the file COPYING for copyright information.
