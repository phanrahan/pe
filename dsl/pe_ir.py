from enum import Enum

class Atom:
    def __init__(self, _id):
        self._id = _id

    def get_id(self):
        return self._id


class AstNode(Atom):
    def __init__(self, _id):
        super().__init__(_id)


class Variable(Atom):
    class DynamicConfigurationQualifier(Enum):
        DYNAMIC = 0
        CONFIGURATION = 1
        NONE = 2

    class NominalQuantitativeQualifier(Enum):
        NOMINAL = 0
        QUANTITATIVE = 1

    def __init__(self, _id, dynamic_configuration_qualifier,
                 nominal_quantitative_qualifier):
        if not isinstance(dynamic_configuration_qualifier,
                          self.DynamicConfigurationQualifier):
            raise ValueError("dynamic_configuration_qualifier must be "
                             "of type DynamicConfigurationQualifier")
        if not isinstance(nominal_quantitative_qualifier,
                          self.NominalQuantitativeQualifier):
            raise ValueError("nominal_quantitative_qualifier must be "
                             "of type NominalQuantitativeQualifier")
        super().__init__(_id)
        self.dynamic_configuration_qualifier = dynamic_configuration_qualifier
        self.nominal_quantitative_qualifier = nominal_quantitative_qualifier


class InputVariable(Variable):
    def __init__(self, _id, dynamic_configuration_qualifier,
                 nominal_quantitative_qualifier):
        super().__init__(_id, dynamic_configuration_qualifier,
                         nominal_quantitative_qualifier)


class IntermediateVariable(Variable):
    def __init__(self, _id, nominal_quantitative_qualifier, is_output=False):
        super().__init__(_id, Variable.DynamicConfigurationQualifier.NONE,
                         nominal_quantitative_qualifier)
        self.is_output = is_output


class OutputVariable(IntermediateVariable):
    def __init__(self, _id, nominal_quantitative_qualifier):
        super().__init__(_id, nominal_quantitative_qualifier, is_output=True)


class StatefulVariable(Variable):
    def __init__(self, _id, nominal_quantitative_qualifier):
        super().__init__(_id, Variable.DynamicConfigurationQualifier.NONE,
                         nominal_quantitative_qualifier)


class NominalRegisterVariable(StatefulVariable):
    def __init__(self, _id):
        super().__init__(_id, Variable.NominalQuantitativeQualifier.NOMINAL)


class RegisterFileVariable(StatefulVariable):
    def __init__(self, _id, is_memory=False):
        super().__init__(_id, Variable.NominalQuantitativeQualifier.NOMINAL)
        self.is_memory = is_memory


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
