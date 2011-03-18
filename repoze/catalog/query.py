import BTrees
import sys

try:
    import ast
    ast_support = True
except ImportError:  # pragma NO COVERAGE
    ast_support = False


class Query(object):
    """
    Base class for all elements that make up queries.
    """
    __parent__ = None
    __name__ = None

    def __and__(self, right):
        self._check_type("and", right)
        return And(self, right)

    def __or__(self, right):
        self._check_type("or", right)
        return Or(self, right)

    def _check_type(self, setop, operand):
        if not isinstance(operand, Query):
            raise TypeError(
                "TypeError: unsupported operand types for %s: %s %s" %
                (setop, type(self), type(operand))
            )

    def iter_children(self):
        return ()

    def print_tree(self, out=sys.stdout, level=0):
        print >>out, '  ' * level + str(self)
        for child in self.iter_children():
            child.print_tree(out, level + 1)

    def _optimize(self):
        """
        If subtree represented by this node can be transformed into a more
        optimal subtree, return the transformed subtree, otherwise return self.
        """
        return self


class Comparator(Query):
    """
    Base class for all comparators used in queries.
    """
    def __init__(self, index_name, value):
        self.index_name = index_name
        self._value = value

    def _get_index(self, catalog):
        return catalog[self.index_name]

    def _get_value(self, names):
        value = self._value
        if isinstance(value, Name):
            name = value.name
            if name not in names:
                raise NameError("No value passed in for name: %s" % name)
            return names[name]
        return value

    def __str__(self):
        return ' '.join((self.index_name, self.operator, repr(self._value)))

    def __eq__(self, other):
        return (self.index_name == other.index_name and
                self._value == other._value)


class Contains(Comparator):
    """Contains query.

    CQE equivalent: 'foo' in index
    """

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyContains(self._get_value(names))

    def __str__(self):
        return '%s in %s' % (repr(self._value), self.index_name)

    def negate(self):
        return DoesNotContain(self.index_name, self._value)


class DoesNotContain(Comparator):
    """CQE equivalent: 'foo' not in index
    """

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyDoesNotContain(self._get_value(names))

    def __str__(self):
        return '%s not in %s' % (repr(self._value), self.index_name)

    def negate(self):
        return Contains(self.index_name, self._value)


class Eq(Comparator):
    """Equals query.

    CQE equivalent:  index == 'foo'
    """
    operator = '=='

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyEq(self._get_value(names))

    def negate(self):
        return NotEq(self.index_name, self._value)


class NotEq(Comparator):
    """Not equal query.

    CQE eqivalent: index != 'foo'
    """
    operator = '!='

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyNotEq(self._get_value(names))

    def negate(self):
        return Eq(self.index_name, self._value)


class Gt(Comparator):
    """ Greater than query.

    CQE equivalent: index > 'foo'
    """
    operator = '>'

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyGt(self._get_value(names))

    def negate(self):
        return Le(self.index_name, self._value)


class Lt(Comparator):
    """ Less than query.

    CQE equivalent: index < 'foo'
    """
    operator = '<'

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyLt(self._get_value(names))

    def negate(self):
        return Ge(self.index_name, self._value)


class Ge(Comparator):
    """Greater (or equal) query.

    CQE equivalent: index >= 'foo'
    """
    operator = '>='

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyGe(self._get_value(names))

    def negate(self):
        return Lt(self.index_name, self._value)


class Le(Comparator):
    """Less (or equal) query.

    CQE equivalent: index <= 'foo
    """
    operator = '<='

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyLe(self._get_value(names))

    def negate(self):
        return Gt(self.index_name, self._value)


class Any(Comparator):
    """Any of query.

    CQE equivalent: index in any(['foo', 'bar'])
    """

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyAny(self._get_value(names))

    def negate(self):
        return NotAny(self.index_name, self._value)

    def __str__(self):
        return '%s in any(%s)' % (self.index_name, repr(self._value))


class NotAny(Comparator):
    """Not any of query (ie, None of query)

    CQE equivalent: index not in any(['foo', 'bar'])
    """
    operator = 'not any'

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyNotAny(self._get_value(names))

    def negate(self):
        return Any(self.index_name, self._value)

    def __str__(self):
        return '%s not in any(%s)' % (self.index_name, repr(self._value))

