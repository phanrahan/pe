import dsl_compiler


def my_pe():
    class Op(Enum):
        ADD = 0
        SUB = 1

    in0 = Input(BitVector(8))
    in1 = Input(Encoded(BitVector(8), val, Op, op))
    out = Output(BitVector(8))
    if in1.op == Op.ADD:
        out.assign(in0 + in1.val)
    else:
        out.assign(in0 - in1.val)


if __name__ == '__main__':
    compiler = dsl_compiler.DslCompiler()
    ir = compiler.compile(my_pe)

    print (ir.src_filename, ir.io, ir.intermediates, ir.module)
