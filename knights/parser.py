import ast
from importlib import import_module

from .lexer import TokenType, tokenise


def wrap_name_in_context(name):
    return ast.Subscript(
        value=ast.Name(id='context', ctx=ast.Load()),
        slice=ast.Index(value=ast.Str(s=name.id)),
        ctx=ast.Load(),
    )


class VarVisitor(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id == 'helpers':
            return node
        return wrap_name_in_context(node)


class Parser:
    def __init__(self, src):
        self.stream = tokenise(src)
        self.parent = None
        self.methods = []
        self.tags = {}
        self.helpers = {}

    def load_library(self, path):
        '''
        Load a template library into the state.
        '''
        module = import_module(path)
        self.tags.update(module.register.tags)
        self.helpers.update(module.register.helpers)

    def build_method(self, name, endnodes=None):
        # Build the body
        if endnodes:
            body, _ = self.parse_nodes_until(*endnodes)
        else:
            body = list(self.parse_node())
        # If it's empty include a blank t
        if not body:
            body.append(ast.Expr(value=ast.Yield(value=ast.Str(s=''))))

        # Create the method
        func = ast.FunctionDef(
            name=name,
            args=ast.arguments(
                args=[
                    ast.arg(arg='self', annotation=None),
                    ast.arg(arg='context', annotation=None),
                ],
                vararg=None,
                kwonlyargs=[],
                kwarg=None,
                defaults=[],
                kw_defaults=[],
            ),
            body=body,
            decorator_list=[],
        )

        self.methods.append(func)

        return func

    def parse_node(self, endnodes=None):
        for token in self.stream:
            if token.mode == TokenType.text:
                node = ast.Yield(value=ast.Str(s=token.token))
            elif token.mode == TokenType.var:
                code = self.parse_expression(token.token)
                node = ast.Yield(value=code)
            elif token.mode == TokenType.block:
                bits = token.token.strip().split(' ', 1)
                tag_name = bits.pop(0).strip()
                if endnodes and tag_name in endnodes:
                    yield tag_name
                    return
                func = self.tags[tag_name]
                node = func(self, *bits)
            else:
                # Must be a comment
                continue

            if node is None:
                continue
            if isinstance(node, (ast.Yield, ast.YieldFrom)):
                node = ast.Expr(value=node, lineno=token.lineno)
            yield node

    def parse_nodes_until(self, *endnodes):
        '''
        '''
        nodes = list(self.parse_node(endnodes=endnodes))
        end = nodes.pop()
        if not isinstance(end, str):
            raise SyntaxError('Did not find end node %e - found %r instead' % (endnodes, end))
        return nodes, end

    def build_class(self):
        return ast.ClassDef(
            name='Template',
            bases=[
                ast.Name(id='parent' if self.parent else 'object', ctx=ast.Load())
            ],
            body=self.methods,
            keywords=[],
            starargs=None,
            kwargs=None,
            decorator_list=[]
        )

    def parse_expression(self, expr):
        code = ast.parse(expr, mode='eval')
        VarVisitor().visit(code)
        return code.body

    def parse_args(self, expr):
        code = ast.parse('x(%s)' % expr, mode='eval')

        return code.body.args, code.body.keywords