class All(Comparator):
    """All query.

    CQE equivalent: index in all(['foo', 'bar'])
    """
    operator = 'all'

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyAll(self._get_value(names))

    def negate(self):
        return NotAll(self.index_name, self._value)

    def __str__(self):
        return '%s in all(%s)' % (self.index_name, repr(self._value))

class NotAll(Comparator):
    """NotAll query.

    CQE equivalent: index not in all(['foo', 'bar'])
    """
    operator = 'not all'

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyAll(self._get_value(names))

    def negate(self):
        return All(self.index_name, self._value)

    def __str__(self):
        return '%s not in all(%s)' % (self.index_name, repr(self._value))

class _Range(Comparator):
    @classmethod
    def fromGTLT(cls, start, end):
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
        return cls(start.index_name, start._value, end._value,
                   start_exclusive, end_exclusive)

    def __init__(self, index_name, start, end,
                 start_exclusive=False, end_exclusive=False):
        self.index_name = index_name
        self._start = start
        self._end = end
        self.start_exclusive = start_exclusive
        self.end_exclusive = end_exclusive

    def _get_start(self, names):
        value = self._start
        if isinstance(value, Name):
            name = value.name
            if name not in names:
                raise NameError("No value passed in for name: %s" % name)
            return names[name]
        return value

    def _get_end(self, names):
        value = self._end
        if isinstance(value, Name):
            name = value.name
            if name not in names:
                raise NameError("No value passed in for name: %s" % name)
            return names[name]
        return value

    def __str__(self):
        s = [repr(self._start)]
        if self.start_exclusive:
            s.append('<')
        else:
            s.append('<=')
        s.append(self.index_name)
        if self.end_exclusive:
            s.append('<')
        else:
            s.append('<=')
        s.append(repr(self._end))
        return ' '.join(s)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return (self.index_name == other.index_name and
                self._start == other._start and
                self._end == other._end and
                self.start_exclusive == other.start_exclusive and
                self.end_exclusive == other.end_exclusive)


class InRange(_Range):
    """ Index value falls within a range.

    CQE eqivalent: lower < index < upper
                   lower <= index <= upper
    """

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyInRange(
            self._get_start(names), self._get_end(names),
            self.start_exclusive, self.end_exclusive
        )

    def negate(self):
        return NotInRange(self.index_name, self._start, self._end,
                          self.start_exclusive, self.end_exclusive)


class NotInRange(_Range):
    """ Index value falls outside a range.

    CQE eqivalent: not(lower < index < upper)
                   not(lower <= index <= upper)
    """

    def _apply(self, catalog, names):
        index = self._get_index(catalog)
        return index.applyNotInRange(
            self._get_start(names), self._get_end(names),
            self.start_exclusive, self.end_exclusive
        )

    def __str__(self):
        return 'not(%s)' % _Range.__str__(self)

    def negate(self):
        return InRange(self.index_name, self._start, self._end,
                       self.start_exclusive, self.end_exclusive)


class BoolOp(Query):
    """
    Base class for Or and And operators.
    """
    family = BTrees.family32

    def __init__(self, *queries):
        arguments = []
        for query in queries:
            # If argument is of the same type, can promote its arguments up
            # to here.
            if type(query) == type(self):
                arguments.extend(query.queries)
            else:
                arguments.append(query)
        self.queries = arguments

    def __str__(self):
        return type(self).__name__

    def iter_children(self):
        for query in self.queries:
            yield query

    def _optimize(self):
        self.queries = [query._optimize() for query in self.queries]
        new_me = self._optimize_eq()
        if new_me is not None:
            return new_me
        new_me = self._optimize_not_eq()
        if new_me is not None:
            return new_me
        return self

    def _optimize_eq(self):
        # If all queries are Eq operators for the same index, we can replace
        # this And or Or with an All or Any node.
        queries = list(self.queries)
        query = queries.pop(0)
        if type(query) != Eq:
            return None
        index_name = query.index_name
        values = [query._value]
        while queries:
            query = queries.pop(0)
            if type(query) != Eq or query.index_name != index_name:
                return None
            values.append(query._value)

        # All queries are Eq operators for the same index.
        if type(self) == Or:
            return Any(index_name, values)
        return All(index_name, values)

    def _optimize_not_eq(self):
        # If all queries are NotEq operators for the same index, we can
        # replace this And or Or with a NotAll or NotAny node.
        queries = list(self.queries)
        query = queries.pop(0)
        if type(query) != NotEq:
            return None
        index_name = query.index_name
        values = [query._value]
        while queries:
            query = queries.pop(0)
            if type(query) != NotEq or query.index_name != index_name:
                return None
            values.append(query._value)

        # All queries are Eq operators for the same index.
        if type(self) == Or:
            return NotAll(index_name, values)
        return NotAny(index_name, values)


