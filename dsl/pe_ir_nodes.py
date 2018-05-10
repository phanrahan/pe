from pe_ir_atom import Atom
from pe_ir_ops import *
from pe_ir_types import *


class IrNode(Atom):
    def __init__(self):
        super().__init__()


class Literal(IrNode):
    def __init__(self, _type, value):
        super().__init__()
        self._type = _type
        self.value = value

    def get_type(self):
        return self._type

    def get_value(self):
        return self.value


class VariableDeclaration(IrNode):
    def __init__(self, _id, _type):
        super().__init__()
        self._id = _id
        self._type = _type

    def get_id(self):
        return self._id

    def get_type(self):
        return self._type


class Name(IrNode):
    def __init__(self, _id):
        super().__init__()
        self._id = _id

    def get_id(self):
        return self._id


class Operation(IrNode):
    def __init__(self, op, arguments):
        super().__init__()
        self.op = op
        self.arguments = arguments

    def get_op(self):
        return self.op

    def get_arguments(self):
        return self.arguments


class Assignment(IrNode):
    def __init__(self, lhs, rhs):
        super().__init__()
        self.lhs = lhs
        self.rhs = rhs

    def get_lhs(self):
        return self.lhs

    def get_rhs(self):
        return self.rhs


class SwitchCase(IrNode):
    def __init__(self, subject, case_map):
        super().__init__()
        self.subject = subject
        self.case_map = case_map

    def get_subject(self):
        return self.subject

    def get_case_map(self):
        return self.case_map


class Ternary(IrNode):
    def __init__(self, condition, true_case, false_case):
        super().__init__()
        self.condition = condition
        self.true_case = true_case
        self.false_case = false_case

    def get_condition(self):
        return self.condition

    def get_true_case(self):
        return self.true_case

    def get_false_case(self):
        return self.false_case


class IrContext:
    def __init__(self):
        self.nodes = []

    def add_node(self, node):
        if not isinstance(node, IrNode):
            raise ValueError("node must be a proper IrNode")
        self.nodes.append(node)

    def get_nodes(self):
        return self.nodes
