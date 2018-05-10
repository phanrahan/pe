import passes
from pe_ir_nodes import *
from pe_ir_ops import *
from pe_ir_types import *
import math

def ConstructCpuIr():
    ctx = IrContext()

    instruction_choices = set(['add', 'sub', 'abs', 'ld'])
    instruction_type = NominalType(instruction_choices)

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
                NominalType(instruction_choices),
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
        ('r_b', 'src1')]

    for name, index in intermediates:
        ctx.add_node(
            VariableDeclaration(
                name,
                IntermediateType(
                    QuantitativeType(REG_WIDTH),
                    False)))
        ctx.add_node(
            Assignment(
                Name(name),
                Operation(
                    Slice(),
                    [Name('R'), Name(index)])))
    ctx.add_node(
        VariableDeclaration(
            'reg_wb',
            IntermediateType(
                QuantitativeType(REG_WIDTH),
                False)))
    ctx.add_node(
        Assignment(
            Name('reg_wb'),
            Literal(QuantitativeType(REG_WIDTH), 0)))

    add_body = [
        Assignment(
            Name('reg_wb'),
            Operation(
                Add(),
                [Name('r_a'), Name('r_a')]))
    ]
    sub_body = [
        Assignment(
            Name('reg_wb'),
            Operation(
                Sub(),
                [Name('r_a'), Name('r_a')]))
    ]
    abs_body = [
        Assignment(
            Name('reg_wb'),
            Ternary(
                Operation(
                    Slice(),
                    [Name('r_a'), 15]),
                Operation(
                    Sub(),
                    [Literal(QuantitativeType(REG_WIDTH), 0), Name('r_a')]),
                Name('r_a')))
    ]
    mov_body = [
        Assignment(
            Name('reg_wb'),
            Operation(
                Slice(),
                [Name('M'), Name('r_a')]))
    ]

    instruction_case_map = {
        Literal(instruction_type, 'add'): add_body,
        Literal(instruction_type, 'sub'): sub_body,
        Literal(instruction_type, 'abs'): abs_body,
        Literal(instruction_type, 'mov'): mov_body,
    }

    ctx.add_node(
        SwitchCase(
            Name('instruction'),
            instruction_case_map))

    return ctx