class Or(BoolOp):
    """Boolean Or of multiple queries."""
    def _apply(self, catalog, names):
        # XXX Try to figure out when we need weightedOr and when we can
        # just use union or multiunion.
        queries = self.queries
        result = queries[0]._apply(catalog, names)
        for query in queries[1:]:
            next_result = query._apply(catalog, names)
            if len(result) == 0:
                result = next_result
            elif len(next_result) > 0:
                _, result = self.family.IF.weightedUnion(result, next_result)
        return result

    def negate(self):
        neg_queries = [query.negate() for query in self.queries]
        return And(*neg_queries)

    def _optimize(self):
        new_self = BoolOp._optimize(self)
        if self is not new_self:
            return new_self

        # There might be a combination of Gt/Ge and Lt/Le operators for the
        # same index that could be used to compose a NotInRange.
        uppers = {}
        lowers = {}
        queries = list(self.queries)

        def process_range(i_lower, query_lower, i_upper, query_upper):
            queries[i_lower] = NotInRange.fromGTLT(
                query_lower.negate(), query_upper.negate())
            queries[i_upper] = None

        for i in xrange(len(queries)):
            query = queries[i]
            if type(query) in (Lt, Le):
                match = uppers.get(query.index_name)
                if match is not None:
                    i_upper, query_upper = match
                    process_range(i, query, i_upper, query_upper)
                else:
                    lowers[query.index_name] = (i, query)

            elif type(query) in (Gt, Ge):
                match = lowers.get(query.index_name)
                if match is not None:
                    i_lower, query_lower = match
                    process_range(i_lower, query_lower, i, query)
                else:
                    uppers[query.index_name] = (i, query)

        queries = filter(None, queries)
        if len(queries) == 1:
            return queries[0]

        self.queries = queries
        return self


class And(BoolOp):
    """Boolean And of multiple queries."""
    def _apply(self, catalog, names):
        # XXX Try to figure out when we need weightedIntersection and when we
        # can just use intersection.
        IF = self.family.IF
        queries = self.queries
        result = queries[0]._apply(catalog, names)
        for query in queries[1:]:
            if len(result) == 0:
                return IF.Set()
            next_result = query._apply(catalog, names)
            if len(next_result) == 0:
                return IF.Set()
            _, result = IF.weightedIntersection(result, next_result)
        return result

    def negate(self):
        neg_queries = [query.negate() for query in self.queries]
        return Or(*neg_queries)

    def _optimize(self):
        new_self = BoolOp._optimize(self)
        if self is not new_self:
            return new_self

        # There might be a combination of Gt/Ge and Lt/Le operators for the
        # same index that could be used to compose an InRange.
        uppers = {}
        lowers = {}
        queries = list(self.queries)

        def process_range(i_lower, query_lower, i_upper, query_upper):
            queries[i_lower] = InRange.fromGTLT(query_lower, query_upper)
            queries[i_upper] = None

        for i in xrange(len(queries)):
            query = queries[i]
            if type(query) in (Gt, Ge):
                match = uppers.get(query.index_name)
                if match is not None:
                    i_upper, query_upper = match
                    process_range(i, query, i_upper, query_upper)
                else:
                    lowers[query.index_name] = (i, query)

            elif type(query) in (Lt, Le):
                match = lowers.get(query.index_name)
                if match is not None:
                    i_lower, query_lower = match
                    process_range(i_lower, query_lower, i, query)
                else:
                    uppers[query.index_name] = (i, query)

        queries = filter(None, queries)
        if len(queries) == 1:
            return queries[0]

        self.queries = queries
        return self


