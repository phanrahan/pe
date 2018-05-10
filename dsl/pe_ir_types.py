from enum import Enum
from pe_ir_atom import Atom

class Type(Atom):
    def __init__(self):
        super().__init__()


class EnumType(Type):
    def __init__(self, value_set):
        super().__init__()
        self.value_set = value_set

    def get_value_set(self):
        return self.value_set


class BitVectorType(Type):
    def __init__(self, width):
        super().__init__()
        self.width = width

    def get_width(self):
        return self.width


class NominalType(EnumType):
    # @value_set should be a python set.
    def __init__(self, value_set):
        super().__init__(value_set)


class QuantitativeType(BitVectorType):
    def __init__(self, width):
        super().__init__(width)


class NestedType(Type):
    # @base_type should be either of type NominalType of QuantitativeType.
    def __init__(self, base_type):
        super().__init__()
        self.base_type = base_type

    def get_base_type(self):
        return self.base_type


class InputType(NestedType):
    class DynamicQualifier(Enum):
        DYNAMIC = 0
        CONFIGURATION = 1

    def __init__(self, base_type, dynamic_qualifier):
        super().__init__(base_type)
        self.dynamic_qualifier = dynamic_qualifier

    def get_dynamic_qualifier(self):
        return self.dynamic_qualifier


class IntermediateType(NestedType):
    def __init__(self, base_type, is_output=False):
        super().__init__(base_type)
        self.is_output = is_output

    def get_is_output(self):
        return self.is_output


class OutputType(IntermediateType):
    def __init__(self, base_type):
        super().__init__(base_type, True)


class NominalRegisterType(NominalType):
    def __init__(self, value_set):
        super().__init__(value_set)


class QuantitativeRegisterFileType(Type):
    def __init__(self, width, height, is_memory=False):
        super().__init__()
        self.width = width
        self.height = height
        self.is_memory = is_memory

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_is_memory(self):
        return self.is_memory


class MemoryType(QuantitativeRegisterFileType):
    def __init__(self, width, height):
        super().__init__(width, height, True)
