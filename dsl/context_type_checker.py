import re
from bit_vector import BitVector
import pe_ir_nodes as nodes
import pe_ir_ops as ops
import pe_ir_types as types
import status

class TypeCheckStatus(status.Status):
    pass


class TypeCheckSuccess(TypeCheckStatus):
    def __str__(self):
        return "Type checking succeeded"

    def ok(self):
        return True


class TypeCheckError(TypeCheckStatus):
    def __str__(self):
        raise NotImplementedError("Can not call __str__ on abstract "
                                  "class TypeCheckError")

    def ok(self):
        return False


class NameNotDeclared(TypeCheckError):
    def __init__(self, var_id):
        self.var_id = var_id

    def __str__(self):
        return ("Name %s used before declaration." % self.var_id)


class NameAlreadyDeclared(TypeCheckError):
    def __init__(self, var_id):
        self.var_id = var_id

    def __str__(self):
        return ("Name %s already declared." % self.var_id)


class GenericTcError(TypeCheckError):
    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return str(self.obj)


class ContextTypeChecker:
    @staticmethod
    def get_fn_name(node):
        name = type(node).__name__
        # Got this logic from Stack Overflow answer 1175208.
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        return "type_check_%s" % name

    @staticmethod
    def can_assign(ltype, rtype):
        if isinstance(ltype, types.InputType):
            return GenericTcError('Can not assign to InputType')
        if ltype.is_nominal() and rtype.is_nominal():
            if ltype.get_value_set() == rtype.get_value_set():
                return TypeCheckSuccess()
            return GenericTcError('Value set mismatch in nominal type assignment')
        if ltype.is_quantitative() and rtype.is_quantitative():
            if ltype.get_width() == rtype.get_width():
                return TypeCheckSuccess()
            return GenericTcError('Width mismatch in quantitative type assignment')
        return GenericTcError(('Assignment not supported for types', ltype, rtype))

    @staticmethod
    def literal_is_compatible(_type, value):
        if _type.is_quantitative():
            if not isinstance(value, BitVector):
                return GenericTcError('Literal value for quantitative type must be BitVector')
            if _type.get_width() != len(value):
                return GenericTcError('Width mistmatch for quantitative literal type')
            return TypeCheckSuccess()
        if _type.is_nominal():
            if value in _type.get_value_set():
                return TypeCheckSuccess()
            return GenericTcError('Value must be in value set for nominal type')
        return GenericTcError(('Literal not allowed for type', _type, value))

    def type_check_literal(self, node):
        res = ContextTypeChecker.literal_is_compatible(
            node.get_type(), node.get_value())
        if not res.ok():
            return res
        self.type_map[node] = node.get_type()
        return TypeCheckSuccess()

    def type_check_variable_declaration(self, node):
        var_id = node.get_id()
        if var_id in self.var_map:
            return NameAlreadyDeclared(var_id)
        self.var_map[var_id] = node.get_type()
        return TypeCheckSuccess()

    def type_check_name(self, node):
        if node.get_id() not in self.var_map:
            return NameNotDeclared(node.get_id())
        return TypeCheckSuccess()

    def type_check_assignment(self, node):        
        lhs_status = self.type_check_node(node.get_lhs())
        if not lhs_status.ok():
            return lhs_status
        rhs_status = self.type_check_node(node.get_rhs())
        if not rhs_status.ok():
            return rhs_status
        lhs_type = self.get_type(node.get_lhs())
        rhs_type = self.get_type(node.get_rhs())
        res = ContextTypeChecker.can_assign(lhs_type, rhs_type)
        if not res.ok():
            return res
        return TypeCheckSuccess()

    def type_check_slice(self, op, args):
        if len(args) != 2:
            return GenericTcError('Argument # mismatch')
        arg0 = args[0]
        arg1 = args[1]
        arg0_res = self.type_check_node(arg0)
        if not arg0_res.ok():
            return arg0_res
        arg0_type = self.get_type(arg0)
        if arg0_type.is_nominal():
            return GenericTcError('Can not slice nominal variable')
        if isinstance(arg0_type, types.QuantitativeRegisterFileType):
            if isinstance(arg1, int):
                if arg1 in range(0, arg0_type.get_height()):
                    self.type_map[op] = arg0_type.generate_underlying_type()
                    return TypeCheckSuccess()
                return GenericTcError('QRF index out of range')
            arg1_res = self.type_check_node(arg1)
            if not arg1_res.ok():
                return arg1_res
            arg1_type = self.get_type(arg1)
            if not arg1_type.is_quantitative():
                return GenericTcError('Slice index must be quantitative')
            if arg1_type.max_value() != arg0_type.get_height():
                return GenericTcError('Slice index width must be log_2 of height')
            self.type_map[op] = arg0_type.generate_underlying_type()
            return TypeCheckSuccess()
        # TODO(raj): Finish this (for quant type).
        return GenericTcError('not impl')

    def type_check_binary_arithmetic(self, op, args):
        if len(args) != 2:
            return GenericTcError('Argument # mismatch')
        for arg in args:
            res = self.type_check_node(arg)
            if not res.ok():
                return res
        types = [self.get_type(arg) for arg in args]
        info = [t.is_quantitative() for t in types]
        if not all(info):
            return GenericTcError('Arguments to binary arithmetic must be quantitative')
        info = [t.get_width() == types[0].get_width() for t in types]
        if not all(info):
            return GenericTcError('Arguments to binary arithmetic must all have the same width')
        self.type_map[op] = types[0]
        return TypeCheckSuccess()

    def type_check_add(self, op, args):
        return self.type_check_binary_arithmetic(op, args)

    def type_check_sub(self, op, args):
        return self.type_check_binary_arithmetic(op, args)

    def type_check_expression(self, node):
        status = self.type_check_op(node.get_op(), node.get_arguments())
        if not status.ok():
            return status
        self.type_map[node] = self.type_map[node.get_op()]
        return TypeCheckSuccess()

    def type_check_switch_case(self, node):
        subject = node.get_subject()
        subject_status = self.type_check_node(subject)
        if not subject_status.ok():
            return subject_status
        subject_type = self.get_type(subject)
        for case, body in node.get_case_map().items():
            case_status = self.type_check_node(case)
            if not case_status.ok():
                return case_status
            # Check that case matches type of subject.
            # NOTE(raj): We are using can_assign() as a proxy for this check.
            # Somewhat hacky.
            can_assign_res = ContextTypeChecker.can_assign(
                self.get_type(subject), self.get_type(case))
            body_status = self.type_check_body(body)
            if not body_status.ok():
                return body_status
        return TypeCheckSuccess()

    def type_check_node(self, node):
        fn_name = ContextTypeChecker.get_fn_name(node)
        fn = getattr(self, fn_name)
        return fn(node)

    def type_check_op(self, op, args):
        fn_name = ContextTypeChecker.get_fn_name(op)
        fn = getattr(self, fn_name)
        return fn(op, args)

    def type_check_body(self, body):
        for node in body:
            node_status = self.type_check_node(node)
            if not node_status.ok():
                return node_status
        return TypeCheckSuccess()

    def get_type(self, node):
        if isinstance(node, nodes.Name):
            return self.var_map[node.get_id()]
        return self.type_map[node]

    def __init__(self):
        # Maps from variable names to types.
        self.var_map = {}
        # Maps from ir nodes (addresses to types).
        self.type_map = {}

    def type_check_context(self, ctx):
        body = ctx.get_nodes()
        return self.type_check_body(body)
