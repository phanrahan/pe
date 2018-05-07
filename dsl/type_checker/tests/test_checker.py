from type_checker import Type, TypeChecker
import ast
from .test_collector import get_ast, Bits, Input, Output, MyCollector

class MyChecker(TypeChecker):
    """
    Checks that we never assign to an input such as:
        a = Input()
        b = Output()
        a = b
    """
    def visit_Assign(self, node : ast.Assign):
        if len(node.targets) > 1:
            raise NotImplementedError("Assigning to multiple values (e.g. a, b, ... = 0, 1, ...) not supported")
        target = node.targets[0]
        value = node.value
        if isinstance(target, ast.Name) and \
           not isinstance(value, ast.Call) or \
           not isinstance(value.func, ast.Name) or \
           not value.func.id in self.type_names:
               if self.is_input(self.type_table[target.id]):
                   # TODO: Lookup line in original function source to print
                   # out prettier error message
                   raise TypeError(f"Assigning to an input {target.id} - Line Number {target.lineno}")

    def is_input(self, type_decl):
        return isinstance(type_decl, ast.Call) and \

def type_check(tree):
    """
    Collect type declarations using `MyCollector`, check types using
    `MyChecker`
    """
    collector = MyCollector([Input, Output])
    collector.visit(tree)
    checker = MyChecker(collector.type_table)
    checker.visit(tree)

def bad_test_func():
    a = Input(8)
    b = Output(8)
    b = a
    a = b  # assign to input

def good_test_func():
    a = Input(8)
    b = Output(8)
    b = a

def test_bad_func():
    bad_test_func_ast = get_ast(bad_test_func)
                    isinstance(type_decl.func, ast.Name) and \
                    type_decl.func.id == "Input"

    try:
        type_check(bad_test_func_ast)
        assert False, "Should not reach this statement because there's a type error (assigns to a which is an input)"
    except TypeError as e:
        assert str(e) == "Assigning to an input a - Line Number 5"
        pass


def test_good_func():
    good_test_func_ast = get_ast(good_test_func)

    try:
        type_check(good_test_func_ast)
    except TypeError as e:
        print(e)
        assert False, "Should not reach this statement because there is no type error"
