from type_checker import Type, TypeCollector

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

class MyCollector(TypeCollector):
    def visit_Assign(self, node : ast.Assign):
        if len(node.targets) > 1:
            raise NotImplementedError("Assigning to multiple values (e.g. a, b, ... = 0, 1, ...) not supported")
        target = node.targets[0]
        value = node.value
        if isinstance(target, ast.Name) and \
           isinstance(value, ast.Call) and \
           isinstance(value.func, ast.Name) and \
           value.func.id in self.type_names:
               self.type_table[target.id] = value

def test_inputs():

    collector = MyCollector([Input, Output])

    def test_func():
        a = Input(8)
        b = Output(8)

    test_func_ast = get_ast(test_func)
    collector.visit(test_func_ast)
    print(collector.type_table)
    assert {key: ast.dump(value) for key, value in collector.type_table.items()} == {
        "a": "Call(func=Name(id='Input', ctx=Load()), args=[Num(n=8)], keywords=[])",
        "b": "Call(func=Name(id='Output', ctx=Load()), args=[Num(n=8)], keywords=[])"
    }
