import ast
import collections
import jinja2
import bit_vector
import dsl_backend
import dsl_ir
import dsl_types


class Register:
    @staticmethod
    def __get_value(type_):
        if isinstance(type_, dsl_types.Array):
            value = Register.__get_value(type_.t)
            return [value for _ in range(type_.size)]
        if isinstance(type_, dsl_types.Encoded):
            ret = {}
            for k, v in type_.encoding.items():
                ret[k] = Register.__get_value(v)
            return ret
        return Register.Null()

    class Null():
        def __eq__(self, other):
            return type(other) == Register.Null

        def __repr__(self):
            return "(null)"

    def __init__(self, type_):
        self.__type = type_
        self.__curr = Register.__get_value(self.__type)
        self.__next = Register.__get_value(self.__type)

    @property
    def curr(self):
        return self.__curr

    @property
    def next(self):
        return self.__next

    @curr.setter
    def curr(self, curr_in):
        self.__curr = curr_in

    @next.setter
    def next(self, next_in):
        self.__next = next_in

    def update(self):
        if Register.Null() != self.next:
            self.curr = self.next
        self.next = Register.__get_value(self.__type)

    def __repr__(self):
        return "{curr: %s, next: %s}" % (self.curr.__repr__(),
                                         self.next.__repr__())


class DslFunctionalModelBackend(dsl_backend.DslBackend):
    class RegisterTransformer(ast.NodeTransformer):
        def __init__(self, registers, ctx=ast.Load()):
            self.__registers = registers
            self.__ctx = ctx

        def __add_attr(self, node):
            attr = "curr" if isinstance(self.__ctx, ast.Load) else "next"
            return ast.Attribute(
                value=ast.Name(
                    id=node.id,
                    ctx=ast.Load()),
                attr=attr,
                ctx=node.ctx)

        def visit_Assign(self, node):
            self.__ctx = ast.Store()
            targets = [self.visit(t) for t in node.targets]
            node.targets = targets
            self.__ctx = ast.Load()
            value = self.visit(node.value)
            node.value = value
            return node

        def visit_Name(self, node):
            if node.id not in self.__registers:
                return node
            ret = self.__add_attr(node)
            ast.copy_location(ret, node)
            ast.fix_missing_locations(ret)
            return ret

    @staticmethod
    def __filter_names(var_map, type_predicate=lambda t: True):
        names = [name for name, t in var_map.items() if type_predicate(t)]
        return set(names)

    def __init__(self, ir : dsl_ir.Ir, *,
                 add_type_checks : bool = False,
                 kwarg_check : bool = False,
                 debug_src_file : str = None):
        super().__init__(ir)
        self.__add_type_checks = add_type_checks
        self.__kwarg_check = kwarg_check
        self.__debug_src_file = debug_src_file

    def __type_check_input(self, name, value):
        def type_match(uqt, v):
            if isinstance(uqt, dsl_types.BitVector):
                return isinstance(v, bit_vector.BitVector) and \
                    uqt.width == v.num_bits
            if isinstance(uqt, dsl_types.Enum):
                return isinstance(v, uqt.enum_cls)
            if isinstance(uqt, dsl_types.Encoded):
                for kk, vv in uqt.encoding.items():
                    ret = hasattr(v, kk) and type_match(vv, getattr(v, kk))
                    if not ret:
                        return False
                return True
            return False
        type_ = self._ir.io.inputs[name]
        unqualified_type = type_.unqualified_type
        if not type_match(unqualified_type, value):
            raise TypeError("Expected %s" % unqualified_type)

    def get_module_code(self):
        return compile(self._ir.module, self._ir.src_filename, mode="exec")

    def generate(self):
        cls = DslFunctionalModelBackend
        inputs = self._ir.io.inputs
        outputs = self._ir.io.outputs
        intermediates = self._ir.intermediates.intermediates
        for var_map in inputs, outputs, intermediates:
            for name, type_ in var_map.items():
                var_map[name] = dsl_types.TypeHelper.TypeInfo.create(type_)
        dynamics = cls.__filter_names(
            inputs,
            lambda t : dsl_types.Configuration not in t.qualifiers)
        configurations = cls.__filter_names(
            inputs,
            lambda t : dsl_types.Configuration in t.qualifiers)
        outputs = cls.__filter_names(outputs)
        registers = cls.__filter_names(
            intermediates,
            lambda t : dsl_types.Register in t.qualifiers)

        transformer = cls.RegisterTransformer(registers)
        transformer.visit(self._ir.module)

        CLS_NAME = "Model"
        tpl_str = ""
        with open("functional_model.py.tpl", 'r') as f:
            tpl_str = f.read()
        tpl = jinja2.Template(tpl_str)

        src = tpl.render(
            TYPES=self._ir.user_defined_types.types.keys(),
            CLS_NAME=CLS_NAME,
            OUTPUT_CLS_NAME="Output",
            DYNAMICS=dynamics,
            CONFIGS=configurations,
            OUTPUTS=outputs,
            REGISTERS=registers,
            ADD_TYPE_CHECKS=self.__add_type_checks,
            KWARG_CHECK=self.__kwarg_check,
        )

        if self.__debug_src_file is not None:
            with open(self.__debug_src_file, 'w') as f:
                f.write(src)

        builtins_ = {
            "concat" : bit_vector.BitVector.concat,
        }
        ctx = {
            "ast" : ast,
            "namedtuple" : collections.namedtuple,
            "bit_vector" : bit_vector,
            "Register" : lambda n: Register(intermediates[n].unqualified_type),
            "type_check_input" : lambda n, v : self.__type_check_input(n, v),
            "user_defined_types" : self._ir.user_defined_types.types,
            "module_code" : self.get_module_code(),
            "builtins_" : builtins_,
        }

        if self.__debug_src_file is not None:
            compiled = compile(src, self.__debug_src_file, mode="exec")
            exec(compiled, ctx)
        else:
            exec(src, ctx)
        return ctx[CLS_NAME]
