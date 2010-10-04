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

# queries

class IQuery(Interface):
    """Search query."""

    def apply():
        """Apply query with predefined query value."""


class ITextQuery(IQuery):
    """Text index query."""

    def __init__(index_name, value):
        """Query signature."""


class IEqQuery(IQuery):
    """Equal query."""

    def __init__(index_name, value):
        """Query signature."""


class INotEqQuery(IQuery):
    """Not equal query."""

    def __init__(index_name, not_value):
        """Query signature."""


class IBetweenQuery(IQuery):
    """Between query."""

    def __init__(index_name, min_value, max_value):
        """Query signature."""


class IGeQuery(IQuery):
    """Greater query."""

    def __init__(index_name, min_value):
        """Query signature."""


class ILeQuery(IQuery):
    """Less query."""

    def __init__(index_name, max_value):
        """Query signature."""


class IInQuery(IQuery):
    """In query."""

    def __init__(index_name, values):
        """Query signature."""


class ISearchQuery(Interface):
    """Chainable search query."""

    def __init__(query=None, family=None):
        """Initialize with none or existing query."""

    results = Attribute("""List of record ids.""")

    def apply():
        """Return iterable search result wrapper."""

    def searchResults(intids=None, searchResultFactory=None, sort_index=None, reverse=False, limit=None):
        """Returns an iterable search result objects.

        The IntIds utility can be specified for use in the ResulSet using the ``intids`` argument.
        
        The ``searchResultFactory`` argument can be used to specify a factory
        for the ResultSet object, returned by this method.
        
        The name of index to sort results with can be specified using the
        ``sort_index`` argument. The index should provide the
        zope.index.interfaces.IIndexSort interface. The optional ``reverse``
        and ``limit`` argument will be used by the index for efficient sorting.
        
        Though the ``limit`` and ``reverse`` arguments can be used without the
        ``sort_index``, it doesn't make much sense, because we can't guarantee
        any particular order in unsorted result set.

        """

    def Or(query):
        """Enhance search results. (union)

        The result will contain intids which exist in the existing result 
        and/or in the result from te given query.
        """

    def And(query):
        """Restrict search results. (intersection)

        The result will only contain intids which exist in the existing
        result and in the result from te given query. (union)
        """

    def Not(query):
        """Exclude search results. (difference)

        The result will only contain intids which exist in the existing
        result but do not exist in the result from te given query.
        
        This is faster if the existing result is small. But note, it get 
        processed in a chain, results added after this query get added again. 
        So probably you need to call this at the end of the chain.
        """
