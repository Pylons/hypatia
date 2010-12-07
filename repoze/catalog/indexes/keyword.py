from zope.interface import implements

from zope.index.keyword import KeywordIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

def _negate(assertion):
    def negation(self, value):
        not_indexed = self.not_indexed
        all_indexed = self._rev_index.keys()
        if len(not_indexed) == 0:
            all = self.family.IF.Set(all_indexed)
        elif len(all_indexed) == 0:
            all = not_indexed
        else:
            all_indexed = self.family.IF.Set(all_indexed)
            all = self.family.IF.union(not_indexed, all_indexed)
        positive = assertion(self, value)
        if len(positive) == 0:
            return all
        return self.family.IF.difference(all, positive)
    return negation


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

    def applyAny(self, values):
        return self.apply({'query': values, 'operator':'or'})

    applyIn = applyAny

    applyNotAny = _negate(applyAny)

    def applyAll(self, values):
        return self.apply({'query': values, 'operator':'and'})

    applyNotAll = _negate(applyAll)

    def applyEq(self, value):
        return self.apply(value)

    applyNotEq = _negate(applyEq)

