.. _api_catalog_section:

:mod:`repoze.catalog.catalog`
-----------------------------

.. automodule:: repoze.catalog.catalog

  .. autoclass:: Catalog
     :members:

     .. automethod:: __setitem__

     .. automethod:: __getitem__

        Retrieve an index.

     .. automethod:: get

        Retrieve an index or return failobj.


:mod:`repoze.catalog.query`
---------------------------

.. module:: repoze.catalog.query

Comparators
~~~~~~~~~~~

   .. autoclass:: Contains

   .. autoclass:: Eq

   .. autoclass:: NotEq

   .. autoclass:: Gt

   .. autoclass:: Lt

   .. autoclass:: Ge

   .. autoclass:: Le

   .. autoclass:: Contains

   .. autoclass:: DoesNotContain

   .. autoclass:: Any

   .. autoclass:: NotAny

   .. autoclass:: All

   .. autoclass:: NotAll

   .. autoclass:: InRange

   .. autoclass:: NotInRange

Boolean Operators
~~~~~~~~~~~~~~~~~

   .. autoclass:: Or

   .. autoclass:: And

   .. autoclass:: Not

Other Helpers
~~~~~~~~~~~~~

.. autoclass:: Name

.. autofunction:: parse_query

.. _api_fieldindex_section:

:mod:`repoze.catalog.indexes.field`
-----------------------------------

.. automodule:: repoze.catalog.indexes.field

   .. autoclass:: CatalogFieldIndex
      :members:

.. _api_keywordindex_section:

:mod:`repoze.catalog.indexes.keyword`
-------------------------------------

.. automodule:: repoze.catalog.indexes.keyword

   .. autoclass:: CatalogKeywordIndex
      :members:

.. _api_textindex_section:

:mod:`repoze.catalog.indexes.text`
-----------------------------------

.. automodule:: repoze.catalog.indexes.text

   .. autoclass:: CatalogTextIndex
      :members:

.. _api_facetindex_section:

:mod:`repoze.catalog.indexes.facet`
-------------------------------------

.. automodule:: repoze.catalog.indexes.facet

   .. autoclass:: CatalogFacetIndex
      :members:

:mod:`repoze.catalog.indexes.path`
----------------------------------

.. automodule:: repoze.catalog.indexes.path

   .. autoclass:: CatalogPathIndex
      :members:

.. _api_document_section:

:mod:`repoze.catalog.document`
------------------------------

.. automodule:: repoze.catalog.document

  .. autoclass:: DocumentMap
     :members:

