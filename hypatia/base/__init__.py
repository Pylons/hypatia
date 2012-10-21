import BTrees

from persistent import Persistent
from ZODB.broken import Broken

_marker = object()

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
        

