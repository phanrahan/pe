from enum import Enum
from pe_ir_atom import Atom

class Type(Atom):
    def __init__(self, _id):
        super().__init__(_id)


class EnumType(Type):
    def __init__(self, _id, value_set):
        super().__init__(_id)
        self.value_set = value_set

    def get_value_set(self):
        return self.value_set


class BitVectorType(Type):
    def __init__(self, _id, width):
        super().__init__(_id)
        self.width = width

    def get_width(self):
        return self.width


class NominalType(EnumType):
    def __init__(self, _id, value_set):
        if not isinstance(value_set, set):
            raise ValueError("value_set must be a python set")
        super().__init__(_id, value_set)


class QuantitativeType(BitVectorType):
    def __init__(self, _id, width):
        super().__init__(_id, width)


class NestedType(Type):
    def __init__(self, _id, base_type):
        if type(base_type) != NominalType and \
           type(base_type) != QuantitativeType:
            raise ValueError("base_type must either be of type NominalType "
                             "or QuantitativeType")
        super().__init__(_id)
        self.base_type = base_type

    def get_base_type(self):
        return self.base_type


class InputType(NestedType):
    class DynamicQualifier(Enum):
        DYNAMIC = 0
        CONFIGURATION = 1

    def __init__(self, _id, base_type, dynamic_qualifier):
        super().__init__(_id, base_type)
        self.dynamic_qualifier = dynamic_qualifier

    def get_dynamic_qualifier(self):
        return self.dynamic_qualifier


class IntermediateType(NestedType):
    def __init__(self, _id, base_type, is_output=False):
        super().__init__(_id, base_type)
        self.is_output = is_output

    def get_is_output(self):
        return self.is_output


class OutputType(IntermediateType):
    def __init__(self, _id, base_type):
        super().__init__(_id, base_type, True)


class NominalRegisterType(NominalType):
    def __init__(self, _id, value_set):
        super().__init__(_id, value_set)


class QuantitativeRegisterFileType(Type):
    def __init__(self, _id, width, height, is_memory=False):
        super().__init__(_id)
        if not isinstance(is_memory, bool):
            raise ValueError("is_memory must be a bool")
        self.is_memory = is_memory
        self.width = width
        self.height = height

    def get_is_memory(self):
        return self.is_memory


class MemoryType(QuantitativeRegisterFileType):
    def __init__(self, _id):
        super().__init__(_id, True)


class TypeUtils:
    def __init__(self):
        pass

    def is_base_type(_type):
        return type(_type) in [BitVectorType, EnumType]
