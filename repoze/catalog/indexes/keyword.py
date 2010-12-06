from zope.interface import implements

from zope.index.keyword import KeywordIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

class CatalogKeywordIndex(CatalogIndex, KeywordIndex):
    """
    Keyword index.

    Query types supported:

    - Eq

    - NotEq

    - In

    - Any

    - All

    """
    implements(ICatalogIndex)

    def __init__(self, discriminator):
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        self.not_indexed = self.family.IF.Set()
        self.clear()

    def reindex_doc(self, docid, value):
        # the base index' index_doc method special-cases a reindex
        return self.index_doc(docid, value)

    def _get_all_docids(self):
        indexed = self._rev_index.keys()
        not_indexed = self.not_indexed
        if len(indexed) == 0:
            return not_indexed
        indexed = self.family.IF.Set(indexed)
        if len(not_indexed) == 0:
            return indexed
        return self.family.IF.union(indexed, not_indexed)

    def applyAny(self, values):
        return self.apply({'query': values, 'operator':'or'})

    applyIn = applyAny

    def applyAll(self, values):
        return self.apply({'query': values, 'operator':'and'})

    def applyEq(self, value):
        return self.apply(value)

    def applyNotEq(self, not_value):
        all = self._get_all_docids()
        r = self.apply(not_value)
        return self.family.IF.difference(all, r)

