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

.. literalinclude:: code/index_interfaces.py
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

   factory = FileStorageCatalogFactory('catalog.db', 'mycatalog')

   if __name__ == '__main__':
       manager = ConnectionManager()
       catalog = factory(manager)
       results = catalog.searchResults(flavor='peach')
       print results

The results of the above search will search the corpus for documents
which have a result in the ``flavor`` index that matches the value
``peach``.  This particular query will return a sequence, with one
result::

  [1]

This is the document id for the content we indexed in the above step
as 'peach'.  Your application is responsible for resolving this unique
identifier back to its constituent content.

You can also pass compound search parameters for multiple indexes.
The results are intersected to provide a result:

.. code-block:: python
   :linenos:

   factory = FileStorageCatalogFactory('catalog.db', 'mycatalog')

   if __name__ == '__main__':
       manager = ConnectionManager()
       catalog = factory(manager)
       results = catalog.searchResults(flavor='peach', text='pistachio')
       print results

The results of the above search will return the empty sequence,
because no results in our index match a document which has both a
flavor of 'peach' and text which contains the word 'pistachio'.

See the :term:`zope.index` documentation and implementation for more
information about special query parameters to indexes.

Restrictions
------------

Values indexed by a :mod:`repoze.bfg` catalog cannot subclass from the
ZODB ``Persistent`` class.  This is a safeguard to ensure that
irresolveable cross-database references aren't put into the catalog's
(separate) database.

Gotchas
-------

When the ``ConnectionManager`` 's ``commit`` method is called, it will
commit a transaction for all databases participating in Zope
transaction management.  Don't use this method if you already have
transaction management enabled in another way.
