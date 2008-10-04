from repoze.catalog.catalog import FileStorageCatalogFactory
from repoze.catalog.catalog import ConnectionManager

from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.text import CatalogTextIndex

factory = FileStorageCatalogFactory('catalog.db', 'mycatalog')

class Content(object):
    def __init__(self, flavor, text):
        self.theflavor = flavor
        self.thetext = text

def get_flavor(object, default):
    return getattr(object, 'theflavor', default)

def get_text(object, default):
    return getattr(object, 'thetext', default)

_initialized = False

def initialize_catalog():
    global _initialized
    if not _initialized:
        # create a catalog
        manager = ConnectionManager()
        catalog = factory(manager)
        # set up indexes
        catalog['flavors'] = CatalogFieldIndex(get_flavor)
        catalog['text'] = CatalogTextIndex(get_text)
        # commit the indexes
        manager.commit()
        manager.close()
        _initialized = True

if __name__ == '__main__':
    initialize_catalog()
    manager = ConnectionManager()
    catalog = factory(manager)
    content = {
         1:Content('peach', 'i am so very very peachy'),
         2:Content('pistachio', 'i am nutty'),
         }
    for docid, doc in content.items():
        catalog.index_doc(docid, doc)
    manager.commit()
