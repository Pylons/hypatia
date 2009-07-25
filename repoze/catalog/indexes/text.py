from zope.interface import implements

from zope.index.interfaces import IIndexSort
from zope.index.text import TextIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

class CatalogTextIndex(CatalogIndex, TextIndex):
    implements(ICatalogIndex, IIndexSort)

    def __init__(self, discriminator, lexicon=None, index=None):
        if not callable(discriminator):
            if not isinstance(discriminator, basestring):
                raise ValueError('discriminator value must be callable or a '
                                 'string')
        self.discriminator = discriminator
        TextIndex.__init__(self, lexicon, index)
        self.clear()

    def reindex_doc(self, docid, object):
        # index_doc knows enough about reindexing to do the right thing
        return self.index_doc(docid, object)

    def sort(self, result, reverse=False, limit=None, sort_type=None):
        """Sort by text relevance.

        This only works if the query includes at least one text query,
        leading to a weighted result.  This method raises TypeError
        if the result is not weighted.

        A weighted result is a dictionary-ish object that has docids
        as keys and floating point weights as values.  This method
        sorts the dictionary by weight and returns the sorted
        docids as a list.
        """
        if not result:
            return result

        if not hasattr(result, 'items'):
            raise TypeError(
                "Unable to sort by relevance because the search "
                "result does not contain weights. To produce a weighted "
                "result, include a text search in the query.")

        items = [(weight, docid) for (docid, weight) in result.items()]
        # when reverse is false, output largest weight first.
        # when reverse is true, output smallest weight first.
        items.sort(reverse=not reverse)
        result = [docid for (weight, docid) in items]
        if limit:
            result = result[:limit]
        return result
