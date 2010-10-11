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

import BTrees
import sys

class Query(object):
    """
    Base class for all elements that make up queries.
    """
    __parent__ = None
    __name__ = None

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

    def iter_children(self):
        return ()

    def print_tree(self, out=sys.stdout, level=0):
        print >>out, '  ' * level + str(self)
        for child in self.iter_children():
            child.print_tree(out, level+1)

class Comparator(Query):
    """
    Base class for all comparators used in queries.
    """
    def __init__(self, index_name, value):
        self.index_name = index_name
        self.value = value

    def get_index(self, catalog):
        return catalog[self.index_name]

    def __str__(self):
        return ' '.join((self.index_name, self.operator, repr(self.value)))

class Contains(Comparator):
    """Contains query.

    AST hint: 'foo' in index
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyContains(self.value)

    def __str__(self):
        return '%s in %s' % (repr(self.value), self.index_name)

class Eq(Comparator):
    """Equals query.

    AST hint:  index == 'foo'
    """
    operator = '=='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyEq(self.value)


class NotEq(Comparator):
    """Not equal query.

    AST hint: index != 'foo'
    """
    operator = '!='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyNotEq(self.value)

class Gt(Comparator):
    """ Greater than query.

    AST hint: index > 'foo'
    """
    operator = '>'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyGt(self.value)

class Lt(Comparator):
    """ Less than query.

    AST hint: index < 'foo'
    """
    operator = '<'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyLt(self.value)

class Ge(Comparator):
    """Greater (or equal) query.

    AST hint: index >= 'foo'
    """
    operator = '>='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyGe(self.value)

class Le(Comparator):
    """Less (or equal) query.

    AST hint: index <= 'foo
    """
    operator = '<='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyLe(self.value)

class Any(Comparator):
    """Any of query.
    """
    operator = 'any'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyAny(self.value)

class All(Comparator):
    """Any of query.
    """
    operator = 'all'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyAll(self.value)

class Range(Comparator):
    """ Index value falls within a range. """
    @classmethod
    def fromGTLT(self, start, end):
        assert isinstance(start, (Gt, Ge))
        if isinstance(start, Gt):
            start_exclusive = True
        else:
            start_exclusive = False

        assert isinstance(end, (Lt, Le))
        if isinstance(end, Lt):
            end_exclusive = True
        else:
            end_exclusive = False

        assert start.index_name == end.index_name
        return Range(start.index_name, start.value, end.value,
                     start_exclusive, end_exclusive)

    def __init__(self, index_name, start, end,
                 start_exclusive=False, end_exclusive=False):
        self.index_name = index_name
        self.start = start
        self.end = end
        self.start_exclusive = start_exclusive
        self.end_exclusive = end_exclusive

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyRange(
            self.start, self.end, self.start_exclusive, self.end_exclusive
        )

    def __str__(self):
        s = [repr(self.start)]
        if self.start_exclusive:
            s.append('<')
        else:
            s.append('<=')
        s.append(self.index_name)
        if self.end_exclusive:
            s.append('<')
        else:
            s.append('<=')
        s.append(repr(self.end))
        return ' '.join(s)

class Operator(Query):
    """
    Base class for operators.
    """
    family = BTrees.family32

    def __init__(self, left, right):
        self.left = left
        self.right = right

    def _set_left(self, left):
        if left is not None:
            left.__parent__ = self
            left.__name__ = 'left'
        self._left = left

    def _get_left(self):
        return self._left

    left = property(_get_left, _set_left)

    def _set_right(self, right):
        if right is not None:
            right.__parent__ = self
            right.__name__ = 'right'
        self._right = right

    def _get_right(self):
        return self._right

    right = property(_get_right, _set_right)

    def __str__(self):
        return type(self).__name__

    def iter_children(self):
        yield self._left
        yield self._right

class Union(Operator):
    """Union of two result sets."""
    def apply(self, catalog):
        left = self.left.apply(catalog)
        right = self.right.apply(catalog)
        if len(left) == 0:
            results = right
        elif len(right) == 0:
            results = left
        else:
            _, results = self.family.IF.weightedUnion(left, right)
        return results

class Intersection(Operator):
    """Intersection of two result sets."""
    def apply(self, catalog):
        left = self.left.apply(catalog)
        if len(left) == 0:
            results = self.family.IF.Set()
        else:
            right = self.right.apply(catalog)
            if len(right) == 0:
                results = self.family.IF.Set()
            else:
                _, results = self.family.IF.weightedIntersection(left, right)
        return results

class Difference(Operator):
    """Difference between two result sets."""
    def apply(self, catalog):
        left = self.left.apply(catalog)
        if len(left) == 0:
            results = self.family.IF.Set()
        else:
            right = self.right.apply(catalog)
            if len(right) == 0:
                results = left
            else:
                results = self.family.IF.difference(left, right)
        return results

def parse_query(expr, names=None):
    """
    Parses the given expression string into a catalog query.  The `names` dict
    provides local variable names that can be used in the expression.
    """
    if names is None:
        names = {}
    return _optimize_query(_AstParser(expr, names).query)

class _AstParser(object):
    """
    Uses Python's ast module to parse an expression into an abstract syntax
    tree.  It then walks the tree and constructs a tree of Query objects.  Take
    the following query:

        >>> expr = "a == 1 or (b == 2 or b == 3)"

    The ast for this expression looks like this:

        >>> _print_ast(expr)
        <_ast.Module object at 0xb7377d4c>
          <_ast.Expr object at 0xb737e44c>
            <_ast.BoolOp object at 0x88f13cc>
              <_ast.And object at 0x88ec0ac>
              <_ast.Compare object at 0x88f13ac>
                <_ast.Name object at 0x88f13ec>
                  <_ast.Load object at 0x88ea86c>
                <_ast.Eq object at 0x88ece2c>
                <_ast.Num object at 0x88f14cc>
              <_ast.BoolOp object at 0x88f14ec>
                <_ast.Or object at 0x88ec14c>
                <_ast.Compare object at 0x88f154c>
                  <_ast.Name object at 0x88f15ac>
                    <_ast.Load object at 0x88ea86c>
                  <_ast.Eq object at 0x88ece2c>
                  <_ast.Num object at 0x88f15cc>
                <_ast.Compare object at 0x88f162c>
                  <_ast.Name object at 0x88f168c>
                    <_ast.Load object at 0x88ea86c>
                  <_ast.Eq object at 0x88ece2c>
                  <_ast.Num object at 0x88f16ac>

    _ast.Module is always the root of any tree returned by the ast parser. It
    is a requirement for _AstParser that the _ast.Module node contain only a
    single child node of type _ast.Expr, which represents the expression we
    are trying to transform into a query. The _ast.Expr node will always only
    have a single child which is the root of the expression tree, ie
    _ast.BoolOp in the above example.

    The walk method is the driver for constructing the query tree.  It performs
    a depth first traversal of the ast.  For each node in the ast it checks to
    see if we have a method for processing that node type.  Node processors are
    all named 'process_NodeType' where NodeType is the name of the class of the
    ast node, ie type(node).__name__.  Each processor method is passed the
    current node and it's children which have already been processed.  In this
    way the query tree is built from the ast from the bottom up.
    """
    def __init__(self, expr, names):
        self.names = names
        statements = ast.parse(expr).body
        if len(statements) > 1 :
            raise ValueError(
                "Can only process single expression."
            )
        expr_tree = statements[0]
        if not isinstance(expr_tree, ast.Expr):
            raise ValueError(
                "Not an expression."
            )

        self.query = self.walk(expr_tree.value)

    def walk(self, tree):
        def visit(node):
            children = [visit(child) for child in ast.iter_child_nodes(node)]
            name = 'process_%s' % type(node).__name__
            processor = getattr(self, name, None)
            if processor is None:
                raise ValueError(
                    "Unable to parse expression.  Unhandled expression "
                    "element: %s" % type(node).__name__
                )
            return processor(node, children)
        return visit(tree)

    def process_Load(self, node, children):
        pass

    def process_Name(self, node, children):
        return node

    def process_Attribute(self, node, children):
        name = children[0]
        dotted_name = ast.Name()
        dotted_name.id = '.'.join((name.id, node.attr))
        return dotted_name

    def process_Str(self, node, children):
        return node.s

    def process_Num(self, node, children):
        return node.n

    def process_List(self, node, children):
        l = list(children[:-1])
        for i in xrange(len(l)):
            if isinstance(l[i], ast.Name):
                l[i] = self._value(l[i])
        return l

    def process_Tuple(self, node, children):
        return tuple(self.process_List(node, children))

    def process_Eq(self, node, children):
        return Eq

    def process_NotEq(self, node, children):
        return NotEq

    def process_Lt(self, node, children):
        return Lt

    def process_LtE(self, node, children):
        return Le

    def process_Gt(self, node, children):
        return Gt

    def process_GtE(self, node, children):
        return Ge

    def process_In(self, node, children):
        return Contains

    def process_Compare(self, node, children):
        # Python allows arbitrary chaining of comparisons, ie:
        #   x == y == z != abc
        #   x < y >= z
        #
        # For our purposes, though, we are only interested in two basic forms:
        #   index_name <comparison_operator> value
        # or
        #   start [<|<=] index_name [<|<=] end
        #
        # Where the second form maps to a Range comparator and the first
        # form matches any of the other comparators.  Arbitrary chaining as
        # shown above is not supported.
        if len(children) == 3:
            # Simple binary form
            operand1, operator, operand2 = children
            if operator is Contains:
                return operator(self._index_name(operand2),
                                self._value(operand1))
            return operator(self._index_name(operand1), self._value(operand2))
        elif len(children) == 5:
            # Range expression
            start, op1, op2, index_name, end = children
            if op1 in (Lt, Le) and op2 in (Lt, Le):
                if op1 is Lt:
                    start_exclusive = True
                else:
                    start_exclusive = False
                if op2 is Lt:
                    end_exclusive = True
                else:
                    end_exclusive = False
                return Range(self._index_name(index_name),
                             self._value(start),
                             self._value(end),
                             start_exclusive,
                             end_exclusive)
        raise ValueError(
            "Bad expression: unsupported chaining of comparators."
        )

    def process_BitOr(self, node, children):
        return Union

    def process_BitAnd(self, node, children):
        return Intersection

    def process_Sub(self, node, children):
        return Difference

    def process_BinOp(self, node, children):
        left, operator, right = children
        if not isinstance(left, Query):
            raise ValueError(
                "Bad expression: left operand for %s must be a result set." %
                operator.__name__
            )
        if not isinstance(right, Query):
            raise ValueError(
                "Bad expression: right operand for %s must be a result set." %
                operator.__name__
            )
        return operator(left, right)

    def process_Or(self, node, children):
        return Union

    def process_And(self, node, children):
        return Intersection

    def process_BoolOp(self, node, children):
        operator = children.pop(0)
        for child in children:
            if not isinstance(child, Query):
                raise ValueError(
                    "Bad expression: All operands for %s must be result sets."
                    % operator.__name__)

        op = operator(children.pop(0), children.pop(0))
        while children:
            op = operator(op, children.pop(0))
        return op

    def _index_name(self, node):
        if not isinstance(node, ast.Name):
            raise ValueError("Index name must be a name.")
        return node.id

    def _value(self, node):
        if isinstance(node, ast.Name):
            try:
                return self.names[node.id]
            except:
                raise NameError(node.id)
        return node

def _group_any_and_all(tree):
    """
    This is a query optimization which looks for subtrees of two or more
    Eq queries for the same index all joined by union or intersection:

        Eq(a, 1) | Eq(a, 2) | etc...

    or:

        Eq(a, 1) & Eq(a, 2) & etc...

    In these cases, instead of performing N individual Eq queries and combining
    the result sets along the way via union or intersection operations, we can
    rewrite these subexpressions as:

        Any(a, [1, 2])

    or:

        All(a, [1, 2])

    Take, for example, the expression:

        >>> expr = "(a == 1 or a == 2 or a == 3) and b == 1"

    Before optimization the query tree looks like this:

        >>> query._AstParser(expr, {}).query.print_tree()
        Intersection
          Union
            Union
              a == 1
              a == 2
            a == 3
          b == 1

    And after optimization:

        >>> query.parse_query(expr).print_tree()
        Intersection
          a any [1, 2, 3]
          b == 1

    So we've taken three separate index queries for index a, joined by two
    set union operations, and replaced this with a single Any query for the
    same index.

    Note that tree transformations are done in place.  The root node of the
    tree is returned since there is a chance that the root node needs to be
    replaced.
    """
    def group(node, index_name, values):
        """
        Called on each node in the tree which might be replaceable.  `node` is
        the candidate for replacement.  `index_name` is the name of the index
        for all descendant Eq queries and `values` is a list of the values for
        the descendant Eq queries.  If there is more than one value and the
        type of the current node is Union or Intersection, then we can replace
        the subexpression represented by this node with a single Any or All
        query.
        """
        if len(values) > 1:
            if isinstance(node, Intersection):
                return All(index_name, values)
            elif isinstance(node, Union):
                return Any(index_name, values)
        return node

    def visit(node):
        """
        Performs a recursive depth first tree traversal attempting to collect
        values for Eq comparators which are joined together by unions or
        intersections. Returns a tuple: (op_type, index_name, values) where
        `op_type` is the type of all operators in the subexpression
        represented by the visited node, `index_name` is the name of the index
        used in all Eq queries in the subexpression represented by the visited
        node, and `values` is the collection of values for each Eq query in
        the subexpression. If the subexpression contains mixed operators,
        comparators other than Eq or mixed index_names, the return value will
        be (None, None, []), meaning that no grouping could be done.

        If a visited node is an Eq comparator, then we start a new potential
        grouping by returning (None, node.index_name, node.value).  `op_type`
        is None because we don't know, yet, what, if any, operator contains the
        current node.  This will be filled in at higher level operator nodes.

        If the visited node is an operator node, then we recursively visit the
        left and right subtrees and look at the results.  If visiting a subtree
        returns None for `op_type` then we fill in the current operation type
        for the subtree.  If `index_name` and `op_type` match for both subtrees
        and if both subtree op_types match the current node's op_type, then we
        may group both subtrees together and return the common `op_type`,
        `index_name` and the values collected from any Eq nodes in either
        subtree.  Otherwise, if not able to group the two subtrees together,
        `group` is called on each subtree, attempting to replace each subtree
        with an Any or All query if possible.
        """
        if isinstance(node, Operator):
            this_op = type(node)
            left_op, left_index, left_values = visit(node.left)
            if left_op is None:
                left_op = this_op
            right_op, right_index, right_values = visit(node.right)
            if right_op is None:
                right_op = this_op
            if left_index != right_index or not (
                left_op == right_op == this_op):
                node.left = group(node.left, left_index, left_values)
                node.right = group(node.right, right_index, right_values)
                return None, None, []
            return this_op, left_index, left_values + right_values
        elif isinstance(node, Eq):
            return None, node.index_name, [node.value]
        return None, None, []

    # Must call group on the root node, in case the root node needs to be
    # replaced.
    op, index, values = visit(tree)
    return group(tree, index, values)

def _make_ranges(tree):
    starts = {}
    ends = {}
    def visit(node):
        if isinstance(node, (Gt, Ge)):
            starts[node.index_name] = node
            return node
        elif isinstance(node, (Lt, Le)):
            ends[node.index_name] = node
            return node
        elif not isinstance(node, Operator):
            return node

        is_intersection = isinstance(node, Intersection)

        node.left = visit(node.left)
        if not is_intersection:
            starts.clear()
            ends.clear()

        node.right = visit(node.right)
        if not is_intersection:
            starts.clear()
            ends.clear()
            return node

        for index_name in starts:
            if index_name not in ends:
                continue
            start = starts.pop(index_name)
            end = ends.pop(index_name)
            gtlt = Range.fromGTLT(start, end)

            if start.__parent__ is end.__parent__ is node:
                return gtlt

            if start.__parent__ is node:
                child = start
                nephew = end
            else:
                child = end
                nephew = start

            if child.__name__ == 'left':
                node.left = gtlt
            else:
                node.right = gtlt

            brother = nephew.__parent__
            if nephew.__name__ == 'left':
                other_nephew = brother.right
            else:
                other_nephew = brother.left
            setattr(brother.__parent__, brother.__name__, other_nephew)

            # Since we check each time, at most there can be only one new
            # match
            break

        return node

    return visit(tree)

def _optimize_query(tree):
    tree = _group_any_and_all(tree)
    tree = _make_ranges(tree)
    return tree

def _print_ast(expr): #pragma NO COVERAGE
    """
    Useful method for visualizing AST trees while debugging.
    """
    tree = ast.parse(expr)
    def visit(node, level):
        print '  ' * level + str(node)
        for child in ast.iter_child_nodes(node):
            visit(child, level + 1)
    visit(tree, 0)

try:
    import ast
except ImportError: #pragma NO COVERAGE
    del parse_query, _AstParser, _optimize_query, _print_ast
