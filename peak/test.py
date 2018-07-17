import collections
import random
import bit_vector
import compiler
import functional_model_backend
import type_check_pass


def my_pe():
    class Op(Enum):
        ADD = 0
        SUB = 1

    in0 = Input(BitVector(8))
    in1 = Input(BitVector(8))
    op = Input(Op)
    prev = Intermediate(Register(BitVector(8)))
    prev_out = Output(BitVector(8))
    out = Output(BitVector(8))
    if op == Op.ADD:
        out.assign(in0 + in1)
    else:
        out.assign(in0 - in1)
    prev.assign(out)
    prev_out.assign(prev)


def to_namedtuple(d):
    return collections.namedtuple('NT', d.keys())(**d)


def random_bv(width):
    value = random.randint(0, 1 << width - 1)
    return bit_vector.BitVector(value=value, num_bits=width)


if __name__ == '__main__':
    compiler = compiler.Compiler()
    ir = compiler.compile(my_pe)

    try:
        pass_ = type_check_pass.TypeCheckPass(ir)
        pass_.run()
    except type_check_pass.TypeCheckError as e:
        raise e.get_exception() from None

    backend = functional_model_backend.FunctionalModelBackend(ir, add_type_checks=True)
    cls = backend.generate()
    inst = cls()
    print (inst(in0=random_bv(8), in1=random_bv(8), op=cls.Op.ADD))
