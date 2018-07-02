import collections
import random
import bit_vector
import dsl_compiler
import dsl_functional_model_backend
import dsl_type_check_pass


def my_pe():
    class FlagSel(Enum):
        Z = 0
        NOT_Z = 1
        C = 2
        NOT_C = 3
        N = 4
        NOT_N = 5
        V = 6
        NOT_V = 7
        C_AND_NOT_Z = 8
        NOT_C_OR_Z = 9
        N_EQUAL_V = 10
        N_NOT_EQUAL_V = 11
        NOT_Z_AND_N_EQUAL_V = 12
        Z_OR_N_NOT_EQUAL_V = 13
        LUT_CODE = 14
        COMP_RES_P = 15

    class RegMode(Enum):
        CONST = 0
        VALID = 1
        BYPASS = 2
        DELAY = 3

    class Op(Enum):
        ADD = 0
        SUB = 1

    # Decalre all configuration state here.
    lut_code = Input(Configuration(BitVector(8)))
    data0_const = Input(Configuration(BitVector(16)))
    data1_const = Input(Configuration(BitVector(16)))
    bit0_const = Input(Configuration(BitVector(1)))
    bit1_const = Input(Configuration(BitVector(1)))
    bit2_const = Input(Configuration(BitVector(1)))
    debug_trig = Input(Configuration(BitVector(16)))
    debug_trig_p = Input(Configuration(BitVector(1)))

    data0_mode = Input(Configuration(RegMode))
    data1_mode = Input(Configuration(RegMode))
    bit0_mode = Input(Configuration(RegMode))
    bit1_mode = Input(Configuration(RegMode))
    bit2_mode = Input(Configuration(RegMode))

    flag_sel = Input(Configuration(FlagSel))

    irq_enable_0 = Input(Configuration(BitVector(1)))
    irq_enable_1 = Input(Configuration(BitVector(1)))
    acc_en = Input(Configuration(BitVector(1)))
    signed = Input(Configuration(BitVector(1)))

    instruction = Input(Configuration(Op))

    data0 = Input(BitVector(16))
    data1 = Input(BitVector(16))
    bit0 = Input(BitVector(1))
    bit1 = Input(BitVector(1))
    bit2 = Input(BitVector(1))

    # Two outputs: result and predicate.
    res = Output(BitVector(16))
    res_p = Output(BitVector(1))

    lut_index = Intermediate(BitVector(3))

    c = Intermediate(BitVector(1))
    v_s = Intermediate(BitVector(1))
    v_u = Intermediate(BitVector(1))
    v = Intermediate(BitVector(1))
    z = Intermediate(BitVector(1))
    n = Intermediate(BitVector(1))

    lut_index.assign(concat(bit2, concat(bit1, bit0)))

    # Instruction logic.
    if instruction == Op.ADD:
        res.assign(data0 + data1)
    elif instruction == Op.SUB:
        res.assign(data0 - data1)

    # Flag selection logic.
    if flag_sel == FlagSel.Z:
        res_p.assign(z)
    elif flag_sel == FlagSel.NOT_Z:
        res_p.assign(~z)
    elif flag_sel == FlagSel.C:
        res_p.assign(c)
    elif flag_sel == FlagSel.NOT_C:
        res_p.assign(~c)
    elif flag_sel == FlagSel.N:
        res_p.assign(n)
    elif flag_sel == FlagSel.NOT_N:
        res_p.assign(~n)
    elif flag_sel == FlagSel.V:
        res_p.assign(v)
    elif flag_sel == FlagSel.NOT_V:
        res_p.assign(~v)
    elif flag_sel == FlagSel.C_AND_NOT_Z:
        res_p.assign(c & ~z)
    elif flag_sel == FlagSel.NOT_C_OR_Z:
        res_p.assign(~c | z)
    elif flag_sel == FlagSel.N_EQUAL_V:
        res_p.assign(n == v)
    elif flag_sel == FlagSel.N_NOT_EQUAL_V:
        res_p.assign(n != v)
    elif flag_sel == FlagSel.NOT_Z_AND_N_EQUAL_V:
        res_p.assign(~z & (n == v))
    elif flag_sel == FlagSel.Z_OR_N_NOT_EQUAL_V:
        res_p.assign(z | (n != v))
    elif flag_sel == FlagSel.LUT_CODE:
        res_p.assign((lut_code >> lut_index)[0])
    else:
        res_p.assign(bit0)


def to_namedtuple(d):
    return collections.namedtuple('NT', d.keys())(**d)


def random_bv(width):
    value = random.randint(0, 1 << width - 1)
    return bit_vector.BitVector(value=value, num_bits=width)


if __name__ == '__main__':
    compiler = dsl_compiler.DslCompiler()
    ir = compiler.compile(my_pe)

    try:
        pass_ = dsl_type_check_pass.DslTypeCheckPass(ir)
        pass_.run()
    except dsl_type_check_pass.DslTypeCheckError as e:
        raise e.get_exception() from None

    backend = dsl_functional_model_backend.DslFunctionalModelBackend(
        ir,
        add_type_checks=True,
        debug_src_file="debug.py",
        kwarg_check=True)
    cls = backend.generate()

    config = {
        "lut_code" : random_bv(8),
        "data0_const" : random_bv(16),
        "data1_const" : random_bv(16),
        "bit0_const" : random_bv(1),
        "bit1_const" : random_bv(1),
        "bit2_const" : random_bv(1),
        "debug_trig" : random_bv(16),
        "debug_trig_p" : random_bv(1),
        "data0_mode" : cls.RegMode.BYPASS,
        "data1_mode" : cls.RegMode.BYPASS,
        "bit0_mode" : cls.RegMode.BYPASS,
        "bit1_mode" : cls.RegMode.BYPASS,
        "bit2_mode" : cls.RegMode.BYPASS,
        "flag_sel" : cls.FlagSel.LUT_CODE,
        "irq_enable_0" : random_bv(1),
        "irq_enable_1" : random_bv(1),
        "acc_en" : random_bv(1),
        "signed" : random_bv(1),
        "instruction" : cls.Op.ADD,
    }
    inputs = {
        "data0" : random_bv(16),
        "data1" : random_bv(16),
        "bit0" : random_bv(1),
        "bit1" : random_bv(1),
        "bit2" : random_bv(1),
    }

    instance = cls(**config)
    print (config, inputs, instance(**inputs))