class Not(Query):
    """Negation of a query."""
    def __init__(self, query):
        self.query = query

    def __str__(self):
        return 'Not'

    def iter_children(self):
        yield self.query

    def negate(self):
        return self.query

    def _apply(self, catalog, names):
        return self.query.negate()._apply(catalog, names)

    def _optimize(self):
        return self.query.negate()._optimize()


class Name(object):
    """
    A variable name in an expression, evaluated at query time.  Can be used
    to defer evaluation of variables used inside of expressions until query
    time.

    Example::

        from repoze.catalog.query import Eq
        from repoze.catalog.query import Name

        # Define query at module scope
        find_cats = Eq('color', Name('color')) & Eq('sex', Name('sex'))

        # Use query in a search function, evaluating color and sex at the
        # time of the query
        def search_cats(catalog, resolver, color='tabby', sex='female'):
            # Let resolver be some function which can retrieve a cat object
            # from your application given a docid.
            params = dict(color=color, sex=sex)
            count, docids = catalog.query(find_cats, params)
            for docid in docids:
                yield resolver(docid)

    """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.name)

    __str__ = __repr__

    def __eq__(self, right):
        if isinstance(right, Name):
            return right.name == self.name
        return False


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
    def __init__(self, expr):
        self.expr = expr

    def parse(self):
        statements = ast.parse(self.expr).body
        if len(statements) > 1:
            raise ValueError(
                "Can only process single expression."
            )
        expr_tree = statements[0]
        if not isinstance(expr_tree, ast.Expr):
            raise ValueError(
                "Not an expression."
            )

        result = self.walk(expr_tree.value)
        return result

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
        return self.process_comparator(Eq)

    def process_NotEq(self, node, children):
        return self.process_comparator(NotEq)

    def process_Lt(self, node, children):
        return self.process_comparator(Lt)

    def process_LtE(self, node, children):
        return self.process_comparator(Le)

    def process_Gt(self, node, children):
        return self.process_comparator(Gt)

    def process_GtE(self, node, children):
        return self.process_comparator(Ge)

    def process_comparator(self, cls):
        def factory(left, right):
            return cls(self._index_name(left), self._value(right))
        factory.type = cls
        return factory

    def process_In(self, node, children):
        def factory(left, right):
            if callable(right):  # any or all, see process_Call
                return right(self._index_name(left))
            return Contains(self._index_name(right), self._value(left))
        factory.type = Contains
        return factory

    def process_NotIn(self, node, children):
        def factory(left, right):
            if callable(right):  # any or all, see process_Call
                return right(self._index_name(left)).negate()
            return DoesNotContain(self._index_name(right), self._value(left))
        factory.type = DoesNotContain
        return factory

    def process_Not(self, node, children):
        return Not

    def process_UnaryOp(self, node, children):
        operator, query = children
        return operator(query)

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
        # Where the second form maps to an InRange comparator and the first
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
                return InRange(self._index_name(index_name),
                               self._value(start),
                               self._value(end),
                               start_exclusive,
                               end_exclusive)
        raise ValueError(
            "Bad expression: unsupported chaining of comparators."
        )

    def process_BitOr(self, node, children):
        return Or

    def process_BitAnd(self, node, children):
        return And

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
        return Or

    def process_And(self, node, children):
        return And

    def process_BoolOp(self, node, children):
        operator = children.pop(0)
        for child in children:
            if not isinstance(child, Query):
                raise ValueError(
                    "Bad expression: All operands for %s must be result sets."
                    % operator.__name__)

        return operator(*children)

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
            return Name(node.id)
        return node


def optimize(query):
    if isinstance(query, Query):
        return query._optimize()
    return query


def parse_query(expr, optimize_query=True):
    """
    Parses the given expression string and returns a query object.  Requires
    Python >= 2.6.
    """
    if not ast_support:
        raise NotImplementedError("Parsing of CQEs requires Python >= 2.6")
    query = _AstParser(expr).parse()
    if optimize_query:
        query = optimize(query)
    return query


def _print_ast(expr):  # pragma NO COVERAGE
    """
    Useful method for visualizing AST trees while debugging.
    """
    tree = ast.parse(expr)

    def visit(node, level):
        print '  ' * level + str(node)
        for child in ast.iter_child_nodes(node):
            visit(child, level + 1)
    visit(tree, 0)
