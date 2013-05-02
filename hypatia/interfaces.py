from zope.interface import (
    Interface,
    Attribute,
    )

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

    def sort(docids, reverse=False, limit=None, sort_type=None,
             raise_unsortable=True):
        """Sort document ids sequence using indexed values
        
        Return a sorted iterable of document ids. Limited by value of the
        'limit' argument and optionally reversed, using the 'reverse'
        argument.

        If ``sort_type`` is not ``None``, it should be the value
        :attr:`hypatia.interfaces.STABLE` to specify that the sort should be
        stable (see http://www.algorithmist.com/index.php/Stable_Sort) or
        :attr:`hypatia.interfaces.OPTIMAL` to specify that the sort should be
        done with the opmimal algorithm (which is not guaranteed to be stable).
        By default, the sort will be done using the optimal algorithm if
        ``sort_type`` is not :attr:`~hypatia.interfaces.STABLE``.

        If ``raise_unsortable`` is ``True`` (the default), if the index cannot
        resolve any of the docids in the set of docids in this result set, a
        :exc:`hypatia.exc.Unsortable` exception will be raised during iteration
        over the sorted docids.  If ``raise_unsortable`` is ``False``, if some
        of docids are not indexed they are skipped from resulting iterable.
        """

class ICatalog(IIndexInjection):
    """ Dictionary-like object which maps index names to index instances.
    Also supports the IIndexInjection interface."""

class ICatalogQuery(Interface):
    def __call__(queryobject, sort_index=None, limit=None, sort_type=None,
                 reverse=False, names=None):
        """Search the catalog using the query and options provided.  """

class IResultSet(Interface):
    """ Iterable sequence of documents or document identifiers."""

    ids = Attribute('An iterable sequence of document identifiers')

    resolver = Attribute(
        'A callable which accepts a document id and which returns a document.  '
        'May be ``None``, in which case, resolution performed by result set '
        'methods is not performed, and document identifiers are returned '
        'unresolved.'
        )

    def __len__():
        """ Return the length of the result set"""

    def sort(index, reverse=False, limit=None, sort_type=None,
             raise_unsortable=True):
        """Return another IResultSet sorted using the ``index`` (an IIndexSort)
        passed to it after performing the sort using the index and the
        ``limit``, ``reverse``, and ``sort_type`` parameters.

        If ``sort_type`` is not ``None``, it should be the value
        :attr:`hypatia.interfaces.STABLE` to specify that the sort should be
        stable or :attr:`hypatia.interfaces.OPTIMAL` to specify that the sort
        algorithm chosen should be optimal (but not necessarily stable).  It's
        usually unnecessary to pass this value, even if you're resorting an
        already-sorted set of docids, because the implementation of IResultSet
        will internally ensure that subsequent sorts of the returned result set
        of an initial sort will be stable; if you don't want this behavior,
        explicitly pass :attr:`hypatia.interfaces.OPTIMAL` on the second and
        subsequent sorts of a set of docids.

        If ``raise_unsortable`` is ``True`` (the default), if the index cannot
        resolve any of the docids in the set of docids in this result set, a
        :exc:`hypatia.exc.Unsortable` exception will be raised during iteration
        over the sorted docids.
        """

    def first(resolve=True):
        """ Return the first element in the sequence.  If ``resolve`` is True,
        and the result set has a valid resolver, return the resolved
        document, otherwise return the document id of the first document. """

    def one(resolve=True):
        """ Return the element in the resultset, asserting that there is only
        one result.  If the resultset has more than one element, raise an
        :exc:`hypatia.exc.MultipleResults` exception.  If the resultset has no
        elements, raise an :ex:`hypatia.exc.NoResults` exception. `If
        ``resolve`` is True, and the result set has a valid resolver, return
        the resolved document, otherwise return the document id of the
        document."""

    def all(resolve=True):
        """ Return a sequence representing all elements in the resultset.  `If
        ``resolve`` is True, and the result set has a valid resolver, return an
        iterable of the resolved documents, otherwise return an iterable
        containing the document id of each document."""

    def __iter__():
        """ Return an iterator over the results of ``self.all()``"""
        
FWSCAN = 'fwscan'
NBEST = 'nbest'
TIMSORT = 'timsort'
STABLE = 'stable'
OPTIMAL = 'optimal'
