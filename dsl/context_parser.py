import pe_ir_nodes as nodes
import pe_ir_ops as ops
import pe_ir_types as types

class ParseStatus:
    def __str__(self):
        raise NotImplementedError("Can not call __str__ on abstract "
                                  "class ParseStatus")

    def ok(self):
        raise NotImplementedError("Can not call ok on abstract "
                                  "class ParseStatus")


class ParseSuccess(ParseStatus):
    def __str__(self):
        return "Parsing succeeded"

    def ok(self):
        return True


class ParseError(ParseStatus):
    def __str__(self):
        raise NotImplementedError("Can not call __str__ on abstract "
                                  "class ParseError")

    def ok(self):
        return False


class ParseTypeError(ParseError):
    def __init__(self, name, valid_types, obj):
        self.name = name
        self.valid_types = valid_types
        self.obj = obj

    def __str__(self):
        actual_type_name = type(self.obj).__name__
        valid_type_names = ", ".join([t.__name__ for t in self.valid_types])
        return ("Expected %s to be of type %s. Got %s instead." %
                (self.name, valid_type_names, actual_type_name))


class ContextParser:
    @staticmethod
    def parse_literal(node):
        if not isinstance(node.get_type(), types.Type):
            return ParseTypeError("Literal.type", (types.Type,),
                                  node.get_type())
        return ParseSuccess()

    @staticmethod
    def parse_variable_declaration(node):
        if not isinstance(node.get_id(), str):
            return ParseTypeError("VariableDeclaration.id", (str,),
                                  node.get_id())
        if not isinstance(node.get_type(), types.Type):
            return ParseTypeError("VariableDeclaration.type", (types.Type,),
                                  node.get_type())
        return ParseSuccess()

    @staticmethod
    def parse_name(node):
        if not isinstance(node.get_id(), str):
            return ParseTypeError("Name.id", (str,), node.get_id())
        return ParseSuccess()

    @staticmethod
    def parse_assignment(node):
        def parse_lvalue(lvalue):
            if isinstance(lvalue, nodes.Name):
                return ContextParser.parse_name(lvalue)
            if isinstance(lvalue, nodes.Expression) and \
               isinstance(lvalue.get_op(), ops.Slice):
                return ContextParser.parse_expression(lvalue)
            return ParseTypeError("Assignment.lhs",
                                  (nodes.Name, nodes.Expression), lvalue)

        lvalue_status = parse_lvalue(node.get_lhs())
        if not lvalue_status.ok():
            return lvalue_status
        return ContextParser.parse_expression(node.get_rhs())

    @staticmethod
    def parse_expression(node):
        def parse_op(op):
            if not isinstance(op, ops.Op):
                return ParseTypeError("Expression.op", (ops.Op,), op)
            return ParseSuccess()

        if isinstance(node, nodes.Name):
            return ContextParser.parse_name(node)
        if isinstance(node, nodes.Literal):
            return ContextParser.parse_literal(node)
        if isinstance(node, nodes.Expression):
            op_status = parse_op(node.get_op())
            if not op_status.ok():
                return op_status
            for arg in node.get_arguments():
                arg_status = ContextParser.parse_expression(arg)
                if not arg_status.ok():
                    return arg_status
            return ParseSuccess()
        # NOTE(raj): This is somewhat of a hack for now.
        if isinstance(node, (str, int)):
            return ParseSuccess()
        return ParseTypeError("Expression", (nodes.Name,
                                             nodes.Literal,
                                             nodes.Expression,
                                             str, int), node)

    @staticmethod
    def parse_switch_case(node):
        def parse_subject(subject):
            return ContextParser.parse_expression(subject)

        def parse_case(case):
            if isinstance(case, nodes.Literal):
                return ContextParser.parse_literal(case)
            return ParseTypeError("SwitchCase.case", (nodes.Literal,), case)

        subject_status = parse_subject(node.get_subject())
        if not subject_status.ok():
            return subject_status
        for case, body in node.get_case_map().items():
            case_status = parse_case(case)
            if not case_status.ok():
                return case_status
            body_status = ContextParser.parse_body(body)
            if not body_status.ok():
                return body_status
        return ParseSuccess()

    @staticmethod
    def parse_stmt(node):
        if isinstance(node, nodes.VariableDeclaration):
            return ContextParser.parse_variable_declaration(node)
        if isinstance(node, nodes.Assignment):
            return ContextParser.parse_assignment(node)
        if isinstance(node, nodes.SwitchCase):
            return ContextParser.parse_switch_case(node)
        return ParseTypeError("statement", (nodes.VariableDeclaration,
                                            nodes.Assignment,
                                            nodes.SwitchCase), node)

    @staticmethod
    def parse_body(body):
        for node in body:
            stmt_status = ContextParser.parse_stmt(node)
            if not stmt_status.ok():
                return stmt_status
        return ParseSuccess()

    def __init__(self):
        pass

    def parse_context(self, ctx):
        body = ctx.get_nodes()
        return ContextParser.parse_body(body)
