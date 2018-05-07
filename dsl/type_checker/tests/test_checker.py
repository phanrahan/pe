from type_checker import Type, TypeCollector, TypeChecker

import ast
import inspect
import textwrap

def get_ast(obj):
    indented_program_txt = inspect.getsource(obj)
    program_txt = textwrap.dedent(indented_program_txt)
    return ast.parse(program_txt)

class Bits(Type):
    def __init__(self, width):
        self.width = width

class Input(Bits):
    pass

class Output(Bits):
    pass

def test_inputs():


    def test_func():
        a = Input(8)
        b = Output(8)
        b = a
        a = b

    test_func_ast = get_ast(test_func)

    class MyChecker(TypeChecker):
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
                    isinstance(type_decl.func, ast.Name) and \
                    type_decl.func.id == "Input"

    def type_check(tree):
        collector = TypeCollector([Input, Output])
        collector.visit(tree)
        checker = MyChecker(collector.type_table)
        checker.visit(tree)

    try:
        type_check(test_func_ast)
        assert False, "Should not reach this statement because there's a type error (assigns to a which is an input)"
    except TypeError as e:
        assert str(e) == "Assigning to an input a - Line Number 5"
        pass

    def no_error():
        a = Input(8)
        b = Output(8)
        b = a

    no_error_ast = get_ast(no_error)

    try:
        type_check(no_error_ast)
    except TypeError as e:
        print(e)
        assert False, "Should not reach this statement because there is no type error"
