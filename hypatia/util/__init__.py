import BTrees

from persistent import Persistent
from ZODB.broken import Broken

_marker = ()

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

    def docids(self):
        not_indexed = self.not_indexed()
        indexed = self.indexed()
        if len(not_indexed) == 0:
            return self.family.IF.Set(indexed)
        elif len(indexed) == 0:
            return not_indexed
        indexed = self.family.IF.Set(indexed)
        return self.family.IF.union(not_indexed, indexed)

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

    def applyContains(self, *args, **kw):
        raise NotImplementedError(
            "Contains is not supported for %s" % type(self).__name__)

    def applyDoesNotContain(self, *args, **kw):
        return self._negate(self.applyContains, *args, **kw)

    def applyEq(self, *args, **kw):
        raise NotImplementedError(
            "Eq is not supported for %s" % type(self).__name__)

    def applyNotEq(self, *args, **kw):
        return self._negate(self.applyEq, *args, **kw)

    def applyGt(self, *args, **kw):
        raise NotImplementedError(
            "Gt is not supported for %s" % type(self).__name__)

    def applyLt(self, *args, **kw):
        raise NotImplementedError(
            "Lt is not supported for %s" % type(self).__name__)

    def applyGe(self, *args, **kw):
        raise NotImplementedError(
            "Ge is not supported for %s" % type(self).__name__)

    def applyLe(self, *args, **kw):
        raise NotImplementedError(
            "Le is not supported for %s" % type(self).__name__)

    def applyAny(self, *args, **kw):
        raise NotImplementedError(
            "Any is not supported for %s" % type(self).__name__)

    def applyNotAny(self, *args, **kw):
        return self._negate(self.applyAny, *args, **kw)

    def applyAll(self, *args, **kw):
        raise NotImplementedError(
            "All is not supported for %s" % type(self).__name__)

    def applyNotAll(self, *args, **kw):
        return self._negate(self.applyAll, *args, **kw)

    def applyInRange(self, *args, **kw):
        raise NotImplementedError(
            "InRange is not supported for %s" % type(self).__name__)

    def applyNotInRange(self, *args, **kw):
        return self._negate(self.applyInRange, *args, **kw)


    
