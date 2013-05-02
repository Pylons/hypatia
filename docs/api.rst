.. _api_catalog_section:

:mod:`hypatia.catalog`
----------------------

.. automodule:: hypatia.catalog

  .. autoclass:: Catalog
     :members:

     .. automethod:: __setitem__

     .. automethod:: __getitem__

        Retrieve an index.

     .. automethod:: get

        Retrieve an index or return failobj.

     .. automethod:: reset

     .. automethod:: index_doc

     .. automethod:: unindex_doc

     .. automethod:: reindex_doc

  .. autoclass:: CatalogQuery
     :members:

     .. automethod:: __call__

     .. automethod:: sort

:mod:`hypatia.query`
--------------------

.. module:: hypatia.query

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

   .. autoclass:: NotContains

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

.. _api_util_section:

:mod:`hypatia.util`
-------------------

.. automodule:: hypatia.util

  .. autoclass:: ResultSet
     :members:

.. _api_exceptions_section:

:mod:`hypatia.exc`
-------------------

.. automodule:: hypatia.exc

  .. autoclass:: BadResults

  .. autoclass:: MultipleResults

  .. autoclass:: NoResults

  .. autoclass:: Unsortable

.. _api_fieldindex_section:

:mod:`hypatia.field`
--------------------

.. automodule:: hypatia.field

   .. autoclass:: FieldIndex
      :members:

.. _api_keywordindex_section:

:mod:`hypatia.keyword`
-------------------------------------

.. automodule:: hypatia.keyword

   .. autoclass:: KeywordIndex
      :members:

.. _api_textindex_section:

:mod:`hypatia.text`
-----------------------------------

.. automodule:: hypatia.text

   .. autoclass:: TextIndex
      :members:

.. _api_facetindex_section:

:mod:`hypatia.facet`
-------------------------------------

.. automodule:: hypatia.facet

   .. autoclass:: FacetIndex
      :members:

:mod:`hypatia.interfaces`
-------------------------

.. automodule:: hypatia.interfaces

  .. attribute:: STABLE

     Used as an argument to the ``sort_type`` parameter of IIndexSort.sort.

  .. attribute:: OPTIMAL

     Used as an argument to the ``sort_type`` parameter of IIndexSort.sort.
