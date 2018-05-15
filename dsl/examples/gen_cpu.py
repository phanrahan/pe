import math
from bit_vector import BitVector
import pe_ir_context as context
import pe_ir_nodes as nodes
import pe_ir_ops as ops
import pe_ir_types as types


def construct_cpu_ir():
    ctx = context.IrContext()

    instruction_choices = set(['add', 'sub', 'abs', 'mov', 'addi'])
    instruction_type = types.NominalType(instruction_choices)

    ctx.add_node(
        nodes.VariableDeclaration(
            'perf_counter',
            types.InputType(
                types.QuantitativeType(16),
                types.InputType.DynamicQualifier.CONFIGURATION)))

    ctx.add_node(
        nodes.VariableDeclaration(
            'instruction',
            types.InputType(
                types.NominalType(instruction_choices),
                types.InputType.DynamicQualifier.DYNAMIC)))

    NUM_REGISTERS = 32
    REG_WIDTH = 16
    reg_bits = math.ceil(math.log(NUM_REGISTERS, 2))
    ctx.add_node(
        nodes.VariableDeclaration(
            'r',
            types.QuantitativeRegisterFileType(REG_WIDTH, NUM_REGISTERS)))

    MEMORY_SIZE = 1 << REG_WIDTH
    MEMORY_WORD = 16
    ctx.add_node(
        nodes.VariableDeclaration(
            'M',
            types.QuantitativeRegisterFileType(MEMORY_WORD, MEMORY_SIZE, is_memory=True)))

    instr_fields = [
        ('src0', reg_bits),
        ('src1', reg_bits),
        ('dst', reg_bits),
        ('imm', 16)]
    for name, width in instr_fields:
        ctx.add_node(
            nodes.VariableDeclaration(
                name,
                types.InputType(
                    types.QuantitativeType(width),
                    types.InputType.DynamicQualifier.DYNAMIC)))

    intermediates = [
        ('r_a', 'src0'),
        ('r_b', 'src1')]

    for name, index in intermediates:
        ctx.add_node(
            nodes.VariableDeclaration(
                name,
                types.IntermediateType(
                    types.QuantitativeType(REG_WIDTH),
                    False)))
        ctx.add_node(
            nodes.Assignment(
                nodes.Name(name),
                nodes.Expression(
                    ops.Slice(),
                    [nodes.Name('r'), nodes.Name(index)])))
    ctx.add_node(
        nodes.VariableDeclaration(
            'reg_wb',
            types.IntermediateType(
                types.QuantitativeType(REG_WIDTH),
                False)))
    ctx.add_node(
        nodes.Assignment(
            nodes.Name('reg_wb'),
            nodes.Literal(types.QuantitativeType(REG_WIDTH), BitVector(0, REG_WIDTH))))

    add_body = [
        nodes.Assignment(
            nodes.Name('reg_wb'),
            nodes.Expression(
                ops.Add(),
                [nodes.Name('r_a'), nodes.Name('r_b')]))
    ]
    sub_body = [
        nodes.Assignment(
            nodes.Name('reg_wb'),
            nodes.Expression(
                ops.Sub(),
                [nodes.Name('r_a'), nodes.Name('r_b')]))
    ]
    abs_body = [
        nodes.Assignment(
            nodes.Name('reg_wb'),
            nodes.Expression(
                ops.Ternary(),
                [
                    nodes.Expression(
                        ops.Slice(),
                        [nodes.Name('r_a'), 15]),
                    nodes.Expression(
                        ops.Sub(),
                        [nodes.Literal(types.QuantitativeType(REG_WIDTH),
                                       BitVector(0, 16)),
                         nodes.Name('r_a')]),
                    nodes.Name('r_a')
                ]))
    ]
    mov_body = [
        nodes.Assignment(
            nodes.Name('reg_wb'),
            nodes.Expression(
                ops.Slice(),
                [nodes.Name('M'), nodes.Name('r_a')]))
    ]
    addi_body = [
        nodes.Assignment(
            nodes.Name('reg_wb'),
            nodes.Expression(
                ops.Add(),
                [nodes.Name('r_a'), nodes.Name('imm')]))
    ]

    instruction_case_map = {
        nodes.Literal(instruction_type, 'add'): add_body,
        nodes.Literal(instruction_type, 'sub'): sub_body,
        nodes.Literal(instruction_type, 'abs'): abs_body,
        nodes.Literal(instruction_type, 'mov'): mov_body,
        nodes.Literal(instruction_type, 'addi'): addi_body,
    }

    ctx.add_node(
        nodes.SwitchCase(
            nodes.Name('instruction'),
            instruction_case_map))

    ctx.add_node(
        nodes.Assignment(
            nodes.Expression(
                ops.Slice(),
                [nodes.Name('r'), nodes.Name('dst')]),
            nodes.Name('reg_wb')))

    return ctx
