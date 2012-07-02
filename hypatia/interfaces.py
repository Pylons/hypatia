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

    def clear():
        """Unindex all documents indexed by the index
        """

class IIndexQuery(Interface):
    """ Interface expected to be implemented by indexes which support CQE
    queries """
    def applyContains(value):
        """ Used by query.Contains comparator """

    def applyDoesNotContain(value):
        """ Used by query.DoesNotContain comparator """ 

    def applyEq(value):
        """ Used by query.Eq comparator  """ 

    def applyNotEq(value):
        """ Used by query.NotEq comparator """ 

    def applyGt(min_value):
        """ Used by query.Gt comparator  """ 

    def applyLt(max_value):
        """ Used by query.Lt comparator  """ 

    def applyGe(min_value):
        """ Used by query.Ge comparator  """ 

    def applyLe(max_value):
        """ Used by query.Le comparator  """ 

    def applyAny(values):
        """ Used by query.Any comparator  """ 

    def applyNotAny(values):
        """ Used by query.NotAny comparator  """ 

    def applyAll(values):
        """ Used by query.All comparator  """ 

    def applyNotAll(values):
        """ Used by query.NotAll comparator  """ 

    def applyInRange(start, end, excludemin=False, excludemax=False):
        """ Used by query.InRange comparator  """ 

    def applyNotInRange(start, end, excludemin=False, excludemax=False):
        """ Used by query.NotInRange comparator  """

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

class IIndex(IIndexQuery, IIndexInjection, IIndexEnumeration):
    pass

class IIndexStatistics(Interface):
    """An index that provides statistical information about itself."""

    def word_count():
        """Return the number of words currently indexed."""

class IIndexSort(Interface):

    def sort(docids, reverse=False, limit=None):
        """Sort document ids sequence using indexed values
        
        If some of docids are not indexed they are skipped
        from resulting iterable.
        
        Return a sorted iterable of document ids. Limited by
        value of the "limit" argument and optionally
        reversed, using the "reverse" argument.
        """

class INBest(Interface):
    """Interface for an N-Best chooser."""

    def add(item, score):
        """Record that item 'item' has score 'score'.  No return value.

        The N best-scoring items are remembered, where N was passed to
        the constructor.  'item' can by anything.  'score' should be
        a number, and larger numbers are considered better.
        """

    def addmany(sequence):
        """Like "for item, score in sequence: self.add(item, score)".

        This is simply faster than calling add() len(seq) times.
        """

    def getbest():
        """Return the (at most) N best-scoring items as a sequence.

        The return value is a sequence of 2-tuples, (item, score), with
        the largest score first.  If .add() has been called fewer than
        N times, this sequence will contain fewer than N pairs.
        """

    def pop_smallest():
        """Return and remove the (item, score) pair with lowest score.

        If len(self) is 0, raise IndexError.

        To be cleaer, this is the lowest score among the N best-scoring
        seen so far.  This is most useful if the capacity of the NBest
        object is never exceeded, in which case  pop_smallest() allows
        using the object as an ordinary smallest-in-first-out priority
        queue.
        """

    def __len__():
        """Return the number of (item, score) pairs currently known.

        This is N (the value passed to the constructor), unless .add()
        has been called fewer than N times.
        """

    def capacity():
        """Return the maximum number of (item, score) pairs.

        This is N (the value passed to the constructor).
        """

class ICatalog(IIndexInjection):
    """ Dictionary-like object which maps index names to index instances.
    Also supports the IIndexInjection interface."""
    def clear_indexes():
        """ Call .clear on all member indexes """

class ICatalogQuery(Interface):
    def __call__(queryobject, sort_index=None, limit=None, sort_type=None,
              reverse=False, names=None):
        """Search the catalog using the query and options provided.  """

