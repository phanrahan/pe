from type_checker import Type, TypeCollector

import ast
import inspect
import textwrap

def get_ast(obj):
    indented_program_txt = inspect.getsource(obj)
    program_txt = textwrap.dedent(indented_program_txt)
    return ast.parse(program_txt)

def test_inputs():
    class Bits(Type):
        def __init__(self, width):
            self.width = width

    class Input(Bits):
        pass

    class Output(Bits):
        pass

    collector = TypeCollector([Input, Output])

    def test_func():
        a = Input(8)
        b = Output(8)

    test_func_ast = get_ast(test_func)
    collector.visit(test_func_ast)
    print(collector.type_table)
    assert {ast.dump(key): ast.dump(value) for key, value in collector.type_table.items()} == {
        "Name(id='a', ctx=Store())": "Call(func=Name(id='Input', ctx=Load()), args=[Num(n=8)], keywords=[])",
        "Name(id='b', ctx=Store())": "Call(func=Name(id='Output', ctx=Load()), args=[Num(n=8)], keywords=[])"
    }


