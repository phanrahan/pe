from peak_ir import Ir
import peak_types
from decode_specification import DecodeSpecification, EnumEncoding


def verify_user_defined_type(type_, enum_encoding):
    member_names = set(type_._member_names_)
    if member_names != set(enum_encoding.mapping.keys()):
        raise Exception()
    values = set()
    for k, v in enum_encoding.mapping.items():
        if v < 0:
            raise Exception()
        if v in values:
            raise Exception()
        values.add(v)
    if max(values) >= 2 ** enum_encoding.bit_width:
        raise Exception()
    return True


def required_bit_width(type_, enums):
    if isinstance(type_, peak_types.BitVector):
        return type_.width
    if isinstance(type_, peak_types.Enum):
        enum_name = type_.enum_cls.__name__
        return enums[enum_name].bit_width
    raise Exception()


def verify_encoded_type(type_, encoded, enums):
    def range_is_valid(range_):
        return range_.start >= 0 and range_.stop >= range_.start
    bit_assignments, bit_width = encoded
    for field, field_type in type_.encoding.items():
        if field not in bit_assignments:
            raise Exception()
        range_ = bit_assignments[field]
        if not range_is_valid(range_):
            raise Exception()
        num_bits = range_.stop - range_.start + 1
        required_bits = required_bit_width(field_type, enums)
        if num_bits < required_bits:
            raise Exception()
    return True


def verify_decode_specification(decode : DecodeSpecification, ir : Ir):
    # Verify enums.
    for name, type_ in ir.user_defined_types.types.items():
        if name not in decode.enums:
            raise Exception()
        if not verify_user_defined_type(type_, decode.enums[name]):
            raise Exception()
    # Verify encoded types.
    inputs = ir.io.inputs
    outputs = ir.io.outputs
    intermediates = ir.intermediates.intermediates
    encoded_types = {}
    for var_map in (inputs, outputs, outputs, intermediates):
        for k, v in var_map.items():
            uqt = peak_types.TypeHelper.get_unqualified_type(v)
            if isinstance(uqt, peak_types.Encoded):
                encoded_types[k] = uqt
    for name, type_ in encoded_types.items():
        if name not in decode.encoded:
            raise Exception()
        if not verify_encoded_type(type_, decode.encoded[name], decode.enums):
            raise Exception()

    return True
