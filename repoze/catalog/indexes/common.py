from persistent import Persistent

_marker = ()

class CatalogIndex(object):
    """ Abstract class for interface-based lookup """

    def __init__(self, discriminator, *args, **kwargs):
        super(CatalogIndex, self).__init__(*args, **kwargs)
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
