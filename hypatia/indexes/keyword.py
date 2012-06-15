from zope.interface import implementer

from zope.index.keyword import KeywordIndex

from ..interfaces import ICatalogIndex
from .common import CatalogIndex


@implementer(ICatalogIndex)
class CatalogKeywordIndex(CatalogIndex, KeywordIndex):
    """
    Keyword index.

    Query types supported:

    - Eq

    - NotEq

    - In

    - NotIn

    - Any

    - NotAny

    - All

    - NotAll

    """

    def __init__(self, discriminator, family=None):
        if family is not None:
            self.family = family
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        self._not_indexed = self.family.IF.TreeSet()
        self.clear()

    def reindex_doc(self, docid, value):
        # the base index' index_doc method special-cases a reindex
        return self.index_doc(docid, value)

    def _indexed(self):
        return self._rev_index.keys()

    def applyAny(self, values):
        return self.apply({'query': values, 'operator': 'or'})

    applyIn = applyAny

    def applyAll(self, values):
        return self.apply({'query': values, 'operator': 'and'})

    def applyEq(self, value):
        return self.apply([value])
