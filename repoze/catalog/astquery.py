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

    def process_Or(self, node, children):
        return query.Or

    def process_And(self, node, children):
        return query.And

    def process_BoolOp(self, node, children):
        operator = children.pop(0)
        index_name = None
        values = []
        operands = []
        not_operands = []
        for subquery in children:
            allowed = query.Query, query.Operator, query.Not
            if not isinstance(subquery, allowed):
                raise ValueError(
                    "Bad expression: operands for %s must be boolean "
                    "expressions or comparisons." % operator.__name__
                )
            if isinstance(subquery, query.Not):
                if operator is query.Or:
                    raise ValueError(
                        "Bad expression: Not may only be used in And expressions."
                    )
                not_operands.append(subquery)
            else:
                operands.append(subquery)

            if isinstance(subquery, query.Query):
                if index_name is None:
                    index_name = subquery.index_name
                elif subquery.index_name != index_name:
                    index_name = _different
                values.append(subquery.value)
            else:
                index_name = _different

        # If all subqueries
        if index_name is not _different:
            if operator is query.Or:
                return query.Any(index_name, values)
            elif operator is query.And:
                return query.All(index_name, values)

        return operator(operands + not_operands)

    def process_Not(self, node, children):
        return query.Not

    def process_UnaryOp(self, node, children):
        operator, operand = children
        if not isinstance(operand, (query.Query, query.Operator)):
            raise ValueError(
                "Bad expression: operand for %s must be a boolean expression "
                "or a comparison." % operator.__name__
            )
        return operator(operand)

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
