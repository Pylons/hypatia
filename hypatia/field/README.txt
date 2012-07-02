Field Indexes
=============

Field indexes index orderable values.  Note that they don't check for
orderability. That is, all of the values added to the index must be
orderable together. It is up to applications to provide only mutually
orderable values.

    >>> from hypatia.indexes.field import FieldIndex

    >>> index = FieldIndex()
    >>> index.index_doc(0, 6)
    >>> index.index_doc(1, 26)
    >>> index.index_doc(2, 94)
    >>> index.index_doc(3, 68)
    >>> index.index_doc(4, 30)
    >>> index.index_doc(5, 68)
    >>> index.index_doc(6, 82)
    >>> index.index_doc(7, 30)
    >>> index.index_doc(8, 43)
    >>> index.index_doc(9, 15)

Field indexes are searched with apply.  The argument is a tuple
with a minimum and maximum value:

    >>> index.apply((30, 70))
    IFSet([3, 4, 5, 7, 8])

A common mistake is to pass a single value.  If anything other than a 
two-tuple is passed, a type error is raised:

    >>> index.apply('hi')
    Traceback (most recent call last):
    ...
    TypeError: ('two-length tuple expected', 'hi')


Open-ended ranges can be provided by provinding None as an end point:

    >>> index.apply((30, None))
    IFSet([2, 3, 4, 5, 6, 7, 8])

    >>> index.apply((None, 70))
    IFSet([0, 1, 3, 4, 5, 7, 8, 9])

    >>> index.apply((None, None))
    IFSet([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

To do an exact value search, supply equal minimum and maximum values:

    >>> index.apply((30, 30))
    IFSet([4, 7])

    >>> index.apply((70, 70))
    IFSet([])

Field indexes support basic statistics:

    >>> index.indexed_count()
    10
    >>> index.word_count()
    8

Documents can be reindexed:

    >>> index.apply((15, 15))
    IFSet([9])
    >>> index.index_doc(9, 14)

    >>> index.apply((15, 15))
    IFSet([])
    >>> index.apply((14, 14))
    IFSet([9])
    
Documents can be unindexed:

    >>> index.unindex_doc(7)
    >>> index.indexed_count()
    9
    >>> index.word_count()
    8
    >>> index.unindex_doc(8)
    >>> index.indexed_count()
    8
    >>> index.word_count()
    7

    >>> index.apply((30, 70))
    IFSet([3, 4, 5])

Unindexing a document id that isn't present is ignored:

    >>> index.unindex_doc(8)
    >>> index.unindex_doc(80)
    >>> index.indexed_count()
    8
    >>> index.word_count()
    7

We can also clear the index entirely:

    >>> index.clear()
    >>> index.indexed_count()
    0
    >>> index.word_count()
    0

    >>> index.apply((30, 70))
    IFSet([])

Sorting
-------

Field indexes also implement IIndexSort interface that
provides a method for sorting document ids by their indexed
values.

    >>> index.index_doc(1, 9)
    >>> index.index_doc(2, 8)
    >>> index.index_doc(3, 7)
    >>> index.index_doc(4, 6)
    >>> index.index_doc(5, 5)
    >>> index.index_doc(6, 4)
    >>> index.index_doc(7, 3)
    >>> index.index_doc(8, 2)
    >>> index.index_doc(9, 1)

    >>> list(index.sort([4, 2, 9, 7, 3, 1, 5]))
    [9, 7, 5, 4, 3, 2, 1]

We can also specify the ``reverse`` argument to reverse results:

    >>> list(index.sort([4, 2, 9, 7, 3, 1, 5], reverse=True))
    [1, 2, 3, 4, 5, 7, 9]

And as per IIndexSort, we can limit results by specifying the ``limit``
argument:

    >>> list(index.sort([4, 2, 9, 7, 3, 1, 5], limit=3)) 
    [9, 7, 5]

If we pass an id that is not indexed by this index, it won't be included
in the result.

    >>> list(index.sort([2, 10]))
    [2]

    >>> index.clear()

Bugfix testing:
---------------
Happened at least once that the value dropped out of the forward index,
but the index still contains the object, the unindex broke

    >>> index.index_doc(0, 6)
    >>> index.index_doc(1, 26)
    >>> index.index_doc(2, 94)
    >>> index.index_doc(3, 68)
    >>> index.index_doc(4, 30)
    >>> index.index_doc(5, 68)
    >>> index.index_doc(6, 82)
    >>> index.index_doc(7, 30)
    >>> index.index_doc(8, 43)
    >>> index.index_doc(9, 15)
    
    >>> index.apply((None, None))
    IFSet([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

Here is the damage:

    >>> del index._fwd_index[68]
    
Unindex should succeed:
    
    >>> index.unindex_doc(5)
    >>> index.unindex_doc(3)
    
    >>> index.apply((None, None))
    IFSet([0, 1, 2, 4, 6, 7, 8, 9])


Optimizations
-------------

There is an optimization which makes sure that nothing is changed in the
internal data structures if the value of the ducument was not changed.

To test this optimization we patch the index instance to make sure unindex_doc
is not called.

    >>> def unindex_doc(doc_id):
    ...     raise KeyError
    >>> index.unindex_doc = unindex_doc

Now we get a KeyError if we try to change the value.

    >>> index.index_doc(9, 14)
    Traceback (most recent call last):
    ...
    KeyError

Leaving the value unchange doesn't call unindex_doc.

    >>> index.index_doc(9, 15)
    >>> index.apply((15, 15))
    IFSet([9])

