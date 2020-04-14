import ast
import re

from . import banner
from . import utils

class Preprocessor:
    """
    """

    def __init__(self, code, num_lines):
        self.code = code
        self.ast = ast.parse(code)
        self.num_lines = num_lines
        self.lambdas_by_line = {}

    def preprocess(self):
        self.log_lambdas()
        self.wrap_calls()
        self.encode_lambdas()
        ast.fix_missing_locations(self.ast)
        self.ast = compile(
            self.ast,
            filename='main.py', # TODO: Why is `__name__` bound to `'builtins'`?
            mode='exec',
        )

    def log_lambdas(self):
        lambda_logger = LambdaLogger(self.lambdas_by_line)
        lambda_logger.visit(self.ast)

    def wrap_calls(self):
        call_wrapper = CallWrapper(self.code)
        self.ast = call_wrapper.visit(self.ast)

    def encode_lambdas(self):
        for lineno in self.lambdas_by_line:
            sorted_lambdas = sorted(self.lambdas_by_line[lineno], key=lambda node: node.col_offset)
            for i, node in enumerate(sorted_lambdas):
                node.lineno = utils.pair_naturals(node.lineno, i + 1, max_x=self.num_lines)

class LambdaLogger(ast.NodeVisitor):
    """
    """

    def __init__(self, lambdas_by_line):
        super().__init__()
        self.lambdas_by_line = lambdas_by_line

    def visit_Lambda(self, node):
        lineno = node.lineno
        if lineno not in self.lambdas_by_line:
            self.lambdas_by_line[lineno] = []
        self.lambdas_by_line[lineno].append(node)
        self.generic_visit(node)

class CallWrapper(ast.NodeTransformer):
    """
    <summary>
    """

    def __init__(self, code):
        super().__init__()
        self.code = code
        self.id_counter = 0

    def visit_Call(self, node):
        """
        <summary>

        :param node: An ast.Call node representing some function call `f(x)`.
        :return: An ast.Call node representing `nop(nop(flag_info, id), f(x), id)`
            where `flag_info` is the information required by the flag banner, and
            `id` uniquely identifies the flag.
        """

        # Or I guess more accurately ...
        # f(...) --> (lambda banner, call: call)(
        #                (lambda: flag_info)(),
        #                f(...),
        #            )

        # TODO: Are there nodes other than Call nodes (eg listcomp, dictcomp, etc) that create their own frames? If so, we need to mutate those too. And also flag_info bitmap should account for them too (not just Call nodes).

        inner_lambda = ast.Lambda(
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                vararg=None,
                kwonlyargs=[],
                kwarg=None,
                defaults=[],
                kw_defaults=[],
            ),
            body=banner.Banner(self.code, node).banner,
        )
        outer_lambda = ast.Lambda(
            args=ast.arguments(
                posonlyargs=[],
                args=[
                    ast.arg(arg='banner', annotation=None),
                    ast.arg(arg='call', annotation=None),
                ],
                vararg=None,
                kwonlyargs=[],
                kwarg=None,
                defaults=[],
                kw_defaults=[],
            ),
            body=ast.Name(id='call', ctx=ast.Load()),
        )
        inner_call = ast.Call(
            func=inner_lambda,
            args=[],
            keywords=[],
            lineno=utils.INNER_CALL_LINENO,
            col_offset=self.id_counter,
        )
        outer_call = ast.Call(
            func=outer_lambda,
            args=[
                inner_call,
                node,
            ],
            keywords=[],
            lineno=utils.OUTER_CALL_LINENO,
            col_offset=self.id_counter,
        )
        self.id_counter += 1 # An outer_call and inner_call correspond to one another iff they have the same ID. (But at the moment we don't actually use that information; we just have it there bc it's nice.)
        self.generic_visit(node)
        return outer_call
