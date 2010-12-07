from zope.interface import Interface
from zope.interface import Attribute

from zope.index.interfaces import IInjection
from zope.index.interfaces import IIndexSearch

class ICatalog(IIndexSearch, IInjection):
    def search(**query):
        """Search on the query provided.  Each query key is an index
        name, each query value is the value that the index expects as
        a query term."""

class ICatalogIndex(IIndexSearch, IInjection):
    """ An index that adapts objects to an attribute or callable value
    on an object """
    def apply_intersect(query, docids):
        """ Run the query implied by query, and return query results
        intersected with the ``docids`` set that is supplied.  If
        ``docids`` is None, return the bare query results. """

    def reindex_doc(docid, obj):
        """ Reindex the document numbered ``docid`` using in the
        information on object ``obj``"""

class ICatalogAdapter(Interface):
    def __call__(default):
        """ Return the value or the default if the object no longer
        has any value for the adaptation"""
