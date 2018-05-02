from pe_ir_atom import Atom
from pe_ir_types import *


class AstNode(Atom):
    def __init__(self, _id):
        super().__init__(_id)


class Literal(Atom):
    def __init__(self, _id, _type):
        if not TypeUtils.is_base_type(_type):
            raise ValueError("_type must be a base type")
        self._type = _type

    def get_type(self):
        return self._type


class Variable(Atom):
    def __init__(self, _id, _type):
        if not isinstance(_type, Type):
            raise ValueError("_type must be a proper IR type")
        super().__init__(_id)
        self._type = _type


class VariableDeclaration(AstNode):
    def __init__(self, variable):
        decl_id = variable.get_id() + "_decl"
        super().__init__(decl_id)
        self.variable = variable


class Operation(Atom):
    def __init__(self, _id, op_id, arguments):
        super().__init__(_id)
        self.op_id = op_id
        self.arguments = arguments


class Expression(Atom):
    def __init__(self, _id, operation):
        super().__init__(_id)
        self.operation = operation


class Assignment(AstNode):
    def __init__(self, _id, lhs, rhs):
        super().__init__(_id)
        self.lhs = lhs
        self.rhs = rhs


class AstContext:
    def __init__(self):
        self.nodes = []
    def add_node(self, node):
        if not isinstance(node, AstNode):
            raise ValueError("node must be a proper AstNode")
        self.nodes.append(node)
