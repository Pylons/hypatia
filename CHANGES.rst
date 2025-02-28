0.6 (unreleased)
----------------

- Migrate C extension to support PEP 489 multi-phase module initialization.

0.5 (2024-11-27)
----------------

- Add support for Python 3.11, 3.12, and 3.13.

- Drop support for Python < 3.8, including all the compatibility shims.

- Repair bitrot in doctests:  ensure that they run under ``py.test``.
  
0.4 (2022-04-23)
----------------

- Drop (unreleased) support for Python 3.3 and Python 3.4 (the ``persistent``
  package no longer supports these versions).

- Drop (unreleased) support for Python 3.5 (too difficult to build correctly --
  even with pyenv -- to bother).

- Drop (released) support for Python 2.6 and 3.2.

- Add support for Python 3.6, 3.7, 3.8, 3.9, 3.10 (thanks to Thierry Florac).

- Use pytest instead of python setup.py test -q in tox.ini.

- Change how cross-version coverage is computed in tests.

- Remove unused hypatia/text/ricecode.py file.

- Change building of docs slightly to cope with modified github protocols.
  Some warnings are unearthed with newer Sphinx, which I've not
  caught by turning warnings into errors yet, because I don't understand them.

- Don't modify queries attribute when optimizing And or Or, return a new
  instance instead. This change is needed to open new optimization
  possibilities, like factorization.

- Fix Comparator __eq__ method to include type in comparison,
  previously NotAny('index', [1]) was equal to Any('index', [1]) for example.


0.3 (2014-06-12)
----------------

