
import ast
from enum import Enum
import re

tag_re = re.compile(
    '|'.join([
        r'{!\s*(?P<load>.+?)\s*!}',
        r'{%\s*(?P<tag>.+?)\s*%}',
        r'{{\s*(?P<var>.+?)\s*}}',
        r'{#\s*(?P<comment>.+?)\s*#}'
    ]),
    re.DOTALL
)


Token = Enum('Token', 'load comment text var block',)


def tokenise(template):
    '''A generator which yields (type, content) pairs'''
    upto = 0
    # XXX Track line numbers and update nodes, so we can annotate the code
    for m in tag_re.finditer(template):
        start, end = m.span()
        if upto < start:
            yield (Token.text, template[upto:start])
        upto = end
        load, tag, var, comment = m.groups()
        if load is not None:
            yield (Token.load, tag)
        elif tag is not None:
            yield (Token.block, tag)
        elif var is not None:
            yield (Token.var, var)
        else:
            yield (Token.comment, comment)
    if upto < len(template):
        yield (Token.text, template[upto:])


class Node(object):
    def __init__(self, token, stream):
        self.token = token
        self.nodelist = []

    def render(self, context):
        return ''


class TextNode(Node):

    def render(self, context):
        return self.token


class VarNode(Node):
    def __init__(self, token, stream):
        super().__init__(token, stream)

        code = ast.parse(token, mode='eval')
        # XXX The magicks happen here

        self.code = compile(code, filename='<template>', mode='eval')

    def render(self, context):
        global_ctx = dict(context)
        return eval(self.code, global_ctx, {})


class BlockNode(Node):
    pass


def parse(source):
    stream = tokenise(source)

    nodelist = []

    for mode, token in stream:
        if mode == Token.load:
            pass
        elif mode == Token.text:
            node = TextNode(token, stream)
        elif mode == Token.var:
            node = VarNode(token, stream)
        elif mode == Token.block:
            # magicks go here
            node = BlockNode(token, stream)
        else:
            # Must be a comment
            continue

        nodelist.append(node)

    return nodelist
