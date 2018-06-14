import ast
import enum
import inspect
from typing import Callable, Dict
from dsl_compiler_error import DslCompilerError
import dsl_ir
import dsl_types
import dsl_type_matcher


class DslCompiler:
    ASSIGN_LHS_ERR_MSG = "LHS of assignment must be a single name"
    UNDECLARED_NAME_ERR_MSG = "Name %s used before declaration"

    def __init__(self):
        pass

    def __collect_vars(self, root, user_defined_types):
        inputs = {}
        outputs = {}
        intermediates = {}
        filename = self.__filename

        def name_declared(_id):
            return _id in (inputs.keys() |
                           outputs.keys() |
                           intermediates.keys() |
                           user_defined_types.keys())

        class VarCollector(ast.NodeTransformer):
            def visit_Assign(self, node):
                targets = node.targets
                if len(targets) > 1 or not isinstance(targets[0], ast.Name):
                    raise DslCompilerError(
                        DslCompiler.ASSIGN_LHS_ERR_MSG, filename, node)
                _id = targets[0].id
                if name_declared(_id):
                    raise DslCompilerError(
                        "Redeclaration of variable %s" % _id, filename, node)
                matcher = dsl_type_matcher.TypeMatcher(user_defined_types)
                match = matcher.match_TopLevelType(node.value)
                if not match:
                    raise DslCompilerError(match.data[0][0],
                                           filename,
                                           match.data[0][1])
                _type = match.data
                if isinstance(_type, dsl_types.Input):
                    inputs[_id] = _type.type
                elif isinstance(_type, dsl_types.Output):
                    outputs[_id] = _type.type
                elif isinstance(_type, dsl_types.Intermediate):
                    intermediates[_id] = _type.type
                else:
                    raise TypeError("Expected top level type")
                return None

            def visit_Name(self, node):
                if name_declared(node.id):
                    return node
                raise DslCompilerError(
                    DslCompiler.UNDECLARED_NAME_ERR_MSG % node.id,
                    filename, node)

        var_collector = VarCollector()
        var_collector.visit(root)
        return (inputs, outputs, intermediates)

    def __collect_user_defined_types(self, root):
        filename = self.__filename
        user_defined_types = {}

        class Transformer(ast.NodeTransformer):
            def visit_ClassDef(self, node):
                if len(node.bases) == 1 and \
                   isinstance(node.bases[0], ast.Name) and \
                   node.bases[0].id == "Enum":
                    name = node.name
                    compiled = compile(ast.Module([node]), filename, mode='exec')
                    ctx = {"Enum" : enum.Enum}
                    exec(compiled, ctx)
                    if name in user_defined_types:
                        raise DslCompilerError(
                            "Redeclaration of class %s" % name, filename, node)
                    user_defined_types[name] = ctx[name]
                    return None
                raise DslCompilerError("All user defined types must derive "
                                       "from Enum only", filename, node)

        transformer = Transformer()
        transformer.visit(root)
        return user_defined_types

    def __transform_assigns(self, root):
        filename = self.__filename

        class Transformer(ast.NodeTransformer):
            def __init__(self):
                pass

            def visit_Expr(self, node):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Attribute) and \
                       node.value.func.attr == "assign":
                        args = node.value.args
                        if len(args) != 1:
                            error_node = node if len(args) == 0 else args[1]
                            raise DslCompilerError(
                                "assign() expects exactly 1 argument",
                                filename, error_node)
                        ret = ast.Assign(targets=[node.value.func.value],
                                         value=args[0])
                        ret.targets[0].ctx = ast.Store()
                        ast.copy_location(ret, node)
                        ast.fix_missing_locations(ret)
                        return ret
                return node

        transformer = Transformer()
        transformer.visit(root)

    def __verify_ast(self, root):
        filename = self.__filename

        class Visitor(ast.NodeVisitor):
            UNSUPPORTED_NODES = {
                # For now we allow FunctionDef because we visit the root node
                # which we expect to be a function def.
                "ClassDef" : "class",
                "Return" : "return",
                "Delete" : "delete",
                "ClassDef" : "def",
                "For" : "for",
                "AsyncFor" : "async",
                "While" : "while",
                "With" : "with",
                "AsyncWith" : "async",
                "Raise" : "raise",
                "Try" : "try",
                "Assert" : "assert",
                "Import" : "import",
                "ImportFrom" : "from",
                "Global" : "global",
                "Nonlocal" : "nonlocal",
                # Note that 'pass' is allowed.
                "Break" : "break",
                "Continue" : "continue",
                "List" : "list",
                "Tuple" : "tuple",
            }

            @staticmethod
            def __unexpected_keyword(kw, node):
                raise DslCompilerError("Unexpected keyword '%s'" % kw,
                                       filename, node)

            def __init__(self):
                for node_type, label in Visitor.UNSUPPORTED_NODES.items():
                    fn = lambda n, l=label: \
                                      Visitor.__unexpected_keyword(l, n)
                    setattr(self, "visit_" + node_type, fn)

        visitor = Visitor()
        visitor.visit(root)

    def compile(self, fn : Callable[[], None]) -> dsl_ir.Ir:
        if not inspect.isfunction(fn):
            raise TypeError("Expected fn to be a function")
        self.__filename = inspect.getsourcefile(fn)
        (src_lines, base_lineno) = inspect.getsourcelines(fn)
        src = "".join(src_lines)
        parsed = ast.parse(src)
        fn_ast = parsed.body[0]
        fn_name = fn_ast.name
        num_args = len(fn_ast.args.args)
        if num_args > 0:
            raise ValueError("fn has %d arguments; expected 0" % num_args)
        module = ast.Module(body=fn_ast.body)
        ast.increment_lineno(module, base_lineno - 1)  # adjust line numbers.

        try:
            user_defined_types = self.__collect_user_defined_types(module)
            (inputs, outputs, intermediates) = self.__collect_vars(
                module, user_defined_types)
            self.__transform_assigns(module)
            self.__verify_ast(module)
        except DslCompilerError as e:
            raise e.get_exception() from None

        udt = dsl_ir.Ir.UserDefinedTypes(user_defined_types)
        io = dsl_ir.Ir.Io(inputs, outputs)
        im = dsl_ir.Ir.Intermediates(intermediates)
        return dsl_ir.Ir(self.__filename, udt, io, im, module)
