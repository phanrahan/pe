import ast


class Type:
    pass


class TypeVisitor(ast.NodeVisitor):
    pass

class TypeCollector(TypeVisitor):
    def __init__(self, types : list):
        self.type_names = {type_.__name__ for type_ in types}
        self.type_table = {}

class TypeChecker(ast.NodeVisitor):
    def __init__(self, type_table):
        self.type_table = type_table
        self.type_names = [value.func.id for value in self.type_table.values()]
