from zope.interface import implements

from zope.index.text import TextIndex

from repoze.catalog.interfaces import ICatalogIndex
from repoze.catalog.indexes.common import CatalogIndex

class CatalogTextIndex(CatalogIndex, TextIndex):
    implements(ICatalogIndex)

