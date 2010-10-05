import ast
import sys

from repoze.catalog import query

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
        return query.Eq

    def process_NotEq(self, node, children):
        return query.NotEq

    def process_Lt(self, node, children):
        return query.Lt

    def process_LtE(self, node, children):
        return query.Le

    def process_Gt(self, node, children):
        return query.Gt

    def process_GtE(self, node, children):
        return query.Ge

    def process_In(self, node, children):
        return query.Contains

    def process_Compare(self, node, children):
        operand1, operator, operand2 = children
        if operator is query.Contains:
            return operator(self._index_name(operand2), self._value(operand1))
        return operator(self._index_name(operand1), self._value(operand2))

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

    def process_BitOr(self, node, children):
        return query.Union

    def process_BitAnd(self, node, children):
        return query.Intersection

    def process_Sub(self, node, children):
        return query.Difference

    def process_BinOp(self, node, children):
        left, operator, right = children
        if not isinstance(left, (query.Query, query.Operator)):
            raise ValueError(
                "Bad expression: left operand for union must be a result set.",
                left
            )
        if not isinstance(right, (query.Query, query.Operator)):
            raise ValueError(
                "Bad expression: right operand for union must be a result set."
            )
        return operator(left, right)

_notset = object()
_different = object()

def parse_query(expr, names=None):
    """
    Parses the given expression string into a catalog query.  The `names` dict
    provides local variable names that can be used in the expression.
    """
    if names is None:
        names = {}
    return _AstQuery(expr, names).query
