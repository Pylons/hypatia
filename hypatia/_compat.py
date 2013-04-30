import sys

PY3 = sys.version_info[0] >= 3

if PY3: #pragma NO COVER
    def b(s):
        return s.encode("latin-1")
    def u(s):
        return s
    string_types = str,
    text_type = str
    binary_type = bytes
    integer_types = int,
    def non_native_string(x):
        if isinstance(x, bytes):
            return x
        return bytes(x, 'unicode_escape')
    def make_binary(x):
        if isinstance(x, bytes):
            return x
        return x.encode('ascii')
    intern = sys.intern
    xrange = range
    _long = int
    def _iteritems(x):
        return x.items()
    def _items(x):
        return list(x.items())
    def _maxint():
        return sys.maxsize
else: #pragma NO COVER
    def b(s):
        return s
    def u(s):
        return unicode(s, "unicode_escape")
    string_types = basestring,
    text_type = unicode
    binary_type = str
    integer_types = (int, long)
    def non_native_string(x):
        if isinstance(x, unicode):
            return x
        return unicode(x, 'unicode_escape')
    def make_binary(x):
        if isinstance(x, str):
            return x
        return x.encode('ascii')
    intern = intern
    xrange = xrange
    _long = long
    def _iteritems(x):
        return x.iteritems()
    def _items(x):
        return x.items()
    def _maxint():
        return sys.maxint
