import ast
import enum
import math
import peak_ir
import compiler_pass
import peak_types
import compiler_error


class DslTypeCheckError(compiler_error.DslCompilerError):
    @staticmethod
    def __get_msg(msg : str):
        return "TypeError: %s" % msg

    def __init__(self, msg : str, filename : str, node : ast.AST):
        msg = DslTypeCheckError.__get_msg(msg)
        super().__init__(msg, filename, node)


class AssignmentTypeError(DslTypeCheckError):
    @staticmethod
    def __get_msg(left, right):
        return "Can not assign type %s to type %s" % (left, right)

    def __init__(self, left, right, filename : str, node : ast.AST):
        msg = AssignmentTypeError.__get_msg(left, right)
        super().__init__(msg, filename, node)


class ImmutableAssignmentError(DslTypeCheckError):
    def __init__(self, filename : str, node : ast.AST):
        super().__init__("Can not assign immutable", filename, node)


class ComparisonTypeError(DslTypeCheckError):
    @staticmethod
    def __get_msg(left, right, op):
        return ("Comparison %s on %s and %s not supported" %
                (type(op).__name__, left, right))

    def __init__(self, left, right, op, filename : str, node : ast.AST):
        super().__init__(
            ComparisonTypeError.__get_msg(left, right, op), filename, node)


class TypeTable:
    class Entry:
        __slots__ = ["__type", "__mutable"]
        def __init__(self, type_, mutable):
            self.__type = type_
            self.__mutable = mutable

        @property
        def type(self):
            return self.__type

        @property
        def mutable(self):
            return self.__mutable

        def __repr__(self):
            return "{type: %s, mutable: %s}" % (self.__type, self.__mutable)

    def __init__(self):
        self.__table = {}

    def __getitem__(self, key : ast.AST):
        return self.__table[key]

    def __setitem__(self, key : ast.AST, value : Entry):
        self.__table[key] = value


class IntType:
    def __init__(self, value : int):
        self.__value = value

    @property
    def value(self):
        return self.__value


