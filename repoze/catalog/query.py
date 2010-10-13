"""
This module provides a means of constructing query objects which can be used to
query a catalog.  Query objects can be composed programmatically or can be
parsed from a string using a Pythonic DSL.

Query objects are of two types: comparators and operators.  A comparator
performs a single query on a single index.  Operators allow results from
individual queries to be combined using set operations.  For example::

    query = Intersection(Eq('author', 'crossi'), Contains('body', 'biscuits'))

This will query two indexes, author and body, and then return all documents
which satisfy both queries. All query objects may be combined using supported
set operators, so the above query could also have been written::

    query = Eq('author', 'crossi') & Contains('body', 'biscuits')

Query objects may also be created by parsing a query string.  The query parser
uses Python's internal code parser to parse query expression strings, so the
syntax is just like Python::

    query = parse_query("author == 'crossi' and 'biscuits' in body")

The query parser allows name substitution in expressions.  Names are resolved
using a dict passed into `parse_query`::

    author = request.params.get("author")
    word = request.params.get("search_term")
    query = parse_query("author == author and word in body", names=locals())

Unlike true Python expressions, ordering of the terms is important for
comparators. For most comparators the index_name must be written on the left.
The following, for example, would raise an exception::

    query = parse_query("'crossi' == author")

Note that not all index types support all comparators. An attempt to perform
a query using a comparator that is not supported by the index being queried
will result in a NotImplementedError being raised when the query is performed.

Comparators
===========

The supported comparators are as follows:

Equal To
--------
Python: Eq(index_name, value)
DSL: index_name == value

Not Equal To
------------
Python: NotEq(index_name, value)
DSL: index_name != value

Greater Than
------------
Python: Gt(index_name, value)
DSL: index_name > value

Less Than
---------
Python: Lt(index_name, value)
DSL: index_name < value

Greater Than Or Equal To
------------------------
Python: Ge(index_name, value)
DSL: index_name >= value

Less Than Or Equal To
---------------------
Python: Le(index_name, value)
DSL: index_name <= value

Any
---
Python: Any(index_name, [value1, value2, ...])
DSL: index_name == value1 or index_name == value2 or etc...
     index_name in any([value1, value2, ...])
     index_name in any(values)

All
---
Python: All(index_name, [value1, value2, ...])
DSL: index_name == value1 and index_name == value2 and etc...
     index_name in all([value1, value2, ...])
     index_name in all(values)


Within Range
------------
Python: Range(index_name, start, end,
              start_exclusive=False, end_exclusive=False)
DSL: start <= index_name <= end
     start < index_name < end

Operators
=========

The following set operations are allowed in queries:

Intersection
------------
Python: Intersection(query1, query2)
        query1 & query2
DSL: query1 and query2
     query1 & query2

Union
-----
Python: Union(query1, query2)
        query1 | query2
DSL: query1 or query2
     query1 | query2

Difference
----------
Python: Difference(query1, query2)
        query1 - query2
DSL: query1 - query2

"""
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

    CQE equivalent: index in all(['foo', 'bar'])
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyContains(self.value)

    def __str__(self):
        return '%s in %s' % (repr(self.value), self.index_name)

class Eq(Comparator):
    """Equals query.

    CQE equivalent:  index == 'foo'
    """
    operator = '=='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyEq(self.value)


class NotEq(Comparator):
    """Not equal query.

    CQE eqivalent: index != 'foo'
    """
    operator = '!='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyNotEq(self.value)

class Gt(Comparator):
    """ Greater than query.

    CQE equivalent: index > 'foo'
    """
    operator = '>'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyGt(self.value)

class Lt(Comparator):
    """ Less than query.

    CQE equivalent: index < 'foo'
    """
    operator = '<'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyLt(self.value)

class Ge(Comparator):
    """Greater (or equal) query.

    CQE equivalent: index >= 'foo'
    """
    operator = '>='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyGe(self.value)

class Le(Comparator):
    """Less (or equal) query.

    CQE equivalent: index <= 'foo
    """
    operator = '<='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyLe(self.value)

class Any(Comparator):
    """Any of query.

    CQE equivalent: ??
    """
    operator = 'any'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyAny(self.value)

