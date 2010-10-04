from zope.interface import implements

from zope.index.keyword import KeywordIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

class CatalogKeywordIndex(CatalogIndex, KeywordIndex):
    implements(ICatalogIndex)

    def __init__(self, discriminator):
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        self.clear()

    def reindex_doc(self, docid, value):
        # the base index' index_doc method special-cases a reindex
        return self.index_doc(docid, value)

    def applyAnyOf(self, values):
        return self.apply({'query': values, 'operator':'or'})

    applyIn = applyAnyOf

    def applyAllOf(self, values):
        return self.apply({'query': values, 'operator':'and'})

    def applyEq(self, value):
        return self.apply(value)

    def applyNotEq(self, not_value):
        all = self.family.IF.multiunion(self._fwd_index.values())
        r = self.apply(not_value)
        return self.family.IF.difference(all, r)