class DslTypeCheckPass(compiler_pass.DslPass):
    def __init__(self, ir : peak_ir.Ir):
        super().__init__(ir)

    def run(self):
        get_uqt = lambda t : peak_types.TypeHelper.get_unqualified_type(t)
        filename = self._ir.src_filename
        user_defined_types = self._ir.user_defined_types.types
        io = self._ir.io
        inputs = {k : get_uqt(v) for k, v in io.inputs.items()}
        outputs = {k : get_uqt(v) for k, v in io.outputs.items()}
        intermediates = {k : get_uqt(v) for k, v in
                         self._ir.intermediates.intermediates.items()}
        types = TypeTable()

        def can_compare(left, right, op):
            if isinstance(op, (ast.In, ast.NotIn, ast.Is, ast.IsNot)):
                return False
            if isinstance(left, peak_types.BitVector) and \
               isinstance(right, peak_types.BitVector) and \
               left.width == right.width:
                return True
            if isinstance(left, peak_types.Enum) and \
               isinstance(right, peak_types.Enum) and \
               left.enum_cls == right.enum_cls and \
               isinstance(op, (ast.Eq, ast.NotEq)):
                return True
            return False

        def can_assign(left, right):
            if isinstance(left, peak_types.BitVector) and \
               isinstance(right, peak_types.BitVector) and \
               left.width == right.width:
                return True
            if isinstance(left, peak_types.Enum) and \
               isinstance(right, peak_types.Enum) and \
               left.enum_cls == right.enum_cls:
                return True
            return False

        def get_bin_op_type(left, right, op):
            SIMPLE_OPS = (ast.Add, ast.Sub, ast.BitAnd, ast.BitOr)
            LOGICAL_SHIFTS = (ast.LShift, ast.RShift)
            if isinstance(left, peak_types.BitVector):
                if isinstance(op, SIMPLE_OPS) and \
                   isinstance(right, peak_types.BitVector) and \
                   left.width == right.width:
                    return left
                if isinstance(op, LOGICAL_SHIFTS) and \
                   isinstance(right, (IntType, peak_types.BitVector)):
                    return peak_types.BitVector(left.width)

        def get_unary_op_type(operand, op):
            if isinstance(operand, peak_types.BitVector):
                if isinstance(op, (ast.Invert)):
                    return operand

        def get_subscript_type(left, right):
            if isinstance(left, peak_types.Array):
                if isinstance(right, IntType) and \
                   right.value in range(0, left.size):
                    return left.type
            if isinstance(left, peak_types.BitVector):
                if isinstance(right, IntType) and \
                   right.value in range(0, left.width):
                    return peak_types.BitVector(1)
                if isinstance(right, peak_types.BitVector) and \
                   right.width == math.log(left.width, 2):
                    return peak_types.BitVector(1)
            return None

        def get_concat_type(left, right):
            if isinstance(left, peak_types.BitVector) and \
               isinstance(right, peak_types.BitVector):
                return peak_types.BitVector(left.width + right.width)
            return None

        class Visitor(ast.NodeVisitor):
            def __init__(self):
                pass

            def visit_Num(self, node):
                types[node] = TypeTable.Entry(IntType(node.n), False)

            def visit_BinOp(self, node):
                self.visit(node.left)
                self.visit(node.right)
                left = types[node.left].type
                right = types[node.right].type
                op = node.op
                ret = get_bin_op_type(left, right, op)
                if ret is None:
                    raise Exception()
                types[node] = TypeTable.Entry(ret, False)

            def visit_UnaryOp(self, node):
                self.visit(node.operand)
                op = node.op
                operand = types[node.operand].type
                ret = get_unary_op_type(operand, op)
                if ret is None:
                    raise Exception()
                types[node] = TypeTable.Entry(ret, False)

            def visit_Index(self, node):
                value = node.value
                self.visit(value)
                types[node] = TypeTable.Entry(types[value].type, False)

            def visit_Subscript(self, node):
                self.visit(node.value)
                self.visit(node.slice)
                left = types[node.value]
                right = types[node.slice]
                ret = get_subscript_type(left.type, right.type)
                if ret is None:
                    raise Exception()
                types[node] = TypeTable.Entry(ret, left.mutable)

            def visit_Compare(self, node):
                assert(len(node.ops) == 1)
                assert(len(node.comparators) == 1)
                op = node.ops[0]
                right = node.comparators[0]
                self.visit(node.left)
                self.visit(right)
                left_type = types[node.left].type
                right_type = types[right].type
                if can_compare(left_type, right_type, op):
                    types[node] = TypeTable.Entry(peak_types.BitVector(1), False)
                    return
                raise ComparisonTypeError(
                    left_type, right_type, op, filename, node)

            def visit_Call(self, node):
                func = node.func
                args = node.args
                kws = node.keywords
                for arg in args:
                    self.visit(arg)
                for kw in kws:
                    self.visit(kw)
                if isinstance(func, ast.Name):
                    id_ = func.id
                    if id_ == "concat":
                        if len(args) != 2 or len(kws) != 0:
                            raise Exception()
                        left = types[args[0]]
                        right = types[args[1]]
                        ret = get_concat_type(left.type, right.type)
                        if ret is None:
                            raise Exception()
                        types[node] = TypeTable.Entry(ret, False)

            def visit_Assign(self, node):
                assert(len(node.targets) == 1)
                target = node.targets[0]
                self.visit(target)
                self.visit(node.value)
                left_type = types[target]
                right_type = types[node.value]
                if not left_type.mutable:
                    raise ImmutableAssignmentError(filename, node)
                if can_assign(left_type.type, right_type.type):
                    types[node] = left_type
                    return
                raise AssignmentTypeError(
                    left_type.type, right_type.type, filename, node)

            def visit_Attribute(self, node):
                self.visit(node.value)
                value_type = types[node.value]
                attr = node.attr
                def get_info():
                    t = value_type.type
                    mutable = value_type.mutable
                    if isinstance(t, peak_types.Encoded):
                        return (t.encoding[attr], mutable)
                    if isinstance(t, enum.EnumMeta):
                        return (peak_types.Enum(t), False)
                ret = get_info()
                assert(ret is not None)
                (type_, mutable) = ret
                entry = TypeTable.Entry(type_, mutable)
                types[node] = entry

            def visit_Name(self, node):
                id_ = node.id
                def get_info():
                    if id_ in inputs:
                        return (inputs, False)
                    if id_ in user_defined_types:
                        return (user_defined_types, False)
                    if id_ in intermediates:
                        return (intermediates, True)
                    if id_ in outputs:
                        return (outputs, True)
                ret = get_info()
                assert(ret is not None)
                (map_, mutable) = ret
                entry = TypeTable.Entry(map_[id_], mutable)
                types[node] = entry

        visitor = Visitor()
        visitor.visit(self._ir.module)
