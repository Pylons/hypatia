.. _usage:

Using :mod:`repoze.catalog`
===========================

:mod:`repoze.catalog` is an indexing and search system for Python.  It
is inspired by (and uses much code from) Zope's
:term:`zope.app.catalog`, and uses other :term:`Zope` libraries to do
much of its work.  It manages its own persistence: it stores catalog
information into a :term:`ZODB` database.

In order to make use of :mod:`repoze.catalog`, your application will
be required to create objects that are willing to be indexed, and it
will be responsible for providing each of these objects a unique
integer identifier, and maintaining the association between the object
and the unique identifier for the lifetime of your application.
Objects which are willing to be indexed must either have a particular
attribute which is guaranteed to have a value *or* you must provide a
callback that is willing to inspect the content for a value.

The result of searching a catalog is a sequence of integers that
represent all the document ids that match the query.  Your application
is responsible for being able to (re-) resolve these integers into
content objects.

Indexing
--------

Here's a simple example of indexing data within your application.
This example sets up two indexes.

The first index for ``flavor`` is a :term:`field index`.  The second
index, ``text``, is a :term:`text index`.

.. literalinclude:: code/index_attributes.py
   :linenos:
   :language: python

Here's a more complicated example.  It uses callbacks to adapt
cataloged objects to values rather than directly inspecting attributes
of the content object.  We use the same types of indexes as the
previous example, but we set up callbacks that allow us to adapt
content to a result instead of examining the object for an attribute
directly.  This is useful in the case that your content objects don't
have attributes that match exactly what you want to index:

.. literalinclude:: code/index_callbacks.py
   :linenos:
   :language: python

Searching
---------

Searching for values from a previously indexed corpus of content is
significantly easier than indexing.  There are a number of ways to
perform searches.

Search Using the :meth:`repoze.catalog.Catalog.query` Method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The suggested way to perform searches is to use the
:meth:`repoze.catalog.Catalog.query` method.  This method accepts a
number of arguments:

``queryobject``
   A query object or a string representing the query.

``sort_index``
   The name of the index used to sort the results.

``limit``
   Limit the number of results returned to this argument, which should be
   an integer.  This is only used if ``sort_index`` is also specified.

``reverse``
   Reverse the order of the result sequence if this is ``True``.  Only used
   if ``sort_index`` is also specified.

For example::

   from repoze.catalog.catalog import FileStorageCatalogFactory
   from repoze.catalog.catalog import ConnectionManager
   from repoze.catalog.query import Eq

   factory = FileStorageCatalogFactory('catalog.db', 'mycatalog')
   manager = ConnectionManager()
   catalog = factory(manager)
   numdocs, results = catalog.query(Eq('flavors', 'peach'))
   print (numdocs, [ x for x in results ])

The results of the above search will search the corpus for documents
which have a result in the ``flavor`` index that matches the value
``peach``.

The :meth:`repoze.catalog.Catalog.query` method will return a
two-tuple, with the first element in the sequence being the length of
the result set, and the second element being the result set
itself.  Our above example will print::

  (1, [1])

The first element in the tuple is the length of the result set (the
integer ``1``, in this case).

The second element in the tuple is the result set.  It has one item.
This item is the document id for the content we indexed.  Your
application is responsible for resolving this document identifier back
to its constituent content.

.. warning:: The result set is only guaranteed to be an iterable.  It
   will always be of a particular type, and *not* always sliceable;
   for example it may be a generator.

You can also combine query objects, using boolean operations, to search
multiple indexes:

.. code-block:: python
   :linenos:

   from repoze.catalog.catalog import FileStorageCatalogFactory
   from repoze.catalog.catalog import ConnectionManager

   factory = FileStorageCatalogFactory('catalog.db', 'mycatalog')
   manager = ConnectionManager()
   catalog = factory(manager)
   numdocs, results = catalog.query(
                          Eq('flavors', 'peach') & Eq('texts', 'nutty'))
   print (numdocs, [ x for x in results ])

