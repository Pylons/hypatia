from persistent import Persistent
from ZODB.broken import Broken
import BTrees

_marker = ()


class CatalogIndex(object):
    """ Abstract class for interface-based lookup """

    family = BTrees.family32

    def __init__(self, discriminator):
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        self.not_indexed = self.family.IF.Set()

    def index_doc(self, docid, object):
        if callable(self.discriminator):
            value = self.discriminator(object, _marker)
        else:
            value = getattr(object, self.discriminator, _marker)

        if value is _marker:
            # unindex the previous value
            super(CatalogIndex, self).unindex_doc(docid)

            # Store docid in set of unindexed docids
            self.not_indexed.add(docid)

            return None

        if isinstance(value, Persistent):
            raise ValueError('Catalog cannot index persistent object %s' %
                             value)

        if isinstance(value, Broken):
            raise ValueError('Catalog cannot index broken object %s' %
                             value)

        if docid in self.not_indexed:
            # Remove from set of unindexed docs if it was in there.
            self.not_indexed.remove(docid)

        return super(CatalogIndex, self).index_doc(docid, value)

    def reindex_doc(self, docid, object):
        """ Default reindex_doc implementation """
        self.unindex_doc(docid)
        self.index_doc(docid, object)

    def apply_intersect(self, query, docids):
        """ Default apply_intersect implementation """
        result = self.apply(query)
        if docids is None:
            return result
        return self.family.IF.weightedIntersection(result, docids)[1]

    def applyContains(self, *args, **kw):
        raise NotImplementedError(
            "Contains is not supported for %s" % type(self).__name__)

    def applyDoesNotContain(self, *args, **kw):
        raise NotImplementedError(
            "DoesNotContain is not supported for %s" % type(self).__name__)

    def applyEq(self, *args, **kw):
        raise NotImplementedError(
            "Eq is not supported for %s" % type(self).__name__)

    def applyNotEq(self, *args, **kw):
        raise NotImplementedError(
            "NotEq is not supported for %s" % type(self).__name__)

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
        raise NotImplementedError(
            "NotAny is not supported for %s" % type(self).__name__)

    def applyAll(self, *args, **kw):
        raise NotImplementedError(
            "All is not supported for %s" % type(self).__name__)

    def applyRange(self, *args, **kw):
        raise NotImplementedError(
            "Range is not supported for %s" % type(self).__name__)

    def avg_result_len_eq(self):
        return None

    avg_result_len_contains = avg_result_len_eq
    avg_result_len_not_eq = avg_result_len_eq
    avg_result_len_gt = avg_result_len_eq
    avg_result_len_lt = avg_result_len_eq
    avg_result_len_ge = avg_result_len_eq
    avg_result_len_le = avg_result_len_eq
    avg_result_len_any = avg_result_len_eq
    avg_result_len_all = avg_result_len_eq
    avg_result_len_range = avg_result_len_eq
