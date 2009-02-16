from zope.interface import implements

from zope.index.text import TextIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

class CatalogTextIndex(CatalogIndex, TextIndex):
    implements(ICatalogIndex)
    def reindex_doc(self, docid, object):
        # index_doc knows enough about reindexing to do the right thing
        return self.index_doc(docid, object)

