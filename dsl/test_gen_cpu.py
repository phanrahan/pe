import sys
from bit_vector import BitVector
from examples import gen_cpu
import context_parser
import context_type_checker
import functional_model_generator
import status


def stderr(err):
    sys.stderr.write(err + "\n")


class Success(status.Status):
    def ok(self):
        return True

    def __str__(self):
        return "Succeeded"


def run_main():
    ctx = gen_cpu.construct_cpu_ir()

    parser = context_parser.ContextParser()
    res = parser.parse_context(ctx)
    if not res.ok():
        return res

    tc = context_type_checker.ContextTypeChecker()
    res = tc.type_check_context(ctx)
    if not res.ok():
        return res

    generator = functional_model_generator.FunctionalModelGenerator(
        'Cpu', ctx, tc.var_map, tc.type_map)
    res = generator.generate()
    if not res.ok():
        return res

    src = generator.get_src()
    with open("cpu_functional_model.py", 'w') as f:
        f.write(src)
    compiled = compile(src, '<string>', mode='exec')
    exec(compiled, globals())
    cpu = Cpu(BitVector(num_bits=16))

    # r0 <- r0 + 4749
    cpu(instruction='addi',
        src0=BitVector(value=0, num_bits=5),
        src1=BitVector(value=0, num_bits=5),
        dst=BitVector(value=0, num_bits=5),
        imm=BitVector(value=4749, num_bits=16))

    assert(cpu.r[0] == 4749)

    # r1 <- r1 + 806
    cpu(instruction='addi',
        src0=BitVector(value=1, num_bits=5),
        src1=BitVector(value=0, num_bits=5),
        dst=BitVector(value=1, num_bits=5),
        imm=BitVector(value=806, num_bits=16))

    assert(cpu.r[1] == 806)

    # r[2] <- r[1] + r[0]
    cpu(instruction='add',
        src0=BitVector(value=0, num_bits=5),
        src1=BitVector(value=1, num_bits=5),
        dst=BitVector(value=2, num_bits=5),
        imm=BitVector(value=0, num_bits=10))

    assert(cpu.r[2] == (4749 + 806))
    
    return Success()


if __name__ == '__main__':
    res = run_main()
    if not res.ok():
        stderr("Could not generate code. Error: %s" % str(res))
