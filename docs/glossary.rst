.. _glossary:

============================
Glossary
============================

.. glossary::

  Setuptools
    `Setuptools <http://peak.telecommunity.com/DevCenter/setuptools>`_
    builds on Python's ``distutils`` to provide easier building,
    distribution, and installation of packages.
  Interface
    An attribute of a model object that determines its type.  It is an
    instance of a ``zope.interface`` Interface class.
  Zope
    `The Z Object Publishing Framework <http://zope.org>`_.  The granddaddy 
    of Python web frameworks.
  ZODB
    `The Zope Object Database <http://wiki.zope.org/ZODB/FrontPage>`_
    which is a persistent object store for Python.
  Field index
    A type of index that is optimized to index single simple tokenized
    values.  When a field index is searched, it can be searched for
    one or more values, and it will return a result set that includes
    these values exacty.
  Text index
    A type of index which indexes a value in such a way that parts of
    it can be searched in a non-exact manner.  When a text index is
    searched, it returns results for values that match based on
    various properties of the text indexed, such as omitting
    "stopwords" the text might have.
  Facet index
    A type of index which can be used for faceted search.
  Path index
    A type of index that keeps track of documents within a graph;
    documents can be searched for by their position in the graph.
  zope.index
    The `underlying indexing machinery
    <http://pypi.python.org/pypi/zope.index>`_ that
    :mod:`repoze.catalog` uses.
  zope.app.catalog
    The `cataloging implementation
    <http://pypi.python.org/pypi/zope.app.catalog>`_ on which
    :mod:`repoze.catalog` is based (although it doesn't use any of
    its code).
  Virtualenv
    An isolated Python environment.  Allows you to control which
    packages are used on a particular project by cloning your main
    Python.  `virtualenv <http://pypi.python.org/pypi/virtualenv>`_
    was created by Ian Bicking.
  CQE
    A string representing a Python-like domain-specific-language
    expression which is used to generate a query object.
  Query Object
    An object used as an argument to the :meth:`repoze.catalog.Catalog.query` 
    method's ``queryobject`` parameter.

