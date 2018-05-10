import math
from pe_lib import *

################################################################################
# BEGIN PE Code
################################################################################
NUM_REGISTERS = 32
REG_WIDTH = 16

MEMORY_SIZE = 1 << REG_WIDTH
MEMORY_WORD = 16

IMMEDIATE_WIDTH = 10

perf_counter = Input('configuration', 'quantitative', width=16)
instruction = Input('dynamic', 'nominal',
                    value_set=set(['add', 'sub', 'abs', 'mov']))

r = RegisterFile(REG_WIDTH, NUM_REGISTERS)
M = Memory(MEMORY_WORD, MEMORY_SIZE)

reg_bits = math.ceil(math.log(NUM_REGISTERS, 2))

src0 = Input('dynamic', 'quantitative', width=reg_bits)
src1 = Input('dynamic', 'quantitative', width=reg_bits)
dst = Input('dynamic', 'quantitative', width=reg_bits)
imm = Input('dynamic', 'quantitative', width=IMMEDIATE_WIDTH)

r_a = r[src0]
r_b = r[src1]

if instruction == 'add':
    r[dst] = r_a + r_b
elif instruction == 'sub':
    r[dst] = r_a + ~r_b + 1
elif instruction == 'abs':
    r[dst] = (0 - r_a) if r_a[15] else r_a
elif instruction == 'mov':
    r[dst] = M[r_a]
# ... specify rest of ops here.
################################################################################
# END PE Code
################################################################################
