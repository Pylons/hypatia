from zope.interface import Interface

class IIndexInjection(Interface):
    """Interface for injecting documents into an index."""

    def index_doc(docid, value):
        """Add a document to the index.

        docid: int, identifying the document

        value: the (undiscriminated) value to be indexed

        return: None

        This can also be used to reindex documents.
        """

    def unindex_doc(docid):
        """Remove a document from the index.

        docid: int, identifying the document

        return: None

        This call is a no-op if the docid isn't in the index, however,
        after this call, the index should have no references to the docid.
        """

    def reindex_doc(docid, value):
        """Reindex a document using the (undiscriminated) value"""

    def reset():
        """Unindex all documents indexed by the index
        """

class IIndexEnumeration(Interface):
    def not_indexed():
        """ Return the set of document ids for which this index's
        discriminator returned ``default`` during ``index_doc`` or
        ``reindex_doc``, indicating that the index configuration was
        uninterested in indexing the value."""

    def not_indexed_count():
        """Return the number of document ids currently not indexed.
        Logically equivalent to len(self.not_indexed())."""

    def indexed():
        """ Return the set of document ids for which this index's
        discriminator returned a non-default value during ``index_doc`` or
        ``reindex_doc``, indicating that the index configuration as
        interested in indexing the value."""

    def indexed_count():
        """Return the number of document ids currently indexed.  Logically
        equivalent to len(self.indexed())."""

    def docids():
        """ Return the set of document ids which have been reported to this
        index via its ``index_doc`` or ``reindex_doc`` method (including
        document ids which had values which were not indexed).  This is the
        logical union of sets returned by indexed() and not_indexed()."""

    def docids_count():
        """Return the number of document ids currently in the set of both
        indexed and not indexed.  Logically equivalent to
        len(self.docids())."""

class IIndexDisplay(Interface):
    def qname():
        """ Return a string suitable for representing the index's name """

    def document_repr(docid, default=None):
        """ Return an index-specific string representation for the docid value,
        or the default if no such docid exists in the index."""

class IIndex(IIndexInjection, IIndexEnumeration, IIndexDisplay):
    pass

class IIndexStatistics(Interface):
    """An index that provides statistical information about itself."""

    def word_count():
        """Return the number of words currently indexed."""

class IIndexSort(Interface):

    def sort(docids, reverse=False, limit=None):
        """Sort document ids sequence using indexed values
        
        If some of docids are not indexed they are skipped from resulting
        iterable.
        
        Return a sorted iterable of document ids. Limited by value of the
        'limit' argument and optionally reversed, using the 'reverse'
        argument.
        """

class ICatalog(IIndexInjection):
    """ Dictionary-like object which maps index names to index instances.
    Also supports the IIndexInjection interface."""

class ICatalogQuery(Interface):
    def __call__(queryobject, sort_index=None, limit=None, sort_type=None,
                 reverse=False, names=None):
        """Search the catalog using the query and options provided.  """

