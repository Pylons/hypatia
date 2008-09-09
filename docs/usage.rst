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
       
Here's a more complicated example of indexing data into a catalog
within your application, which uses callbacks to adapt cataloged
objects to values rather than directly inspecting attributes of the
content object.  We use the same types of indexes, but we set up
callbacks that allow us to adapt content to a result instead of
exmaining the object for an attribute directly.  This is useful in the
case that your content objects don't have attributes that match
exactly what you want to index:

.. literalinclude:: code/index_callbacks.py
   :linenos:
   :language: python
  
Searching
---------

Searching for values from a previously indexed corpus of content is
significantly easier than indexing.  We pass a query into our
catalog's ``searchResults`` method, which is composed of the name of
our index and a value we'd like to find a document for.

.. code-block:: python
   :linenos:

   from repoze.catalog.catalog import FileStorageCatalogFactory
   from repoze.catalog.catalog import ConnectionManager

   factory = FileStorageCatalogFactory('catalog.db', 'mycatalog')
   manager = ConnectionManager()
   catalog = factory(manager)
   numdocs, results = catalog.searchResults(flavors=('peach', 'peach'))
   print (numdocs, [ x for x in results ])

The results of the above search will search the corpus for documents
which have a result in the ``flavor`` index that matches the value
``peach``.  Since the index is a "field" index, its query arguments
are a "range" search: you can read ``('peach', 'peach')`` as "from
peach to peach".  You could say ``('peach', 'pistachio')`` to find all
documents that are in the "range" from peach to pistachio.

This particular query will return a two-tuple, with the first element
in the sequence being the length of the result set, and the second
element being the result set itself, which is only guaranteed to be an
interable (not any particular type, and *not* always sliceable; it may
be a generator).  Our above example would print.

  (1, [1])

The second element is the result set.  It has one item.  This item is
the document id for the content we indexed in the above step with
``peach`` as a ``flavors`` value.  Your application is responsible for
resolving this unique identifier back to its constituent content.

You can also pass compound search parameters for multiple indexes.
The results are intersected to provide a result:

.. code-block:: python
   :linenos:

   from repoze.catalog.catalog import FileStorageCatalogFactory
   from repoze.catalog.catalog import ConnectionManager

   factory = FileStorageCatalogFactory('catalog.db', 'mycatalog')
   manager = ConnectionManager()
   catalog = factory(manager)
   numdocs, results = catalog.searchResults(flavors=('peach', 'peach'), texts='nutty')
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

   numdocs, results = catalog.searchResults(flavors=('peach', 'pistachio'),
                                            sort_index='flavors')
   print (numdocs, [ x for x in results ])
   (2, [1, 2])

The default sort order is ascending.  You can reverse the sort using
``sort_descending``::

   numdocs, results = catalog.searchResults(flavors=('peach', 'pistachio'),
                                            sort_index='flavors', 
                                            sort_descending=True)
   print (numdocs, [ x for x in results ])
   (2, [2, 1])

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
