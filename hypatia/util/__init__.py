import BTrees

from persistent import Persistent
from ZODB.broken import Broken

_marker = object()

from .. import exc

class ResultSet(object):

    family = BTrees.family64

    def __init__(self, ids, numids, resolver):
        self.ids = ids # only guaranteed to be iterable, not sliceable
        self.numids = numids
        self.resolver = resolver
        
    def __len__(self):
        return self.numids

    def sort(self, index, limit=None, reverse=False):
        ids = self.ids

        if not hasattr(ids, '__len__'):
            # indexes have no obligation to be able to sort generators
            ids = list(ids)
            self.ids = ids

        ids = index.sort(
            self.ids,
            reverse=reverse,
            limit=limit,
            )

        numids = self.numids

        if limit:
            numids = min(numids, limit)

        return self.__class__(ids, numids, self.resolver)

    def first(self, resolve=True):
        # return the first object or None
        resolver = self.resolver
        if resolver is None or not resolve:
            for id_ in self.ids:
                return id_
        else:
            for id_ in self.ids:
                return resolver(id_)

    def one(self, resolve=True):
        if self.numids == 1:
            return self.first(resolve=resolve)
        if self.numids > 1:
            raise exc.MultipleResults(self)
        else:
            raise exc.NoResults(self)

    def _resolve_all(self, resolver):
        for id_ in self.ids:
            yield resolver(id_)

    def all(self, resolve=True):
        resolver = self.resolver
        if resolver is None or not resolve:
            return self.ids
        else:
            return self._resolve_all(resolver)

    def __iter__(self):
        return iter(self.all())

class BaseIndexMixin(object):
    """ Mixin class for indexes that implements common behavior """

    family = BTrees.family64

    def discriminate(self, obj, default):
        """ See interface IIndexInjection """
        if callable(self.discriminator):
            value = self.discriminator(obj, _marker)
        else:
            value = getattr(obj, self.discriminator, _marker)

        if value is _marker:
            return default
        
        if isinstance(value, Persistent):
            raise ValueError('Catalog cannot index persistent object %s' %
                             value)

        if isinstance(value, Broken):
            raise ValueError('Catalog cannot index broken object %s' %
                             value)

        return value

    def reindex_doc(self, docid, obj):
        """ See interface IIndexInjection """
        self.unindex_doc(docid)
        self.index_doc(docid, obj)

    def indexed_count(self):
        """ See IIndexedDocuments """
        return len(self.indexed())

    def not_indexed_count(self):
        """ See IIndexedDocuments """
        return len(self.not_indexed())

    def docids(self):
        """ See IIndexedDocuments """
        not_indexed = self.not_indexed()
        indexed = self.indexed()
        if len(not_indexed) == 0:
            return self.family.IF.Set(indexed)
        elif len(indexed) == 0:
            return not_indexed
        indexed = self.family.IF.Set(indexed)
        return self.family.IF.union(not_indexed, indexed)

    def docids_count(self):
        """ See IIndexedDocuments """
        return len(self.docids())

    def apply_intersect(self, query, docids):
        """ Default apply_intersect implementation """
        result = self.apply(query)
        if docids is None:
            return result
        return self.family.IF.weightedIntersection(result, docids)[1]

    def _negate(self, apply_func, *args, **kw):
        positive = apply_func(*args, **kw)
        all = self.docids()
        if len(positive) == 0:
            return all
        return self.family.IF.difference(all, positive)

    def qname(self):
        # used in query representations; __name__ should be set by
        # catalog __setitem__ but if it's not, we fall back to a generic
        # representation
        return getattr(
            self,
            '__name__',
            str(self),
            )
        
    def resultset_from_query(self, query, names=None, resolver=None):
        # default resultset factory; meant to be overridden by systems
        # that have a default resolver
        docids = query._apply(names)
        numdocs = len(docids)
        return ResultSet(docids, numdocs, resolver)

    def flush(self, *arg, **kw):
        """ Hookable by upstream systems"""
        pass

class RichComparisonMixin(object):
    # Stolen from http://www.voidspace.org.uk/python/recipebook.shtml#comparison

    def __eq__(self, other):
        raise NotImplementedError("Equality not implemented")

    def __lt__(self, other):
        raise NotImplementedError("Less than not implemented")

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __gt__(self, other):
        return not (self.__lt__(other) or self.__eq__(other))

    def __le__(self, other):
        return self.__eq__(other) or self.__lt__(other)

    def __ge__(self, other):
        return self.__eq__(other) or self.__gt__(other)

