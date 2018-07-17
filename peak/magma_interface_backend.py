import ast
import math
import magma
import backend
import peak_ir
import peak_types


class MagmaInterfaceBackend(backend.Backend):
    def __init__(self, ir : peak_ir.Ir):
        super().__init__(ir)

    def generate(self):
        input_map = {k : v for k, v in self._ir.io.inputs.items() \
                     if not isinstance(v, peak_types.Configuration)}
        IO_GEN_INFO = ((input_map, magma.In),
                       (self._ir.io.outputs, magma.Out))
        def generate_magma_type(_type):
            uqt = peak_types.TypeHelper.get_unqualified_type(_type)
            if isinstance(uqt, peak_types.BitVector):
                return magma.Bits(uqt.width)
            if isinstance(uqt, peak_types.Enum):
                enum_len = len(uqt.enum_cls)
                width = math.ceil(math.log(enum_len, 2))
                return magma.Bits(width)
            # TODO(raj): Handle other types (e.g. Array, Encoded).
            raise Exception()
        name = "top"
        circuit_io = []
        for info in IO_GEN_INFO:
            type_map = info[0]
            MagmaIoType = info[1]
            for name, type_ in type_map.items():
                magma_type = generate_magma_type(type_)
                circuit_io.append(name)
                circuit_io.append(MagmaIoType(magma_type))
        return magma.DefineCircuit(name, *circuit_io)
