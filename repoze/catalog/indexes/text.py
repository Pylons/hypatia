from zope.interface import implements

from zope.index.text import TextIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

class CatalogTextIndex(CatalogIndex, TextIndex):
    implements(ICatalogIndex)

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
