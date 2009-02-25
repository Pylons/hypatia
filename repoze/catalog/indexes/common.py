from persistent import Persistent
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

    def index_doc(self, docid, object):
        if callable(self.discriminator):
            value = self.discriminator(object, _marker)
        else:
            value = getattr(object, self.discriminator, _marker)

        if value is _marker:
            # unindex the previous value
            super(CatalogIndex, self).unindex_doc(docid)
            return None

        if isinstance(value, Persistent):
            raise ValueError('Catalog cannot index persistent object %s' %
                             value)

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
