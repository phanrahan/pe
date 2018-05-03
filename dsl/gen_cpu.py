from pe_ir_nodes import *
from pe_ir_ops import *
from pe_ir_types import *
import math

ctx = IrContext()

ctx.add_node(
    VariableDeclaration(
        'perf_counter',
        InputType(
            QuantitativeType(16),
            InputType.DynamicQualifier.CONFIGURATION)))

ctx.add_node(
    VariableDeclaration(
        'instruction',
        InputType(
            NominalType(set()),
            InputType.DynamicQualifier.DYNAMIC)))

NUM_REGISTERS = 32
REG_WIDTH = 16
reg_bits = math.log(NUM_REGISTERS, 2)
ctx.add_node(
    VariableDeclaration(
        'r',
        QuantitativeRegisterFileType(REG_WIDTH, NUM_REGISTERS)))

MEMORY_SIZE = 1 << REG_WIDTH
MEMORY_WORD = 16
ctx.add_node(
    VariableDeclaration(
        'M',
        QuantitativeRegisterFileType(MEMORY_WORD, MEMORY_SIZE, is_memory=True)))

instr_fields = [
    ('src0', reg_bits),
    ('src1', reg_bits),
    ('dst', reg_bits),
    ('imm', 10)]
for name, width in instr_fields:
    ctx.add_node(
        VariableDeclaration(
            name,
            InputType(
                QuantitativeType(width),
                InputType.DynamicQualifier.DYNAMIC)))

intermediates = [
    ('r_a', 'src0'),
    ('r_b', 'src1'),
    ('r_dst', 'dst')]

for name, index in intermediates:
    ctx.add_node(
        VariableDeclaration(
            name,
            IntermediateType(
                QuantitativeType(REG_WIDTH),
                False),
            Operation(
                Slice(),
                [Name('R'), Name(index)])))

print (ctx.nodes)
