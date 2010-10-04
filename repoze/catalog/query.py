##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
$Id:$
"""
__docformat__ = "reStructuredText"

import zope.interface
import zope.component

import BTrees

from zope.index.interfaces import IIndexSort
from repoze.catalog import interfaces

class Text(object):
    """Text query."""

    zope.interface.implements(interfaces.ITextQuery)

    def __init__(self, index_name, value):
        self.index_name = index_name
        self.value = value

    def apply(self, catalog):
        index = catalog[self.index_name]
        return index.apply(self.value)


class Eq(object):
    """Equal query."""

    zope.interface.implements(interfaces.IEqQuery)

    def __init__(self, index_name, value):
        if value is None:
            raise AssertionError('value to Eq query must not be ``None``')
        self.index_name = index_name
        self.value = value

    def apply(self, catalog):
        index = catalog[self.index_name]
        return index.applyEq(self.value)


class NotEq(object):
    """Not equal query."""

    zope.interface.implements(interfaces.INotEqQuery)

    def __init__(self, index_name, value):
        if value is None:
            raise AssertionError('value to NotEq query must not be ``None``')
        self.index_name = index_name
        self.value = value

    def apply(self, catalog):
        index = catalog[self.index_name]
        return index.applyNotEq(self.value)


class Between(object):
    """Between query."""

    zope.interface.implements(interfaces.IBetweenQuery)

    def __init__(self, index_name, min_value, max_value):
        self.index_name = index_name
        self.min_value = min_value
        self.max_value = max_value

    def apply(self, catalog):
        index = catalog[self.index_name]
        return index.applyBetween(self.min_value, self.max_value)


class Ge(object):
    """Greater (or equal) query."""

    zope.interface.implements(interfaces.IGeQuery)

    def __init__(self, index_name, min_value):
        self.index_name = index_name
        self.min_value = min_value

    def apply(self, catalog):
        index = catalog['index_name']
        return index.applyGe(self.min_value, self.exclude_min)


class Le(object):
    """Less (or equal) query."""

    zope.interface.implements(interfaces.ILeQuery)

    def __init__(self, index_name, max_value):
        self.index_name = index_name
        self.max_value = max_value

    def apply(self, catalog):
        index = catalog[self.index_name]
        return index.applyLe(self.max_value)


class In(object):
    """In query."""

    zope.interface.implements(interfaces.IInQuery)

    def __init__(self, index_name, values):
        self.index_name = index_name
        self.values = values

    def apply(self, catalog):
        index = catalog[self.index_name]
        return index.applyIn(self.values)


class SearchQuery(object):
    """Chainable query processor.

    Note: this search query acts as a chain. This means if you apply
    two queries with the And method, the result will contain the
    intersection of both results. If you later add a query within the
    Or method to the chain the new result will contain items in the
    result we skipped with the And method before if the new query
    contains such (previous Not() filtered) items.

    Sample query::

      appleQuery = Text('textIndex', 'Apple')
      houseQuery = Text('textIndex', 'House')
      towerQuery = Text('textIndex', 'Tower')
      SearchQuery(appleQuery).And(houseQuery).Or(towerQuery).apply(catalog)
    """

    zope.interface.implements(interfaces.ISearchQuery)

    family = BTrees.family32
    _results = None

    def __init__(self, catalog, query=None, family=None):
        """Initialize with none or existing query."""
        res = None
        self.catalog = catalog
        if query is not None:
            res = query.apply(self.catalog)
        if family is not None:
            self.family = family
        if res is not None:
            self.results = self.family.IF.Set(res)

    @apply
    def results():
        """Ensure a empty result if None is given and allows to override
           existing results.
        """
        def get(self):
            if self._results is None:
                return self.family.IF.Set()
            return self._results
        def set(self, results):
            self._results = results
        return property(get, set)

    def apply(self, sort_index=None, limit=None, sort_type=None, reverse=False):
        return self.catalog.sort_result(self.results, sort_index, limit,
                                        sort_type, reverse)

    def Or(self, query):
        """Enhance search results. (union)

        The result will contain docids which exist in the existing result
        and/or in the result from the given query.
        """
        res = query.apply(self.catalog)
        if res:
            if len(self.results) == 0:
                # setup our first result if query=None was used in __init__
                self.results = self.family.IF.Set(res)
            else:
                self.results = self.family.IF.union(self.results, res)
        return self

    def And(self, query):
        """Restrict search results. (intersection)

        The result will only contain docids which exist in the existing
        result and in the result from the given query.
        """
        if len(self.results) == 0:
            # there is no need to do something if previous results is empty
            return self

        res = query.apply(self.catalog)
        if res:
            self.results = self.family.IF.intersection(self.results, res)
        # if given query is empty, means we have to return a empty result too!
        else:
            self.results = self.family.IF.Set()
        return self

    def Not(self, query):
        """Exclude search results. (difference)

        The result will only contain docids which exist in the existing
        result but do not exist in the result from the given query.

        This is faster if the existing result is small. But note, it get
        processed in a chain, results added after this query get added again.
        So probably you need to call this at the end of the chain.
        """
        if len(self.results) == 0:
            # there is no need to do something if previous results is empty
            return self

        res = query.apply(self.catalog)
        if res:
            self.results = self.family.IF.difference(self.results, res)
        return self