class All(Comparator):
    """All query.

    CQE equivalent: ??
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

    @apply
    def left():
        def _set_left(self, left):
            if left is not None:
                left.__parent__ = self
                left.__name__ = 'left'
            self._left = left

        def _get_left(self):
            return self._left

        return property(_get_left, _set_left)

    @apply
    def right():
        def _set_right(self, right):
            if right is not None:
                right.__parent__ = self
                right.__name__ = 'right'
            self._right = right

        def _get_right(self):
            return self._right

        return property(_get_right, _set_right)

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

def _comparator_factory(method):
    def wrapper(self, node, children):
        cls = method(self, node, children)
        def factory(left, right):
            return cls(self._index_name(left), self._value(right))
        factory.type = cls
        return factory
    return wrapper

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
    have a single child which is the root of the expression tree,
    _ast.BoolOp in the above example.

    The walk method is the driver for constructing the query tree.  It performs
    a depth first traversal of the ast.  For each node in the ast it checks to
    see if we have a method for processing that node type.  Node processors are
    all named 'process_NodeType' where NodeType is the name of the class of the
    ast node, ie type(node).__name__.  Each processor method is passed the
    current node and its children which have already been processed.  In this
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

    @_comparator_factory
    def process_Eq(self, node, children):
        return Eq

    @_comparator_factory
    def process_NotEq(self, node, children):
        return NotEq

    @_comparator_factory
    def process_Lt(self, node, children):
        return Lt

    @_comparator_factory
    def process_LtE(self, node, children):
        return Le

    @_comparator_factory
    def process_Gt(self, node, children):
        return Gt

    @_comparator_factory
    def process_GtE(self, node, children):
        return Ge

    def process_In(self, node, children):
        def factory(left, right):
            if callable(right): # any or all, see process_Call
                return right(self._index_name(left))
            return Contains(self._index_name(right), self._value(left))
        factory.type = Contains
        return factory


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
            left, factory, right = children
            return factory(left, right)
        elif len(children) == 5:
            # Range expression
            start, f1, f2, index_name, end = children
            op1, op2 = f1.type, f2.type
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

    def process_Call(self, node, children):
        func = children.pop(0)
        name = getattr(func, 'id', str(node.func))
        if name not in ('any', 'all'):
            raise ValueError(
                "Bad expression: Illegal function call in expression: %s" %
                name)
        if len(children) != 1:
            raise ValueError(
                "Bad expression: Wrong number of arguments to %s" % name)

        values = children[0]
        if name == 'any':
            comparator = Any
        else:
            comparator = All
        def factory(index_name):
            return comparator(index_name, values)
        return factory

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
        query.  Returns either the node or its replacement.
        """
        if len(values) > 1:
            if isinstance(node, Intersection):
                return All(index_name, values)
            elif isinstance(node, Union):
                return Any(index_name, values)
        return node

    def visit(node):
        """
        Performs a recursive depth first traversal attempting to collect
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
        grouping by returning (None, node.index_name, node.value). `op_type`
        is None because we don't know yet what, if any, operator contains the
        current node. This will be filled in at the Eq node's parent, which
        will be an operator node.

        If the visited node is an operator node, then we recursively visit the
        left and right subtrees and look at the results. If visiting a subtree
        returns None for `op_type` then we fill in the current operation type
        for the subtree. If `index_name` and `op_type` match for both subtrees
        and if both subtree op_types match the current node's op_type, then we
        may group both subtrees together and return the common `op_type`,
        `index_name` and the values collected from any Eq nodes in either
        subtree. Otherwise, if not able to group the two subtrees together,
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
    """
    This is a query optimization which looks for pairs of Gt/Ge and Lt/Le
    queries for the same index, joined by intersection. So, for example, this
    query:

      Ge(a, 0) & Le(a, 5)

    Can be rewritten as:

      Range(a, 0, 5, False, False)

    Here we take what would be two separate index queries and an intersection
    and replace with a single range query on that index.

    The start and end queries for a pair do not have to be immediately
    adjacent to each other--they need only be in the same grouping of
    intersections. For example this query:

      Ge(a, 0) & Eq(b, 7) & Lt(a, 5)

    Will be rewritten as:

      Eq(b, 7) & Range(a, 0, 5, False, True)

    This query will not be rewritten because the start and end queries are
    separated by a union operator:

      Ge(a, 0) | Eq(b, 7) & Lt(a, 5)


    Note that tree transformations are done in place.  The root node of the
    tree is returned since there is a chance that the root node needs to be
    replaced.

    Potential range boundaries are discovered by performing a depth first
    traversal of the query tree.  At each node, there is a check to see if
    the current node could potentially form half of a range query.  Range
    boundaries are collected by index_name and stored in `starts` and `ends`
    dictionaries that will be accessible at higher nodes.  Whenever an operator
    node other than an intersection is traversed, potential range boundaries
    are forgotten since we only want to create ranges from subqueries that are
    connected to each other via intersection operations.

    At each intersection node, after potential range boundaries have been
    collected from the left and right subtrees, the potential boundaries are
    checked for any matching pairs. A matching pair is comprised of a Gt or Ge
    and an Lt or Le which are for the same index. When a matching pair is
    found, the tree must be transformed. There are three potential cases which
    must be handled each in a different way.

    In the first and easier case, the range boundary pair nodes are the
    immediate left and right children of the current node.  In this case, the
    current node can simply be replaced by a range.  For example, this query:

        >>> expr = "A > 0 and A < 5 and B ==7"
        >>> _AstParser(expr, {}).query.print_tree()
        Intersection
          Intersection
            A > 0
            A < 5
          B == 7

    Is transformed to:

        >>> expr = "A > 0 and A < 5 and B ==7"
        >>> parse_query(expr).print_tree()
        Intersection
          0 < A < 5
          B == 7

    The nested Intersection was replaced with the range query.

    In the second, somewhat more complicated case, one of the pair is a
    descendant of the current node but not an immediate child. We refer to the
    descendant node half of the pair as the nephew and that node's parent,
    which we know must be an intersection node, as the brother. Don't worry if
    the nephew/brother nomenclature doesn't make complete sense. We need to
    refer to them as something. We could have called them Fred and Barney. To
    help visualize, consider this unoptimized query tree:

        >>> expr = "A > 0 and (A < 5 and B == 7)"
        >>> _AstQuery(expr, {}).query.print_tree()
        Intersection
          A > 0           <-- child
          Intersection    <-- brother
            A < 5         <-- nephew
            B == 7        <-- other_nephew

    When the match is found between the child and nephew, we now need to
    transform the tree in such a way that the expression remains equivalent
    but with two fewer nodes since we are trading one intersection and two
    comparisons for a single range query. In this case we can replace the
    child with the new range query and then promote the other_nephew up to
    replace the brother (an intersection node), since the nephew has been
    absorbed into the range query. The transformed tree looks like this:

        >>> parse_query(expr).print_tree()
        Intersection
          0 < A < 5
          B == 7

    The third, trickiest case is when neither bound is a child of the current
    node, but both lie further down in the tree.  We know that one bound is in
    the left subtree and one bound is in the right subtree, otherwise we would
    have matched them before getting to the current node.  As an example, let's
    take a look at this unoptimized tree:

        >>> expr = "(A > 0 and B == 2) and (A < 5 and C == 3)"
        >>> _AstParser(expr, {}).query.print_tree()
        Intersection
          Intersection
            A > 0       <-- start
            B == 2      <-- siblings[0]
          Intersection
            A < 5       <-- end
            C == 3      <-- siblings[1]

    In this case, we are not going to find the match between start and end
    until we process the root node of our tree. Both bounds are in subtrees of
    the root node, but are not immediate children. We need to be a bit more
    drastic in how we rearrange the tree. To solve this problem, we group
    together the bounds' siblings and combine them in a new intersection. We
    then replace the parent of start with the new range and we replace the
    parent of end with the intersection of the two siblings. (In this example,
    both start and end share the same grandparent node, but this does not have
    to be the case generally.)  The transformed tree looks like this:

        >>> parse_query(expr).print_tree()
        Intersection
          0 < A < 5
          Intersection
            B == 2
            C == 3

    One other complication remains.  To illustrate, consider this expression:

        >>> expr = "(A > 0 and B > 0 and C > 0) and (A < 5 and B < 5 and C < 5)"
        >>> _AstParser(expr, {}).query.print_tree()
        Intersection
          Intersection
            Intersection
              A > 0
              B > 0
            C > 0
          Intersection
            Intersection
              A < 5
              B < 5
            C < 5

    In this case, ranges for A, B, and C are all going to be found at the root
    node and not before. The order the ranges are processed in depends on dict
    key ordering, but let's presume for a moment that we end up processing A
    first. Our tree after processing A now looks like:

        Intersection
          Intersection
            0 < A < 5
            C > 0
          Intersection
            Intersection  <-- nearest common ancestor to bounds of B
              B > 0
              B < 5
            C < 5

    You can see that the lower bound for B has now been moved over to a
    completely different branch of the tree. Had this tree looked like this
    initially, range B would have been processed as the first case, described
    above, long before we ever got to the current node.. Code which now tries
    to process range B as the third case will break because the relationship
    between the bounds has changed. We can detect this case, though, by
    computing the nearest common ancestor of our bounds before attempting to
    perform any transformations. If the nearest common ancestor is not the
    current node, we know that a transformation performed for another range,
    in this case A, has rearranged the tree. In that case, we can bypass the
    current processing and start a new traversal at the nearest common
    ancestor, replacing the nearest common ancestor with the result of the
    traversal. In the example, above, then, assuming that B is processed next,
    we see that processing the nearest common ancestor to the bounds of B will
    lead us to the first case, where both bounds are immediate children of the
    node being processed. After performing the transformation for range B, our
    tree now looks like:

        Intersection
          Intersection
            0 < A < 5
            C > 0
          Intersection
            0 < B < 5
            C < 5

    We can see now that when we go to process range C, the nearest common
    ancestor of the bounds of C is going to be the root node, so C will be
    processed using the third case where neither bound is an immediate child
    of the node being processed.  The final optimized tree looks like:

        >>> parse_query(expr).print_tree()
        Intersection
          0 < C < 5
          Intersection
            0 < A < 5
            0 < B < 5

    """
    def visit(node, starts, ends):
        # Is this node potentially one half of a range query?
        if isinstance(node, (Gt, Ge)):
            starts[node.index_name] = node
            return node
        elif isinstance(node, (Lt, Le)):
            ends[node.index_name] = node
            return node

        # If a leaf node and not an upper or lower bound, nothing to do.
        elif not isinstance(node, Operator):
            return node

        # Left and right subtrees shouldn't know about each other's potential
        # matches, because we always want to process matches at the nearest
        # common ancestor to both nodes.
        left_starts = starts.copy()
        left_ends = ends.copy()
        node.left = visit(node.left, left_starts, left_ends)

        right_starts = starts.copy()
        right_ends = ends.copy()
        node.right = visit(node.right, right_starts, right_ends)

        if not isinstance(node, Intersection):
            starts.clear()
            ends.clear()
            return node

        # Combine potential matches from left and right subtrees so we can
        # look for matches.
        starts.update(left_starts)
        starts.update(right_starts)
        ends.update(left_ends)
        ends.update(right_ends)
        for index_name in starts.keys():
            if index_name not in ends:
                continue

            # Found a match
            start = starts.pop(index_name)
            end = ends.pop(index_name)

            # Tree may have gotten rearranged such that current node is no
            # longer the nearest common ancestor of start and end. If this is
            # the case, process the subtree rooted at the nearest common
            # ancestor of the matching nodes and replace nce with the result.
            nce = _nearest_common_ancestor(start, end)
            if nce is not node:
                setattr(nce.__parent__, nce.__name__, visit(nce, {}, {}))
                continue

            range_query = Range.fromGTLT(start, end)

            # Case 1: Both bounds are immediate children of this node
            if start.__parent__ is end.__parent__ is node:
                return range_query

            # Case 2: One bound is an immediate child of this node, and one
            # child is a descendent
            elif start.__parent__ is node or end.__parent__ is node:
                if start.__parent__ is node:
                    child = start
                    nephew = end
                else:
                    child = end
                    nephew = start

                if child.__name__ == 'left':
                    node.left = range_query
                else:
                    node.right = range_query

                brother = nephew.__parent__
                if nephew.__name__ == 'left':
                    other_nephew = brother.right
                else:
                    other_nephew = brother.left
                setattr(brother.__parent__, brother.__name__, other_nephew)

            # Case 3: Neither bound is an immediate child of this node
            else:
                siblings = []
                for bound in start, end:
                    if bound.__name__ == 'left':
                        siblings.append(bound.__parent__.right)
                    else:
                        siblings.append(bound.__parent__.left)
                other = Intersection(*siblings)
                start_parent = start.__parent__
                end_parent = end.__parent__
                setattr(start_parent.__parent__, start_parent.__name__,
                        range_query)
                setattr(end_parent.__parent__, end_parent.__name__, other)

        return node

    return visit(tree, {}, {})

def _nearest_common_ancestor(n1, n2):
    n1_ancestors = set([n1])
    n2_ancestors = set([n2])
    while n1.__parent__ is not None or n2.__parent__ is not None:
        if n1 in n2_ancestors:
            return n1
        elif n2 in n1_ancestors:
            return n2

        if n1.__parent__ is not None:
            n1 = n1.__parent__
            n1_ancestors.add(n1)

        if n2.__parent__ is not None:
            n2 = n2.__parent__
            n2_ancestors.add(n2)
    assert n1 is n2, "Nodes are not part of same tree."
    return n1

def _optimize_query(tree):
    tree = _group_any_and_all(tree)
    tree = _make_ranges(tree)
    return tree

def parse_query(expr, names=None):
    """
    Parses the given expression string into a catalog query.  The `names` dict
    provides local variable names that can be used in the expression.
    """
    if names is None:
        names = {}
    return _optimize_query(_AstParser(expr, names).query)

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
