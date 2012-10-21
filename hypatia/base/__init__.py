import BTrees

from persistent import Persistent
from ZODB.broken import Broken

from .. import query

_marker = ()

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

    def _negate(self, assertion, *args, **kw):
        positive = assertion(*args, **kw)
        all = self.docids()
        if len(positive) == 0:
            return all
        return self.family.IF.difference(all, positive)

    def __str__(self):
        return getattr(self, '__name__', repr(self))

    def applyContains(self, *args, **kw):
        raise NotImplementedError(
            "Contains is not supported for %s" % type(self).__name__)

    def contains(self, value):
        return query.Contains(self, value)

    def applyDoesNotContain(self, *args, **kw):
        return self._negate(self.applyContains, *args, **kw)

    def doesnotcontain(self, value):
        return query.DoesNotContain(self, value)

    def applyEq(self, *args, **kw):
        raise NotImplementedError(
            "Eq is not supported for %s" % type(self).__name__)

    def eq(self, value):
        return query.Eq(self, value)

    def applyNotEq(self, *args, **kw):
        return self._negate(self.applyEq, *args, **kw)

    def noteq(self, value):
        return query.NotEq(self, value)

    def applyGt(self, *args, **kw):
        raise NotImplementedError(
            "Gt is not supported for %s" % type(self).__name__)

    def gt(self, value):
        return query.Gt(self, value)

    def applyLt(self, *args, **kw):
        raise NotImplementedError(
            "Lt is not supported for %s" % type(self).__name__)

    def lt(self, value):
        return query.Lt(self, value)

    def applyGe(self, *args, **kw):
        raise NotImplementedError(
            "Ge is not supported for %s" % type(self).__name__)

    def ge(self, value):
        return query.Ge(self, value)

    def applyLe(self, *args, **kw):
        raise NotImplementedError(
            "Le is not supported for %s" % type(self).__name__)

    def le(self, value):
        return query.Le(self, value)

    def applyAny(self, *args, **kw):
        raise NotImplementedError(
            "Any is not supported for %s" % type(self).__name__)

    def any(self, value):
        return query.Any(self, value)

    def applyNotAny(self, *args, **kw):
        return self._negate(self.applyAny, *args, **kw)

    def notany(self, value):
        return query.NotAny(self, value)

    def applyAll(self, *args, **kw):
        raise NotImplementedError(
            "All is not supported for %s" % type(self).__name__)

    def all(self, value):
        return query.All(self, value)

    def applyNotAll(self, *args, **kw):
        return self._negate(self.applyAll, *args, **kw)

    def notall(self, value):
        return query.NotAll(self, value)

    def applyInRange(self, *args, **kw):
        raise NotImplementedError(
            "InRange is not supported for %s" % type(self).__name__)

    def inrange(self, value):
        return query.InRange(self, value)

    def applyNotInRange(self, *args, **kw):
        return self._negate(self.applyInRange, *args, **kw)

    def notinrange(self, value):
        return query.NotInRange(self, value)
