import collections
import random
import bit_vector
import dsl_compiler
import dsl_functional_model_backend
import dsl_type_check_pass


def my_pe():
    class FlagSel(Enum):
        Z = auto()
        NOT_Z = auto()
        C = auto()
        NOT_C = auto()
        N = auto()
        NOT_N = auto()
        V = auto()
        NOT_V = auto()
        C_AND_NOT_Z = auto()
        NOT_C_OR_Z = auto()
        N_EQUAL_V = auto()
        N_NOT_EQUAL_V = auto()
        NOT_Z_AND_N_EQUAL_V = auto()
        Z_OR_N_NOT_EQUAL_V = auto()
        LUT_CODE = auto()
        COMP_RES_P = auto()

    class RegMode(Enum):
        CONST = auto()
        VALID = auto()
        BYPASS = auto()
        DELAY = auto()

    class Op(Enum):
        ADD = auto()
        SUB = auto()

    # Decalre all configuration state here.
    lut_code = Input(Configuration(BitVector(8)))
    data0_const = Input(Configuration(BitVector(16)))
    data1_const = Input(Configuration(BitVector(16)))
    bit0_const = Input(Configuration(BitVector(1)))
    bit1_const = Input(Configuration(BitVector(1)))
    bit2_const = Input(Configuration(BitVector(1)))
    debug_trig = Input(Configuration(BitVector(16)))
    debug_trig_p = Input(Configuration(BitVector(1)))

    op_code = Input(Configuration(Encoded(
        RegMode, bit2_mode,
        RegMode, bit1_mode,
        RegMode, bit0_mode,
        RegMode, data1_mode,
        RegMode, data0_mode,
        FlagSel, flag_sel,
        BitVector(1), irq_enable_1,
        BitVector(1), irq_enable_0,
        BitVector(1), acc_en,
        BitVector(1), signed,
        Op, operation,
    )))

    # Dynamic inputs.
    data0 = Input(BitVector(16))
    data1 = Input(BitVector(16))
    bit0 = Input(BitVector(1))
    bit1 = Input(BitVector(1))
    bit2 = Input(BitVector(1))

    # Data registers.
    data0_reg = Intermediate(Register(BitVector(16)))
    data1_reg = Intermediate(Register(BitVector(16)))
    bit0_reg = Intermediate(Register(BitVector(1)))
    bit1_reg = Intermediate(Register(BitVector(1)))
    bit2_reg = Intermediate(Register(BitVector(1)))

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

    # Operation logic.
    if op_code.operation == Op.ADD:
        res.assign(data0 + data1)
    elif op_code.operation == Op.SUB:
        res.assign(data0 - data1)

    # Flag selection logic.
    if op_code.flag_sel == FlagSel.Z:
        res_p.assign(z)
    elif op_code.flag_sel == FlagSel.NOT_Z:
        res_p.assign(~z)
    elif op_code.flag_sel == FlagSel.C:
        res_p.assign(c)
    elif op_code.flag_sel == FlagSel.NOT_C:
        res_p.assign(~c)
    elif op_code.flag_sel == FlagSel.N:
        res_p.assign(n)
    elif op_code.flag_sel == FlagSel.NOT_N:
        res_p.assign(~n)
    elif op_code.flag_sel == FlagSel.V:
        res_p.assign(v)
    elif op_code.flag_sel == FlagSel.NOT_V:
        res_p.assign(~v)
    elif op_code.flag_sel == FlagSel.C_AND_NOT_Z:
        res_p.assign(c & ~z)
    elif op_code.flag_sel == FlagSel.NOT_C_OR_Z:
        res_p.assign(~c | z)
    elif op_code.flag_sel == FlagSel.N_EQUAL_V:
        res_p.assign(n == v)
    elif op_code.flag_sel == FlagSel.N_NOT_EQUAL_V:
        res_p.assign(n != v)
    elif op_code.flag_sel == FlagSel.NOT_Z_AND_N_EQUAL_V:
        res_p.assign(~z & (n == v))
    elif op_code.flag_sel == FlagSel.Z_OR_N_NOT_EQUAL_V:
        res_p.assign(z | (n != v))
    elif op_code.flag_sel == FlagSel.LUT_CODE:
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
        "op_code" : to_namedtuple({
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
            "operation" : cls.Op.ADD,
        }),
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