The results of the above search will return the following::

   (0, [])

This is because no results in our index match a document which has
both a flavor of ``peach`` and text which contains the word ``nutty``.

You can sort the result set using ``sort_index``.  The value of
``sort_index`` should be the name of an index which supports being
used as a sort index::

   from repoze.catalog.query import Range

   numdocs, results = catalog.query(
                  Range('flavors', 'peach', 'pistachio'),
                  sort_index='flavors')
   print (numdocs, [ x for x in results ])

Would result in::

   (2, [1, 2])

The default sort order is ascending.  You can reverse the sort using
``reverse``::

   from repoze.catalog.query import Range

   numdocs, results = catalog.query(
                  Range('flavors', 'peach', 'pistachio'),
                  sort_index='flavors',
                  reverse=True)
   print (numdocs, [ x for x in results ])

Would result in::

   (2, [2, 1])

Query Objects
!!!!!!!!!!!!!

The value passed as the ``queryobject`` argument to
:meth:`repoze.catalog.Catalog.query` may be one of two distinct types:

- a "raw" :term:`query object`

- a "CQE" string representing a domain-specific-language expression
  which will be used to *generate* a :term:`query object`.  "CQE"
  stands for "catalog query expression".

For example, you can construct a raw query object using Python, and
pass it as ``queryobject`` to the :meth:`repoze.catalog.Catalog.query`
method:

.. code-block:: python
   :linenos:

   from repoze.catalog.query import Eq
   results = catalog.query(Eq('index_name', 'value'))

Or you can allow repoze.catalog to construct a query object on your
behalf by passing a *string* as ``queryobject``.

.. code-block:: python
   :linenos:

   from repoze.catalog.query import Eq
   catalog.query('index_name == "value"')

The above string is a CQE.  A "CQE" is a string representing a Python
expression which uses index names and values.  It is parsed by the
catalog to create a query object.

.. warning:: CQE strings are not supported on Python versions < 2.6.

Whether a query object is used directly or query objects are generated
as the result of a CQE, an individual query object will be one of two
types: a comparator or a boolean operator.  A comparator performs a single
query on a single index.  A boolean operator allows results from
individual queries to be combined using boolean operations.  For example:

.. code-block:: python
   :linenos:

    from repoze.catalog.query import And, Eq, Contains
    query = And(Eq('author', 'crossi'), Contains('body', 'biscuits'))

In the above example, ``And`` is a boolean operator, and both ``Eq`` and
``Contains`` are comparison operators. The resulting query will search two
indexes, ``author`` and ``body``. Because the individual comparators are
passed as arguments to the ``And`` set operator, the result becomes all
documents which satisfy *both* comparators.

All query objects overload the bitwise and (``&``) and or (``|``) operators
and can be combined using these.  The above query could also have been written
as follows:

.. code-block:: python
   :linenos:

    query = Eq('author', 'crossi') & Contains('body', 'biscuits')

.. note:: Although it would be more intuitive to use the boolean operators,
   ``or`` and ``and`` for this rather than bitwise operators, Python does not
   allow overloading boolean operators.

Query objects may also be created by parsing a :term:`CQE` string.
The query parser uses Python's internal code parser to parse CQE query
expression strings, so the syntax is just like Python::

    mycatalog.query("author == 'crossi' and 'biscuits' in body")

The query parser allows name substitution in expressions.  Names are
resolved using a dict passed into
:meth:`repoze.catalog.Catalog.query`::

    author = request.params.get("author")
    word = request.params.get("search_term")
    query = mycatalog.query("author == author and word in body",
                            names=locals())

Unlike true Python expressions, ordering of the terms in a CQE
expression is important for comparators. For most comparators the
``index_name`` must be written on the left.  The following, for
example, would raise an exception::

    query = mycatalog.query("'crossi' == author")

Note that not all index types support all comparators. An attempt to
perform a query using a comparator that is not supported by the index
being queried will result in a NotImplementedError being raised when
the query is performed.

