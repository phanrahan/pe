import ast


class Type:
    pass


class TypeVisitor(ast.NodeVisitor):
    pass

class TypeCollector(TypeVisitor):
    def __init__(self, types : list):
        self.type_names = {type_.__name__ for type_ in types}
        self.type_table = {}

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

class TypeChecker(ast.NodeVisitor):
    def __init__(self, type_table):
        self.type_table = type_table
        self.type_names = [value.func.id for value in self.type_table.values()]
