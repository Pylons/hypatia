Upgrading From Earlier Versions
===============================

Catalogs generated with :mod:`repoze.catalog` versions prior to 0.8.0 require
migration in order to add some house keeping data to the indexes that was not
needed prior to 0.8.0.  The easiest way to migrate a catalog is actually to
delete the catalog and reindex your content objects.  This is sufficient in
the vast majority of cases, since the catalog merely indexes data which itself
lives outside of the catalog, either in the same ZODB instance or in another
database altogether.

For particularly large datasets, rebuilding your catalog from scratch can
potentially take a long time. In order to make this less painful,
:mod:`repoze.catalog` does contain a migration utility which can migrate an
existing catalog in a much shorter period of time.  This utility comes in three
different flavors which can be used according to your use case.  The primary
problem being solved by the migration utility is making the indexes aware of
all of the docids stored in the catalog, not just just the docids of documents
which have values in a particular index.  To this end, the three different
flavors of migration utility represent three different ways to obtain the set
of all document ids stored in the catalog.


Migrate Using a Document Map
----------------------------

It will be the easiest and fastest to migrate your pre-0.8.0 catalog if you
are using a document map which is an instance of
``repoze.bfg.document.DocumentMap``::

    from repoze.catalog.migration import migrate_to_0_8_0_from_document_map

    migrate_to_0_8_0_from_document_map(catalog, document_map)


Migrate Using Self-Generated Set of Docids
------------------------------------------

Alternatively, if you do not use a document map, you can use a self-generated
set of document ids.  It is up to your application to calculate the set of all
document ids used in the catalog::

    from repoze.catalog.migration import migrate_to_0_8_0_from_docids

    migrate_to_0_8_0_from_docids(catalog, docids)


Let the Migration Utility Calculate the Set of Docids
-----------------------------------------------------

Your last option is to allow the migration utility to calculate the set of all
docids by examinging the indexes in the catalog.  If you can assume that every
document indexed by the catalog has a value in at least one index, then this
method, while potentially slow, should succeed in calculating the superset of
all document ids in the catalog::

    from repoze.catalog.migration import migrate_to_0_8_0

    migrate_to_0_8_0(catalog)