Comparators
!!!!!!!!!!!

The supported comparator operators are as follows:

Equal To
########

Python::

   from repoze.catalog.query import Eq
   Eq(index_name, value)

CQE::

   index_name == value

Not Equal To
############

Python::

   from repoze.catalog.query import NotEq
   NotEq(index_name, value)

CQE::

   index_name != value

Greater Than
############

Python::

   from repoze.catalog.query import Gt
   Gt(index_name, value)

CQE::

   index_name > value

Less Than
#########

Python::

   from repoze.catalog.query import Lt
   Lt(index_name, value)

CQE::

   index_name < value

Greater Than Or Equal To
########################

Python::

   from repoze.catalog.query import Ge
   Ge(index_name, value)

CQE::

   index_name >= value

Less Than Or Equal To
#####################

Python::

   from repoze.catalog.query import Ge
   Le(index_name, value)

CQE::

   index_name <= value

Contains
########

Python::

   from repoze.catalog.query import Contains
   Contains(index_name, value)

CQE::

   value in index_name

Does Not Contain
################

Python::

   from repoze.catalog.query import DoesNotContain
   DoesNotContain(index_name, value)

CQE::

   value not in index_name

Any
###

Python::

   from repoze.catalog.query import Any
   Any(index_name, [value1, value2, ...])

CQE::

   index_name == value1 or index_name == value2 or etc...
   index_name in any([value1, value2, ...])
   index_name in any(values)

Not Any (aka None Of)
#####################

Python::

   from repoze.catalog.query import NotAny
   NotAny(index_name, [value1, value2, ...])

CQE::

   index_name != value1 and index_name != value2 and etc...
   index_name not in any([value1, value2, ...])
   index_name not in any(values)

All
###

Python::

   from repoze.catalog.query import All
   All(index_name, [value1, value2, ...])

CQE::

   index_name == value1 and index_name == value2 and etc...
   index_name in all([value1, value2, ...])
   index_name in all(values)

Not All
#######

Python::

   from repoze.catalog.query import NotAll
   NotAll(index_name, [value1, value2, ...])

CQE::

   index_name != value1 or index_name != value2 or etc...
   index_name not in all([value1, value2, ...])
   index_name not in all(values)

Within Range
############

Python::

   from repoze.catalog.query import InRange
   InRange(index_name, start, end,
         start_exclusive=False, end_exclusive=False)

CQE::

   index_name >= start and index_name <= end
   start < index_name < end

Not Within Range
################

Python::

   from repoze.catalog.query import NotInRange
   NotInRange(index_name, start, end,
         start_exclusive=False, end_exclusive=False)

CQE::

   index_name <= start or index_name >= end
   not(start < index_name < end)

Boolean Operators
!!!!!!!!!!!!!!!!!

The following set operators are allowed in queries:

And
###

Python (explicit)::

   from repoze.catalog.query import And
   And(query1, query2)

Python (implicit)::

   query1 & query2

CQE::

    query1 and query2
    query1 & query2

Or
##

Python (explicit)::

   from repoze.catalog.query import Or
   Or(query1, query2)

Python (implicit)::

   query1 | query2

CQE::

    query1 or query2
    query1 | query2

Not
###

Python (explicit)::

   from repoze.catalog.query import Not
   Not(query1, query2)

CQE::

   not query1

Search Using the :meth:`repoze.catalog.Catalog.search` Method (Deprecated)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning:: The :meth:`repoze.catalog.Catalog.search` method is
   deprecated as of :mod:`repoze.catalog` 0.8.  Use
   :meth:`repoze.catalog.Catalog.query` instead.

We can pass a query into our catalog's ``search`` method, which is
composed of the name of our index and a value we'd like to find a
document for.

