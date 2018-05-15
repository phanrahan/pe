import re
from bit_vector import BitVector
import pe_ir_nodes as nodes
import pe_ir_ops as ops
import pe_ir_types as types
import status


class FunctionalModelGeneratorStatus(status.Status):
    pass


class FunctionalModelGeneratorError(FunctionalModelGeneratorStatus):
    def __str__(self):
        raise NotImplementedError("Can not call __str__ on abstract class "
                                  "FunctionalModelGeneratorError")

    def ok(self):
        return False


class FunctionalModelGeneratorGenericError(FunctionalModelGeneratorError):
    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return str(obj)


class FunctionalModelGeneratorSuccess(FunctionalModelGeneratorStatus):
    def __str__(self):
        return "Functional model generations succeeded"

    def ok(self):
        return True


class FunctionalModelGenerator:
    imports = ['bit_vector']

    @staticmethod
    def get_fn_name(node):
        name = type(node).__name__
        # Got this logic from Stack Overflow answer 1175208.
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        return "generate_%s" % name

    def __init__(self, module_name, ctx, var_map, type_map):
        self.module_name = module_name
        self.ctx = ctx
        self.var_map = var_map
        self.type_map = type_map
        self.src = None

    def add_line(self, line=None, indent=0):
        if line is None:
            self.src += "\n"
            return
        self.src += (indent * '    ') + line + "\n"

    def generate_type_init(_type):
        if _type.is_quantitative():
            return "bit_vector.BitVector(num_bits=%d)" % (_type.get_width())
        if _type.is_nominal():
            # TODO(raj): Fix nominal type init.
            return "<some nominal thing>"
        if isinstance(_type, types.QuantitativeRegisterFileType):
            return ("[bit_vector.BitVector(num_bits=%d) for _ in range(%d)]" %
                    (_type.get_width(), _type.get_height()))
        raise TypeError("Unsupported type: %s" % str(_type))

    def generate_name(node):
        return node.get_id()

    def generate_slice(args):
        def generate_index_code(index):
            if isinstance(index, int):
                return str(index)
            ret = FunctionalModelGenerator.generate_atom(index)
            return "(%s).as_int()" % ret
        (lhs, index) = args[0:2]
        lhs_code = FunctionalModelGenerator.generate_atom(lhs)
        index_code = generate_index_code(index)
        return "(%s)[%s]" % (lhs_code, index_code)

    def generate_add(args):
        arg_code = [FunctionalModelGenerator.generate_atom(arg) for arg in args]
        return "(%s) + (%s)" % (arg_code[0], arg_code[1])

    def generate_sub(args):
        arg_code = [FunctionalModelGenerator.generate_atom(arg) for arg in args]
        return "(%s) - (%s)" % (arg_code[0], arg_code[1])

    def generate_ternary(args):
        arg_code = [FunctionalModelGenerator.generate_atom(arg) for arg in args]
        return "(%s) if (%s) else (%s)" % (arg_code[1], arg_code[0], arg_code[2])

    def generate_op(op, args):
        fn_name = FunctionalModelGenerator.get_fn_name(op)
        fn = getattr(FunctionalModelGenerator, fn_name)
        return fn(args)

    def generate_expression(node):
        op = node.get_op()
        args = node.get_arguments()
        return FunctionalModelGenerator.generate_op(op, args)

    def generate_variable_declaration(self, node, depth):
        var_id = node.get_id()
        _type = self.var_map[var_id]
        if not isinstance(_type, types.IntermediateType):
            return FunctionalModelGeneratorSuccess()
        rhs = FunctionalModelGenerator.generate_type_init(_type)
        line = "%s = %s" % (var_id, rhs)
        self.add_line(line, depth)
        return FunctionalModelGeneratorSuccess()

    def generate_assignment(self, node, depth):
        def get_lhs_string(lhs):
            if isinstance(lhs, nodes.Name):
                return self.generate_name(lhs, depth)
        def get_rhs_string(rhs):
            if isinstance(rhs, nodes.Expression):
                return self.generate_expression(rhs, depth)
        lhs_str = FunctionalModelGenerator.generate_atom(node.get_lhs())
        rhs_str = FunctionalModelGenerator.generate_atom(node.get_rhs())
        self.add_line("%s = %s" % (lhs_str, rhs_str), depth)
        return FunctionalModelGeneratorSuccess()

    def generate_switch_case(self, node, depth):
        first = True
        subject_code = FunctionalModelGenerator.generate_atom(
            node.get_subject())
        for case, body in node.get_case_map().items():
            tpl = "%s (%s) == (%s):"
            if_kw = "if" if first else "elif"
            case_code = FunctionalModelGenerator.generate_atom(case)
            line = tpl % (if_kw, subject_code, case_code)
            self.add_line(line, depth)
            self.generate_body(body, depth + 1)
            first = False
        return FunctionalModelGeneratorSuccess()

    def generate_literal(node):
        def generate_bit_vector_code(bv):
            tpl = "bit_vector.BitVector(value=%d, num_bits=%d, signed=%s)"
            # TODO(raj): Make this more robust. Also, we shouldn't use the
            # _value field directly.
            return tpl % (bv._value, bv.num_bits, str(bv.signed))
        _type = node.get_type()
        value = node.get_value()
        if _type.is_quantitative():
            return generate_bit_vector_code(value)
        if _type.is_nominal():
            return "'%s'" % value
        # TODO(raj): Fix exception type.
        raise TypeError("Unsupported literal type: %s" % str(_type))

    def generate_atom(node):
        if isinstance(node, nodes.Name):
            return FunctionalModelGenerator.generate_name(node)
        if isinstance(node, nodes.Expression):
            return FunctionalModelGenerator.generate_expression(node)
        if isinstance(node, nodes.Literal):
            return FunctionalModelGenerator.generate_literal(node)
        # TODO(raj): Finish rest of cases.
        # TODO(raj): Fix exception type.
        raise TypeError("node wrong type for generate atom: %s" % str(node))

    def generate_statement(self, node, depth):
        if isinstance(node, nodes.VariableDeclaration):
            return self.generate_variable_declaration(node, depth)
        if isinstance(node, nodes.Assignment):
            return self.generate_assignment(node, depth)
        if isinstance(node, nodes.SwitchCase):
            return self.generate_switch_case(node, depth)
        # TODO(raj): Fix error code.
        return FunctionalModelGeneratorGenericError(
            "%s is not a statement type" % str(node))

    def generate_body(self, body, depth):
        if len(body) == 0:
            self.add_line("pass", depth)
            return FunctionalModelGeneratorSuccess()
        for node in body:
            node_status = self.generate_statement(node, depth)
            if not node_status.ok():
                return node_status
        return FunctionalModelGeneratorSuccess()

    def generate(self):
        self.src = ""
        # Collect all dynamic and configuration inputs.
        dynamic_inputs = []
        configuration_inputs = []
        stateful_variables = []
        for var_id, _type in self.var_map.items():
            if isinstance(_type, types.InputType):
                if _type.is_dynamic():
                    dynamic_inputs.append(var_id)
                else:
                    configuration_inputs.append(var_id)
            if _type.is_stateful():
                stateful_variables.append(var_id)
        for imp in FunctionalModelGenerator.imports:
            self.add_line('import %s' % imp)
        if len(FunctionalModelGenerator.imports) > 0:
            self.add_line()
        self.add_line("class %s:" % self.module_name)
        self.add_line("def __init__(self, %s):" %
                      ", ".join(configuration_inputs), 1)
        if len(configuration_inputs) == 0:
            self.add_line("pass", 2)
        for ci in configuration_inputs:
            self.add_line("self.%s = %s" % (ci, ci), 2)
        for sv in stateful_variables:
            _type = self.var_map[sv]
            type_str = FunctionalModelGenerator.generate_type_init(_type)
            self.add_line("self.%s = %s" % (sv, type_str), 2)
        self.add_line()
        self.add_line("def __call__(self, %s):" % ", ".join(dynamic_inputs), 1)
        # NOTE(raj): To avoid having "self.*" on all stateful variables
        # downstream, we make pointers to all of them here. Note that this is ok
        # since all variables live in the same namespace, and duplicate names
        # are not allowed. This is somewhat hacky, but should be pretty robust.
        for sv in stateful_variables:
            self.add_line("%s = self.%s" % (sv, sv), 2)
        body = self.ctx.get_nodes()
        return self.generate_body(body, 2)

    def get_src(self):
        return self.src
