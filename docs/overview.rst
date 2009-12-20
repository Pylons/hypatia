A Tour of :mod:`repoze.catalog`
===============================

All versions of Zope depend heavily on the Zope Object Database (ZODB).
Because ZODB is less a database and more a persistent object store (it
doesn't possess a query language; Python *is* its query language), it
has been necessary to create indexing and searching facilities for data
stored in ZODB.

The first iteration of searching and indexing for ZODB-based
applications (at least post-Principia, which had something named
Tabula, which I never actually used) was the ZCatalog.  The ZCatalog
was entirely tied to Zope2, and still remains in heavy use today
within Zope 2 applications such as Plone.

The second iteration was ``zope.app.catalog``, which was a ZCatalog
do-over for Zope 3 applications.

Neither of these searching and indexing packages are particularly easy
to use outside of a Zope application.  Each makes various assumptions
about the content objects that need indexing or the environment that
aren't appropriate for arbitrary applications.  For instance, ZCatalog
wants objects you want to catalog to have a ``getPhysicalPath`` method
which returns a "path".  An instance of ``zope.app.catalog`` makes the
assumption that that it's located within a Zope 3 "site" object within
a ZODB, and assumes that you want query result sets to be sets of
Python references to the original object you indexed.  In other words,
these packages assume too much to be maximally useful outside the
context in which they were developed.  `Repoze <http://repoze.org>`_ is
a project which has as a stated goal making it easier for non-Zope
Python developers to use Zope technologies outside Zope, so this
seemed like a natural thing to do under the Repoze flag.

:mod:`repoze.catalog` borrows heavily from ``zope.app.catalog`` and
depends wholly on the ``zope.index`` package for its index
implementations, but assumes less about how you want your indexing and
querying to behave.  In this spirit, you can index any Python object;
it needn't implement any particular interface except perhaps one you
define yourself conventionally.  :mod:`repoze.catalog` does less than
any of its predecessors, in order to make it more useful for arbitrary
Python applications.  Its implemented in terms of ZODB objects, and
the ZODB will store the derived index data, but it assumes little
else.  You should be able to use it in any Python application.  The
fact that it uses ZODB is ancillary: it's akin to Xapian using "flint"
or "quartz" backends.

Indexing
--------

To perform indexing of objects, you set up a catalog with some number
of indexes, each of which is capable of calling a callback function to
obtain data about an object being cataloged::

  from repoze.catalog.indexes.field import CatalogFieldIndex
  from repoze.catalog.indexes.text import CatalogTextIndex
  from repoze.catalog.catalog import Catalog

  def get_flavor(object, default):
      return getattr(object, 'flavor', default)

  def get_text(object, default):
      return getattr(object, 'text', default)

  catalog = Catalog()
  catalog['flavors'] = CatalogFieldIndex(get_flavor)
  catalog['text'] = CatalogTextIndex(get_text)

Note that ``get_flavor`` and ``get_text`` will be called for each
object you attempt to index.  Each of them attempts to grab an
attribute from the object being indexed, and returns a default if no
such attribute exists.

Once you've got a catalog set up, you can begin to index Python
objects (aka "documents")::

  class IceCream(object):
      def __init__(self, flavor, description):
          self.flavor = flavor
          self.description = description

  peach = IceCream('peach', 'This ice cream has a peachy flavor')
  catalog.index_doc(1, peach)

  pistachio = IceCream('pistachio', 'This ice cream tastes like pistachio nuts')
  catalog.index_doc(2, pistachio)

Note that when you call ``index_doc``, you pass in a ``docid`` as the
first argument, and the object you want to index as the second
argument.  When we index the ``peach`` object above we index it with
the docid ``1``.  Each docid must be unique within a catalog; when you
query a :mod:`repoze.catalog` catalog, you'll get back a sequence of
document ids that match the query you supplied, which you'll
presumably need to map back to the content object in order to make
sense of the response; you're responsible for keeping track of which
objects map to which document id yourself.

Querying
--------

Once you've got some number of documents indexed, you can perform
queries against an existing catalog.  A query is performed by passing
keyword arguments to the ``search`` method of the catalog object::

   catalog.search(flavor=('peach', 'peach'))

Each keyword argument passed to ``search`` is either the name of an
index contained within the catalog or a special value that specifies
sort ordering and query limiting.  In the above example, we specified
no particular sort ordering or limit, and we're essentially asking the
catalog to return us all the documents that match the word 'peach' as
a field within the field index named ``flavor``.  Each index specifies
its own query argument style: field indexes specify that the value you
must pass in be a "range" search, so we pass in the tuple ``('peach',
'peach')``, which can be read "from peach to peach".  Other types of
indexes accept different query parameters.  For example, text indexes
accept only a term::

  catalog.search(description='nuts')

The result of calling the ``search`` method is a two tuple.  The first
element of the tuple is the number of document ids in the catalog
which match the query.  The second element is an iterable: each
iteration over this iterable returns a document id.  The results of
``catalog.search(description='nuts')`` might return::

  (1, [2])

The first element in the tuple indicates that there is one document in
the catalog that matches the description 'nuts'.  The second element
in the tuple (here represented as a list, although it's more typically
a generator) is a sequence of document ids that match the query.

You can combine search parameters to further limit a query::

  catalog.search(flavor=('peach', 'peach'), description='nuts')

This would return a result representing all the documents indexed
within the catalog with the flavor of peach and a description of nuts.

Index Types
-----------

Out of the box, ``repoze.catalog`` supports five index types: field
indexes, keyword indexes, text indexes, facet indexes, and path
indexes.  Field indexes are meant to index single discrete values, and
queries to a field index will only match if the value which was
indexed matches the query exactly.  Keyword indexes are essentially
field indexes which index sequences of values, and which can be
queried for any of the values in each sequence indexed.  Text indexes
index text using the ``zope.index.text`` index type, and can be
queried with arbitrary textual terms.  Text indexes can use various
splitting and normalizing strategies to collapse indexed texts for
better querying.  Facet indexes are much like keyword indexes, but
also allow for "faceted" indexing and searching, useful for performing
narrowing searches when there is a well-known set of allowable values
(the "facets").  Path indexes allow you to index documents as part of
a graph, and return documents that are contained in a portion of the
graph.

.. note:: The existing facet index implementation narrowing support is
   naive.  It is not meant to be used in catalogs that must use it to
   get count information for over, say, 30K documents, for performance
   reasons.

Helper Facilities
-----------------

:mod:`repoze.catalog` provides some helper facilities which help you
integrate a catalog into an arbitrary Python application.  The most
obvious is a ``FileStorageCatalogFactory``, which makes it reasonably
easy to create a Catalog object within an arbitrary Python
application.  Using this facility, you don't have to know anything
about ZODB to use :mod:`repoze.catalog`.  If you have an existing ZODB
application, however, you can ignore this facility entirely and use
the Catalog implementation directly.

:mod:`repoze.catalog` provides a ``DocumentMap`` object which can be
used to map document ids to "addresses".  An address is any value that
can be used to resolve the document id back into to a Python object.
In Zope, an address is typically a traversal path.  This facility
exists in :mod:`repoze.catalog.document.DocumentMap`.



