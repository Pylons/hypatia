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

import zope.interface
import zope.component

import BTrees

from repoze.catalog import interfaces

class Query(object):
    """
    Base class for all elements that make up queries.
    """
    def __and__(self, right):
        self._check_type("set intersection", right)
        return Intersection(self, right)

    def __or__(self, right):
        self._check_type("set union", right)
        return Union(self, right)

    def __sub__(self, right):
        self._check_type("set difference", right)
        return Difference(self, right)

    def _check_type(self, operator, operand):
        if not isinstance(operand, Query):
            raise TypeError(
                "TypeError: unsupported operand types for %s: %s %s" %
                (operator, type(self), type(operand))
            )

class Comparator(Query):
    """
    Base class for all comparators used in queries.
    """
    def __init__(self, index_name, value):
        self.index_name = index_name
        self.value = value

    def get_index(self, catalog):
        return catalog[self.index_name]

class Contains(Comparator):
    """Contains query.

    AST hint: 'foo' in index
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyContains(self.value)

class Eq(Comparator):
    """Equals query.

    AST hint:  index == 'foo'
    """
    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyEq(self.value)


class NotEq(Comparator):
    """Not equal query.

    AST hint: index != 'foo'
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyNotEq(self.value)

class Gt(Comparator):
    """ Greater than query.

    AST hint: index > 'foo'
    """
    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyGt(self.value)

class Lt(Comparator):
    """ Less than query.

    AST hint: index < 'foo'
    """
    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyLt(self.value)

class Ge(Comparator):
    """Greater (or equal) query.

    AST hint: index >= 'foo'
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyGe(self.value)


class Le(Comparator):
    """Less (or equal) query.

    AST hint: index <= 'foo
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyLe(self.value)

class Any(Comparator):
    """Any of query.

    AST hint: any(['a', 'b', 'c']) in index
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyAny(self.value)

class All(Comparator):
    """Any of query.

    AST hint: all(['a', 'b', 'c']) in index
    """
    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyAll(self.value)

class Operator(Query):
    """
    Base class for operators.
    """
    family = BTrees.family32

    def __init__(self, left, right):
        self.left = left
        self.right = right

class Union(Operator):
    """Union of two result sets."""
    def apply(self, catalog):
        # Untested, should look something like this:
        _, results = self.family.IF.weightedUnion(
            self.left.apply(catalog), self.right.apply(catalog))
        return results

class Intersection(Operator):
    """Intersection of two result sets."""
    def apply(self, catalog):
        # Untested, should look something like this:
        _, results = self.family.IF.weightedIntersection(
            self.left.apply(catalog), self.right.apply(catalog))
        return results

class Difference(Operator):
    """Difference between two sets."""
    def apply(self, catalog):
        self.family.IF.difference(
            self.left.apply(catalog), self.right.apply(catalog))

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
      SearchQuery(catalog, appleQuery).And(houseQuery).Or(towerQuery).apply()
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
        self.results = res

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
                self.results = res
            else:
                _, self.results = self.family.IF.weightedUnion(
                    self.results, res)
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
            _, self.results = self.family.IF.weightedIntersection(
                self.results, res)
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
