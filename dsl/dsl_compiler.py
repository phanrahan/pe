import ast
import enum
import inspect
from typing import Callable, Dict
from dsl_compiler_error import DslCompilerError
import dsl_ir
import dsl_types
import dsl_type_matcher


class DslCompiler:
    def __init__(self):
        pass

    def __compile_module(self, module : ast.Module) -> dsl_ir.Ir:
        filename = self.__filename
        user_defined_types = {}
        inputs = {}
        outputs = {}
        intermediates = {}

        def name_declared(_id):
            return _id in (inputs.keys() |
                           outputs.keys() |
                           intermediates.keys() |
                           user_defined_types.keys())

        class Transformer(ast.NodeTransformer):
            def visit_Assign(self, node):
                targets = node.targets
                if len(targets) > 1 or not isinstance(targets[0], ast.Name):
                    raise DslCompilerError(
                        "LHS of assignment must be a single name",
                        filename, node)
                _id = targets[0].id
                if name_declared(_id):
                    raise DslCompilerError(
                        "Redeclaration of %s" % _id, filename, node)
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
                    "Name %s used before declaration" % node.id,
                    filename, node)

            def visit_Expr(self, node):
                if isinstance(node.value, ast.Call) and \
                   isinstance(node.value.func, ast.Attribute) and \
                   node.value.func.attr == "assign":
                    args = node.value.args
                    if len(args) != 1:
                        error_node = node if len(args) == 0 else args[1]
                        raise DslCompilerError(
                            "assign() expects exactly 1 argument",
                            filename, error_node)
                    target = self.visit(node.value.func.value)
                    value = self.visit(args[0])
                    ret = ast.Assign(targets=[target], value=value)
                    ret.targets[0].ctx = ast.Store()
                    ast.copy_location(ret, node)
                    ast.fix_missing_locations(ret)
                    return ret
                return self.generic_visit(node)

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

        try:
            transformer = Transformer()
            transformer.visit(module)
        except DslCompilerError as e:
            raise e.get_exception() from None

        udt = dsl_ir.Ir.UserDefinedTypes(user_defined_types)
        io = dsl_ir.Ir.Io(inputs, outputs)
        im = dsl_ir.Ir.Intermediates(intermediates)
        return dsl_ir.Ir(self.__filename, udt, io, im, module)

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
        return self.__compile_module(module)
