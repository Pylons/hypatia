Genealogy of :mod:`hypatia`
===========================

Hypatia is derived from :term:`zope.index` and :term:`repoze.catalog`.

Hypatia depends heavily on the Zope Object Database (ZODB).  Because ZODB is
less a database and more a persistent object store (it doesn't possess a
query language; Python *is* its query language), it has been necessary to
create indexing and searching facilities for data stored in ZODB.

The first iteration of searching and indexing for ZODB-based applications (at
least post-Principia, which had something named Tabula, which I never
actually used) was the ZCatalog.  The ZCatalog was entirely tied to Zope2,
and still remains in heavy use today within Zope 2 applications such as
Plone.

The second iteration was ``zope.app.catalog``, which was a ZCatalog do-over
for Zope 3 applications.

Neither of these searching and indexing packages are particularly easy to use
outside of a Zope application.  Each makes various assumptions about the
content objects that need indexing or the environment that aren't appropriate
for arbitrary applications.  For instance, ZCatalog wants objects you want to
catalog to have a ``getPhysicalPath`` method which returns a "path".  An
instance of ``zope.app.catalog`` makes the assumption that that it's located
within a Zope 3 "site" object within a ZODB, and assumes that you want query
result sets to be sets of Python references to the original object you
indexed.  In other words, these packages assume too much to be maximally
useful outside the context in which they were developed.  `Repoze
<http://repoze.org>`_ is a project which has as a stated goal making it
easier for non-Zope Python developers to use Zope technologies outside Zope,
so this seemed like a natural thing to do under the Repoze flag.

Hypatia is a reboot of both zope.index and repoze.catalog with no backwards
compatibility constraints.
