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

import ast
import BTrees
import sys

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

    def __str__(self):
        return type(self).__name__

    def iter_children(self):
        yield self.left
        yield self.right

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

class _AstQuery(object):
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
            name = 'process_%s' % node.__class__.__name__
            processor = getattr(self, name, None)
            if processor is None:
                raise ValueError(
                    "Unable to parse expression.  Unhandled expression "
                    "element: %s" % node.__class__.__name__
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
    def group(node, index_name, values):
        if len(values) > 1:
            if isinstance(node, Intersection):
                return All(index_name, values)
            elif isinstance(node, Union):
                return Any(index_name, values)
        return node

    def visit(node):
        if isinstance(node, Operator):
            left_index, left_values = visit(node.left)
            right_index, right_values = visit(node.right)
            if left_index != right_index:
                node.left = group(node.left, left_index, left_values)
                node.right = group(node.right, right_index, right_values)
                return None, []
            return left_index, left_values + right_values
        elif isinstance(node, Eq):
            return node.index_name, [node.value]
        return None, []

    index, values = visit(tree)
    return group(tree, index, values)

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

def parse_query(expr, names=None):
    """
    Parses the given expression string into a catalog query.  The `names` dict
    provides local variable names that can be used in the expression.
    """
    if names is None:
        names = {}
    return _group_any_and_all(_AstQuery(expr, names).query)