.. code-block:: python
   :linenos:

   from repoze.catalog.catalog import FileStorageCatalogFactory
   from repoze.catalog.catalog import ConnectionManager

   factory = FileStorageCatalogFactory('catalog.db', 'mycatalog')
   manager = ConnectionManager()
   catalog = factory(manager)
   numdocs, results = catalog.search(flavors=('peach', 'peach'))
   print (numdocs, [ x for x in results ])

The results of the above search will search the corpus for documents
which have a result in the ``flavor`` index that matches the value
``peach``.  Since the index is a "field" index, its query arguments
are a "range" search: you can read ``('peach', 'peach')`` as "from
peach to peach".  You could say ``('peach', 'pistachio')`` to find all
documents that are in the "range" from peach to pistachio.

The :meth:`repoze.catalog.Catalog.search` method will return a
two-tuple, with the first element in the sequence being the length of
the result set, and the second element being the result set itself.
Our above example will print:

  (1, [1])

The first element in the tuple is the length of the result set (the
integer ``1``, in this case).

The second element in the tuple is the result set.  It has one item.
This item is the document id for the content we indexed.  Your
application is responsible for resolving this document identifier back
to its constituent content.

You can also pass compound search parameters for multiple indexes.
The results are intersected to provide a result:

.. code-block:: python
   :linenos:

   from repoze.catalog.catalog import FileStorageCatalogFactory
   from repoze.catalog.catalog import ConnectionManager

   factory = FileStorageCatalogFactory('catalog.db', 'mycatalog')
   manager = ConnectionManager()
   catalog = factory(manager)
   numdocs, results = catalog.search(flavors=('peach', 'peach'), texts='nutty')
   print (numdocs, [ x for x in results ])

The results of the above search will return the following:

   (0, [])

This is because no results in our index match a document which
has both a flavor of ``peach`` and text which contains the word
``nutty``.

See the :term:`zope.index` documentation and implementation for more
information about what specific index types expect for query
parameters.

You can also use a field index as a ``sort_index``, which sorts the
document ids based on the values for that docid present in that index::

   numdocs, results = catalog.search(flavors=('peach', 'pistachio'),
                                            sort_index='flavors')
   print (numdocs, [ x for x in results ])
   (2, [1, 2])

The default sort order is ascending.  You can reverse the sort using
``reverse``::

   numdocs, results = catalog.search(flavors=('peach', 'pistachio'),
                                     sort_index='flavors',
                                     reverse=True)
   print (numdocs, [ x for x in results ])
   (2, [2, 1])

If you use a sort index, you may choose to limit the number of results
returned.  Do this by passing ``limit`` with an integer value of the
number of results you want.  Note that this parameter has no effect if
you do not supply a ``sort_index``::

   numdocs, results = catalog.search(flavors=('peach', 'pistachio'),
                                     sort_index='flavors',
                                     limit=1)
   print (numdocs, [ x for x in results ])
   (1, [1])

You may combine ``reverse`` and ``limit`` as necessary.

If a sort_index is used, and the sort index you're using does not
contain all the documents returned by the search, the ``numdocs``
value returned by ``search`` may be incorrect.  There will be fewer
results than those indicated by ``numdocs`` in this circumstance.

When querying a text index, to sort the results by relevance, specify
the name of the text index as the sort index.  The most relevant
results will be provided first, unless you specify reverse=True, in
which case the least relevant will be provided first.

Document Map
------------

An implementation of a "document map" suitable for ZODB applications
exists within the ``repoze.bfg.document.DocumentMap`` class.  A
document map allows you to map document ids to "addresses" (e.g. paths
or unique identifiers).  See :ref:`api_document_section` in the API
documentation chapter for more information.

Restrictions
------------

Values indexed by a :mod:`repoze.catalog` catalog cannot subclass from the
ZODB ``Persistent`` class.  This is a safeguard to ensure that
irresolveable cross-database references aren't put into the catalog's
(separate) database.

Gotchas
-------

When the ``ConnectionManager`` 's ``commit`` method is called, it will
commit a transaction for all databases participating in Zope
transaction management.  Don't use this method if you already have
transaction management enabled in another way.
