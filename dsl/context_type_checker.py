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


class GenericAssignmentError(TypeCheckError):
    def __init__(self, ltype=None, rtype=None):
        self.ltype = ltype
        self.rtype = rtype

    def __str__(self):
        ltype_name = type(self.ltype).__name__
        rtype_name = type(self.rtype).__name__
        return ("Can not assign type %s to type %s." % (ltype_name, rtype_name))


class AssignmentLTypeError(GenericAssignmentError):
    def __str__(self):
        return ("Can not assign to type %s." % self.ltype.__name__)


class AssignmentValueSetError(GenericAssignmentError):
    def __str__(self):
        vs0 = self.ltype.get_value_set()
        vs1 = self.rtype.get_value_set()
        return ("Can not assign types with value sets %s and %s." %
                (str(vs0), str(vs1)))


class AssignmentWidthError(GenericAssignmentError):
    def __str__(self):
        w0 = self.ltype.get_width()
        w1 = self.rtype.get_width()
        return ("Can not assign types with widths %s and %s." %
                (w0, w1))


class GenericLiteralError(TypeCheckError):
    def __init__(self, _type, value):
        self._type = _type
        self.value = value

    def __str__(self):
        return ("Literal value %s is not compatible with type %s" %
                (str(self.value), type(self._type).__name__))


class ArgumentMismatchError(TypeCheckError):
    def __init__(self, expected, got):
        self.expected = expected
        self.got = got

    def __str__(self):
        return "Expected %d arguments; got %d" % (expected, got)


class GenericBinaryOpError(TypeCheckError):
    def __init__(self, op, arg0, arg1):
        self.op = op
        self.arg0 = arg0
        self.arg1 = arg1

    def __str__(self):
        op_name = type(self.op).__name__
        arg0_type = type(self.arg0).__name__
        arg1_type = type(self.arg1).__name__
        return ("Can not apply op %s to types %s and %s" %
                (op_name, arg0_type, arg1_type))

class GenericTernaryOpError(TypeCheckError):
    def __init__(self, conditional, true_case, false_case):
        self.conditional = conditional
        self.true_case = true_case
        self.false_case = false_case

    def __str__(self):
        tpl = ("Can not perform ternary with conditional type %s, true case "
               "type %s, and false case type %s.")
        fmt = (type(self.conditional).__name__,
               type(self.true_case).__name__,
               type(self.false_case).__name__)
        return tpl % fmt


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
            return AssignmentLTypeError(ltype)
        if ltype.is_nominal() and rtype.is_nominal():
            if ltype.get_value_set() == rtype.get_value_set():
                return TypeCheckSuccess()
            return AssignmentValueSetError(ltype, rtype)
        if ltype.is_quantitative() and rtype.is_quantitative():
            if ltype.get_width() == rtype.get_width():
                return TypeCheckSuccess()
            return AssignmentWidthError(ltype, rtype)
        return GenericAssignmentError(ltype, rtype)

    @staticmethod
    def literal_is_compatible(_type, value):
        if _type.is_quantitative():
            if not isinstance(value, BitVector):
                return GenericLiteralError(_type, value)
            if _type.get_width() != len(value):
                return GenericLiteralError(_type, value)
            return TypeCheckSuccess()
        if _type.is_nominal():
            if value in _type.get_value_set():
                return TypeCheckSuccess()
            return GenericLiteralError(_type, value)
        return GenericLiteralError(_type, value)

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
            return ArgumentMismatchError(2, len(args))
        arg0 = args[0]
        arg1 = args[1]
        arg0_res = self.type_check_node(arg0)
        if not arg0_res.ok():
            return arg0_res
        arg0_type = self.get_type(arg0)
        if arg0_type.is_nominal():
            return GenericBinaryOpError(op, arg0, arg1)
        if arg0_type.is_quantitative():
            if not isinstance(arg1, int):
                return GenericBinaryOpError(op, arg0, arg1)
            if arg1 not in range(0, arg0_type.get_width()):
                return GenericBinaryOpError(op, arg0, arg1)
            # Result of slice on a QuantitativeType is a single-bit bit-vector.
            self.type_map[op] = types.QuantitativeType(1)
            return TypeCheckSuccess()
        if isinstance(arg0_type, types.QuantitativeRegisterFileType):
            if isinstance(arg1, int):
                if arg1 in range(0, arg0_type.get_height()):
                    self.type_map[op] = arg0_type.generate_underlying_type()
                    return TypeCheckSuccess()
                return GenericBinaryOpError(op, arg0, arg1)
            arg1_res = self.type_check_node(arg1)
            if not arg1_res.ok():
                return arg1_res
            arg1_type = self.get_type(arg1)
            if not arg1_type.is_quantitative():
                return GenericBinaryOpError(op, arg0, arg1)
            if arg1_type.max_value() != arg0_type.get_height():
                return GenericBinaryOpError(op, arg0, arg1)
            self.type_map[op] = arg0_type.generate_underlying_type()
            return TypeCheckSuccess()
        return GenericBinaryOpError(op, arg0, arg1)

    def type_check_binary_arithmetic(self, op, args):
        if len(args) != 2:
            return ArgumentMismatchError(2, len(args))
        for arg in args:
            res = self.type_check_node(arg)
            if not res.ok():
                return res
        types = [self.get_type(arg) for arg in args]
        info = [t.is_quantitative() for t in types]
        if not all(info):
            return GenericBinaryOpError(op, args[0], args[1])
        info = [t.get_width() == types[0].get_width() for t in types]
        if not all(info):
            return GenericBinaryOpError(op, args[1], args[1])
        self.type_map[op] = types[0]
        return TypeCheckSuccess()

    def type_check_add(self, op, args):
        return self.type_check_binary_arithmetic(op, args)

    def type_check_sub(self, op, args):
        return self.type_check_binary_arithmetic(op, args)

    def type_check_ternary(self, op, args):
        if len(args) != 3:
            return ArgumentMismatchError(3, len(args))
        for arg in args:
            res = self.type_check_node(arg)
            if not res.ok():
                return res
        types = [self.get_type(arg) for arg in args]
        if not types[0].is_quantitative():
            return GenericTernaryOpError(args[0], args[1], args[2])
        if types[0].get_width() != 1:
            return GenericTernaryOpError(args[0], args[1], args[2])
        # Check that types of true and false case of ternary "match".
        # NOTE(raj): We are using can_assign() as a proxy for this check.
        # Somewhat hacky.
        can_assign_res = ContextTypeChecker.can_assign(types[1], types[2])
        if not can_assign_res.ok():
            return can_assign_res
        self.type_map[op] = types[1]
        return TypeCheckSuccess()

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
