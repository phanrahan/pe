from pe_ir_nodes import *
from pe_ir_types import *
import math
import pe_ir_builder

ctx = AstContext()

ctx.add_node(
    VariableDeclaration(
        Variable(
            'perf_counter',
            InputType(
                None,
                QuantitativeType(None, 16),
                InputType.DynamicQualifier.CONFIGURATION))))

ctx.add_node(
    VariableDeclaration(
        Variable(
            'instruction',
            InputType(
                None,
                NominalType(None, set()),
                InputType.DynamicQualifier.DYNAMIC))))

NUM_REGISTERS = 32
REG_WIDTH = 16
reg_bits = math.log(NUM_REGISTERS, 2)
ctx.add_node(
    VariableDeclaration(
        Variable(
            'r',
            QuantitativeRegisterFileType(None, REG_WIDTH, NUM_REGISTERS))))

MEMORY_SIZE = 1 << REG_WIDTH
MEMORY_WORD = 16
ctx.add_node(
    VariableDeclaration(
        Variable(
            'M',
            QuantitativeRegisterFileType(None, MEMORY_WORD, MEMORY_SIZE, is_memory=True))))

instr_fields = [
    ('src0', reg_bits),
    ('src1', reg_bits),
    ('dst', reg_bits),
    ('imm', 10)]
for name, width in instr_fields:
    ctx.add_node(
        VariableDeclaration(
            Variable(
                name,
                InputType(
                    None,
                    QuantitativeType(None, width),
                    InputType.DynamicQualifier.DYNAMIC))))

for name in ['r_a', 'r_b', 'r_dst']:
    ctx.add_node(
        VariableDeclaration(
            Variable(
                name,
                IntermediateType(
                    None,
                    QuantitativeType(None, REG_WIDTH),
                    False))))

print (ctx.nodes)
