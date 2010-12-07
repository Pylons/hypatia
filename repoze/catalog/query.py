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
        self.value = value

    def get_index(self, catalog):
        return catalog[self.index_name]

    def __str__(self):
        return ' '.join((self.index_name, self.operator, repr(self.value)))

    def __eq__(self, other):
        return (self.index_name == other.index_name and
                self.value == other.value)


class Contains(Comparator):
    """Contains query.

    CQE equivalent: 'foo' in index
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyContains(self.value)

    def __str__(self):
        return '%s in %s' % (repr(self.value), self.index_name)

    def negate(self):
        return DoesNotContain(self.index_name, self.value)


class DoesNotContain(Comparator):
    """CQE equivalent: 'foo' not in index
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyDoesNotContain(self.value)

    def __str__(self):
        return '%s not in %s' % (repr(self.value), self.index_name)

    def negate(self):
        return Contains(self.index_name, self.value)


class Eq(Comparator):
    """Equals query.

    CQE equivalent:  index == 'foo'
    """
    operator = '=='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyEq(self.value)

    def negate(self):
        return NotEq(self.index_name, self.value)


class NotEq(Comparator):
    """Not equal query.

    CQE eqivalent: index != 'foo'
    """
    operator = '!='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyNotEq(self.value)

    def negate(self):
        return Eq(self.index_name, self.value)


class Gt(Comparator):
    """ Greater than query.

    CQE equivalent: index > 'foo'
    """
    operator = '>'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyGt(self.value)

    def negate(self):
        return Le(self.index_name, self.value)


class Lt(Comparator):
    """ Less than query.

    CQE equivalent: index < 'foo'
    """
    operator = '<'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyLt(self.value)

    def negate(self):
        return Ge(self.index_name, self.value)


class Ge(Comparator):
    """Greater (or equal) query.

    CQE equivalent: index >= 'foo'
    """
    operator = '>='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyGe(self.value)

    def negate(self):
        return Lt(self.index_name, self.value)


class Le(Comparator):
    """Less (or equal) query.

    CQE equivalent: index <= 'foo
    """
    operator = '<='

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyLe(self.value)

    def negate(self):
        return Gt(self.index_name, self.value)


class Any(Comparator):
    """Any of query.

    CQE equivalent: index in any(['foo', 'bar'])
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyAny(self.value)

    def negate(self):
        return NotAny(self.index_name, self.value)

    def __str__(self):
        return '%s in any(%s)' % (self.index_name, repr(self.value))


class NotAny(Comparator):
    """Not any of query (ie, None of query)

    CQE equivalent: index not in any(['foo', 'bar'])
    """
    operator = 'not any'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyNotAny(self.value)

    def negate(self):
        return Any(self.index_name, self.value)

    def __str__(self):
        return '%s not in any(%s)' % (self.index_name, repr(self.value))

class All(Comparator):
    """All query.

    CQE equivalent: index in all(['foo', 'bar'])
    """
    operator = 'all'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyAll(self.value)

    def negate(self):
        return NotAll(self.index_name, self.value)

    def __str__(self):
        return '%s in all(%s)' % (self.index_name, repr(self.value))

class NotAll(Comparator):
    """NotAll query.

    CQE equivalent: index not in all(['foo', 'bar'])
    """
    operator = 'not all'

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyAll(self.value)

    def negate(self):
        return All(self.index_name, self.value)

    def __str__(self):
        return '%s not in all(%s)' % (self.index_name, repr(self.value))

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
        return cls(start.index_name, start.value, end.value,
                   start_exclusive, end_exclusive)

    def __init__(self, index_name, start, end,
                 start_exclusive=False, end_exclusive=False):
        self.index_name = index_name
        self.start = start
        self.end = end
        self.start_exclusive = start_exclusive
        self.end_exclusive = end_exclusive

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

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return (self.index_name == other.index_name and
                self.start == other.start and
                self.end == other.end and
                self.start_exclusive == other.start_exclusive and
                self.end_exclusive == other.end_exclusive)


class InRange(_Range):
    """ Index value falls within a range.

    CQE eqivalent: lower < index < upper
                   lower <= index <= upper
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyInRange(
            self.start, self.end, self.start_exclusive, self.end_exclusive
        )

    def negate(self):
        return NotInRange(self.index_name, self.start, self.end,
                          self.start_exclusive, self.end_exclusive)


class NotInRange(_Range):
    """ Index value falls outside a range.

    CQE eqivalent: not(lower < index < upper)
                   not(lower <= index <= upper)
    """

    def apply(self, catalog):
        index = self.get_index(catalog)
        return index.applyNotInRange(
            self.start, self.end, self.start_exclusive, self.end_exclusive
        )

    def __str__(self):
        return 'not(%s)' % _Range.__str__(self)

    def negate(self):
        return InRange(self.index_name, self.start, self.end,
                       self.start_exclusive, self.end_exclusive)