- Depend on the ``ZODB`` package rather than the ``ZODB3`` package.  The former
  is a newer ZODB packaging, implying ZODB4.  If you actually require ZODB v3,
  you will need to pin ``hypatia`` to an older release.  You should know that
  the most recent release of ``ZODB3`` at this time (3.11) actually implies
  ZODB v4 (I know it's not exactly obvious, but Jim ensures me it is), so if
  you really require ZODB v3, you'll need to pin ``ZODB3`` to below 3.11 and
  ``hypatia`` to below this release.

- Keyword indices now have a ``unique_values`` method like Field indexes.

- Calling ``hypatia.util.ResultSet.first()`` and
  ``hypatia.util.ResultSet.one()`` is now idempotent.  Calling it a second time
  will return the same value, and calling it will not effect the result set's
  iterability (it will start from zero).

0.2 (2014-05-16)
----------------

- Query objects are now consulted for intersect and union operations via
  methods, instead of the intersection/union logic being embedded in And and Or
  query objects.  This makes it possible to create query object types which
  intersect and/or union differently when combined with other query results.

0.1 (2014-02-09)
----------------

- Fix a typo in the Sphinx docs, which causes intersphinx references to
  fail.

0.1a7 (2013-10-08)
------------------

- Add a ``unique_values`` API to field index.

- Sometimes an ``index`` attribute could not be found to resolve a result 
  set when deeply nesting boolean operations (like And and Or).  See 
  https://github.com/Pylons/hypatia/pull/5

- Throw an Unsortable properly when a field index without any docids is used as
  a sort index and ``raise_unsortable`` is ``True``.

0.1a6 (2013-05-30)
------------------

- Add ``check_query`` method to text index to allow for checking if a search
  term is parseable.

0.1a5 (2013-05-06)
------------------

- Added support for Python 3.2 / 3.3.

- Fix signature of TextIndex.sort (it would fail when e.g. raise_unsortable was
  passed).

- Add the a ``sort_type`` keyword argument to ``IIndexSort.sort`` and
  ``IResultSet.sort`` methods.  This value can be passed by calling code to
  control the type of sorting used.

- Add two constants: ``hypatia.interfaces.STABLE`` and
  ``hypatia.interfaces.OPTIMAL``.  These can be used as explicit arguments to
  the ``IIndexSort.sort`` and ``IResultSet.sort`` ``sort_type`` parameter to
  control the stability of sorting.

- The constructor of ``IResultSet`` now accepts a ``sort_type`` keyword
  argument.

- The ResultSet constructed by ``IResultSet.sort`` will be passed the value
  ``hypatia.interfaces.STABLE`` in its constructor to ensure that the second
  and subsequent sorts of the result set will be done as a stable sort, unless
  an explicit ``sort_type`` value is passed to that second sort.

0.1a4 (2013-04-28)
------------------

- Add IResultSet interface definition.

- Normalize keyword argument ordering of IIndexSort.sort and IResultSet.sort.

- Add an argument ``raise_unsortable`` to IIndexSort.sort and IResultSet.sort
  methods.  By default this is ``True``.  It means that iterating over the
  results returned by one of these methods *may* raise a
  ``hypatia.exc.Unsortable`` exception when a member of the docids passed in
  cannot be sorted by the index used to do the sort (e.g. a value for the docid
  is not present in the index).  It defaults to ``True``, which changes the
  default behavior of indexes.  To get the old default behavior back, pass
  ``False`` for this value.  Alternately, write code like this::

     from hypatia.exc import Unsortable

     ids = []
     results = resultset.sort(someindex)
     try:
         for id in results:
             ids.append(id)
     except Unsortable as e:
         unsorted = e.docids
         ids.extend(unsorted)

0.1a3 (2013-01-10)
------------------

- Optimize ``index_doc`` implementations of field and keyword index in cases
  where the discriminator returns the default.

- Remove code from ``hypatia.path``.  This package no longer supports
  PathIndex.

- Remove ``interfaces.IIndexQuery`` interface.  It was never relevant, as
  indices cannot be expected to implement all of its methods, only the ones
  which apply to each index.

- ``BaseIndexMixin`` no longer supplies default implementation of applyFoo
  methods which raise NotImplementedError.  Each index is now responsible for
  implementing all of its own applyFoo methods.  This is in the interest of
  fidelity with new query methods such as ``eq``, which are similarly not
  implemented in the base.

- Indexes are now compelled to implement a ``qname`` method for use by
  queries.

- ``DoesNotContain`` query renamed to ``NotContains`` for symmetry with other
  negated query names.

- New index methods: ``eq``, ``noteq``, ``ge``, ``le``, ``lt``, ``gt``,
  ``any``, ``notany``, ``all``, ``notall``, ``inrange``, ``notinrange``,
  ``contains``, ``notcontains``.  These methods return query objects.  Ex::

      catalog['flavors'].eq('peach')

- Query objects refactored internally to deal in index objects rather than
  index names.

- The ``query.parse_query`` function now requires a ``catalog`` argument.

- Query objects now supply an .execute method which returns a ResultSet.

- ResultSet objects are returned from .execute.  They represent a set of
  docids; they are iterable and have various methods for obtaining single
  objects (like ``one``, ``first``) and sorting (``sort``).

- All Query objects now have a ``flush`` method which accepts arbitrary
  positional and keyword arguments.  Calling the ``flush`` method of a query
  object will cause the ``flush`` method of all indexes participating in the
  query with the value passed to Query.flush with the same positional and
  keyword arguments.  This is to support Substance D upstream, which may
  require indexes to be flushed before a query happens.

- Add a ``document_repr`` method to all indexes which accepts a docid and
  returns a string represnting the index's knowledge about that docid.

0.1a2 (2012-07-02)
------------------

- This version of the code is incompatible with indexes produced by 0.1a1.
  There is no upgrade script.  Shame on you for using software with a 0.1a1
  version number and expecting backwards compatibility.

- Add `hypatia.catalog.CatalogQuery.sort` API for sorting external sets
  of docids based on index values.

- Add ``IIndexEnumeration`` interface, which all indexes must support.
  This implied the following backwards incompatibilities:

  - New interface methods: docids, docids_count, indexed, indexed_count,
    not_indexed and not_indexed_count.

  - documentCount method renamed to indexed_count.

  - wordCount method renamed to word_count.

- Remove unused INBest interface.

- IIndexInjection interface ``clear`` method renamed to ``reset`` to prevent
  confusion with dictionary ``clear`` (catalog is often dictionarylike).
  Catalog ``clear_indexes`` method replaced with ``reset``.

0.1a1
-----

- Initial release: fork of repoze.catalog and zope.index, combined.