class BoolOp(Query):
    """
    Base class for Or and And operators which can have N arguments.
    """
    family = BTrees.family32

    def __init__(self, *args):
        arguments = []
        for arg in args:
            # If argument is of the same type, can promote its arguments up
            # to here.
            if type(arg) == type(self):
                arguments.extend(arg.arguments)
            else:
                arguments.append(arg)
        self.arguments = arguments

    def __str__(self):
        return type(self).__name__

    def iter_children(self):
        for arg in self.arguments:
            yield arg

    def _optimize(self):
        self.arguments = [arg._optimize() for arg in self.arguments]
        new_me = self._optimize_eq()
        if new_me is not None:
            return new_me
        new_me = self._optimize_not_eq()
        if new_me is not None:
            return new_me
        return self

    def _optimize_eq(self):
        # If all arguments are Eq operators for the same index, we can replace
        # this And or Or with an All or Any node.
        args = list(self.arguments)
        arg = args.pop(0)
        if type(arg) != Eq:
            return None
        index_name = arg.index_name
        values = [arg.value]
        while args:
            arg = args.pop(0)
            if type(arg) != Eq or arg.index_name != index_name:
                return None
            values.append(arg.value)

        # All arguments are Eq operators for the same index.
        if type(self) == Or:
            return Any(index_name, values)
        return All(index_name, values)

    def _optimize_not_eq(self):
        # If all arguments are NotEq operators for the same index, we can
        # replace this And or Or with a NotAll or NotAny node.
        args = list(self.arguments)
        arg = args.pop(0)
        if type(arg) != NotEq:
            return None
        index_name = arg.index_name
        values = [arg.value]
        while args:
            arg = args.pop(0)
            if type(arg) != NotEq or arg.index_name != index_name:
                return None
            values.append(arg.value)

        # All arguments are Eq operators for the same index.
        if type(self) == Or:
            return NotAll(index_name, values)
        return NotAny(index_name, values)


class Or(BoolOp):
    """Or of two result sets."""
    def apply(self, catalog):
        # XXX Try to figure out when we need weightedOr and when we can
        # just use union or multiunion.
        arguments = self.arguments
        result = arguments[0].apply(catalog)
        for arg in arguments[1:]:
            next_result = arg.apply(catalog)
            if len(result) == 0:
                result = next_result
            elif len(next_result) > 0:
                _, result = self.family.IF.weightedUnion(result, next_result)
        return result

    def negate(self):
        neg_args = [arg.negate() for arg in self.arguments]
        return And(*neg_args)

    def _optimize(self):
        new_self = BoolOp._optimize(self)
        if self is not new_self:
            return new_self

        # There might be a combination of Gt/Ge and Lt/Le operators for the
        # same index that could be used to compose a NotInRange.
        uppers = {}
        lowers = {}
        args = list(self.arguments)

        def process_range(i_lower, arg_lower, i_upper, arg_upper):
            if arg_lower.value >= arg_upper.value:
                return
            args[i_lower] = NotInRange.fromGTLT(
                arg_lower.negate(), arg_upper.negate())
            args[i_upper] = None

        for i in xrange(len(args)):
            arg = args[i]
            if type(arg) in (Lt, Le):
                match = uppers.get(arg.index_name)
                if match is not None:
                    i_upper, arg_upper = match
                    process_range(i, arg, i_upper, arg_upper)
                else:
                    lowers[arg.index_name] = (i, arg)

            elif type(arg) in (Gt, Ge):
                match = lowers.get(arg.index_name)
                if match is not None:
                    i_lower, arg_lower = match
                    process_range(i_lower, arg_lower, i, arg)
                else:
                    uppers[arg.index_name] = (i, arg)

        args = filter(None, args)
        if len(args) == 1:
            return args[0]

        self.arguments = args
        return self


class And(BoolOp):
    """And of two result sets."""
    def apply(self, catalog):
        # XXX Try to figure out when we need weightedIntersection and when we
        # can just use intersection.
        IF = self.family.IF
        arguments = self.arguments
        result = arguments[0].apply(catalog)
        for arg in arguments[1:]:
            if len(result) == 0:
                return IF.Set()
            next_result = arg.apply(catalog)
            if len(next_result) == 0:
                return IF.Set()
            _, result = IF.weightedIntersection(result, next_result)
        return result

    def negate(self):
        neg_args = [arg.negate() for arg in self.arguments]
        return Or(*neg_args)

    def _optimize(self):
        new_self = BoolOp._optimize(self)
        if self is not new_self:
            return new_self

        # There might be a combination of Gt/Ge and Lt/Le operators for the
        # same index that could be used to compose an InRange.
        uppers = {}
        lowers = {}
        args = list(self.arguments)

        def process_range(i_lower, arg_lower, i_upper, arg_upper):
            if arg_lower.value >= arg_upper.value:
                return
            args[i_lower] = InRange.fromGTLT(arg_lower, arg_upper)
            args[i_upper] = None

        for i in xrange(len(args)):
            arg = args[i]
            if type(arg) in (Gt, Ge):
                match = uppers.get(arg.index_name)
                if match is not None:
                    i_upper, arg_upper = match
                    process_range(i, arg, i_upper, arg_upper)
                else:
                    lowers[arg.index_name] = (i, arg)

            elif type(arg) in (Lt, Le):
                match = lowers.get(arg.index_name)
                if match is not None:
                    i_lower, arg_lower = match
                    process_range(i_lower, arg_lower, i, arg)
                else:
                    uppers[arg.index_name] = (i, arg)

        args = filter(None, args)
        if len(args) == 1:
            return args[0]

        self.arguments = args
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

    def apply(self, catalog):
        return self.query.negate().apply(catalog)

    def _optimize(self):
        return self.query.negate()._optimize()


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
        self.expr = expr
        self.names = names

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
            try:
                return self.names[node.id]
            except:
                raise NameError(node.id)
        return node


def optimize(query):
    if isinstance(query, Query):
        return query._optimize()
    return query


def parse_query(expr, names=None, optimize_query=True):
    """
    Parses the given expression string into a catalog query.  The `names` dict
    provides local variable names that can be used in the expression.
    """
    if not ast_support:
        raise NotImplementedError("Parsing of CQEs requires Python >= 2.6")
    if names is None:
        names = {}
    query = _AstParser(expr, names).parse()
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
