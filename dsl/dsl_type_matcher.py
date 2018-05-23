import ast
import dsl_types

class Match:
    @staticmethod
    def make_false(*errors):
        return Match(False, errors)

    def __init__(self, match, data):
        self.__match = match
        self.__data = data

    @property
    def data(self):
        return self.__data

    @property
    def errors(self):
        return self.__errors

    def __bool__(self):
        return self.__match

    def __or__(self, other):
        if not isinstance(other, Match):
            raise TypeError("Expected other Match object")
        if self.__match:
            return Match(True, self.__data)
        if other.__match:
            return Match(True, other.__data)
        return Match.make_false(*self.__data, *other.__data)

    def __repr__(self):
        return "{match: %s, data: %s}" % (self.__match, self.data)


class TypeMatcher:
    def __init__(self, user_defined_types):
        self.__user_defined_types = user_defined_types
        self.__errors = []
        self.__nodes = []

    @property
    def errors(self):
        return self.__errors

    @property
    def nodes(self):
        return self.__nodes

    def match_TopLevelType(self, node):
        return self.match_Input(node) | \
            self.match_Output(node) | \
            self.match_Intermediate(node)

    def match_Input(self, node):
        match = self.__match_func(node, "Input", self.match_QualifiedType)
        if not match:
            return match
        return Match(True, dsl_types.Input(*match.data))

    def match_Output(self, node):
        match = self.__match_func(node, "Output", self.match_QualifiedType)
        if not match:
            return match
        return Match(True, dsl_types.Output(*match.data))

    def match_Intermediate(self, node):
        match = self.__match_func(
            node, "Intermediate", self.match_QualifiedType)
        if not match:
            return match
        return Match(True, dsl_types.Intermediate(*match.data))

    def match_QualifiedType(self, node):
        return self.match_UnqualifiedType(node) | \
            self.match_Register(node) | \
            self.match_Configuration(node)

    def match_Register(self, node):
        match = self.__match_func(node, "Register", self.match_QualifiedType)
        if not match:
            return match
        return Match(True, dsl_types.Register(*match.data))

    def match_Configuration(self, node):
        match =  self.__match_func(
            node, "Configuration", self.match_QualifiedType)
        if not match:
            return match
        return Match(True, dsl_types.Configuration(*match.data))

    def match_UnqualifiedType(self, node):
        return self.match_BaseType(node) | \
            self.match_Array(node) | \
            self.match_Encoded(node)

    def match_Array(self, node):
        match = self.__match_func(
            node, "Array", self.match_UnqualifiedType, self.match_Num)
        if not match:
            return match
        return Match(True, dsl_types.Array(*match.data))

    def match_Encoded(self, node):
        NAME = "Encoded"
        ARG_ERR_MSG = "Expected even number of arguments >= 2"
        if not TypeMatcher.__match_func_name(node, NAME):
            return Match.make_false(("Expected %s" % NAME, node))
        args = node.args
        if len(args) == 0 or len(args) % 2:
            return Match.make_false((ARG_ERR_MSG, node))
        fields = {}
        for i in range(0, len(args), 2):
            type_arg = args[i]
            name_arg = args[i + 1]
            type_arg_match = self.match_BaseType(type_arg)
            if not type_arg_match:
                return type_arg_match
            if not isinstance(name_arg, ast.Name) or \
               name_arg.id in fields:
                return Match.make_false(("Expected unique name", name_arg))
            fields[name_arg.id] = type_arg_match.data
        return Match(True, dsl_types.Encoded(fields))

    def match_BaseType(self, node):
        return self.match_BitVector(node) | \
            self.match_Enum(node)

    def match_BitVector(self, node):
        match = self.__match_func(node, "BitVector", self.match_Num)
        if not match:
            return match
        return Match(True, dsl_types.BitVector(*match.data))

    def match_Enum(self, node):
        if isinstance(node, ast.Name) and \
           node.id in self.__user_defined_types:
            return Match(True, dsl_types.Enum(self.__user_defined_types[node.id]))
        return Match.make_false(("Expected enum", node))

    def match_Num(self, node):
        if isinstance(node, ast.Num):
            return Match(True, node.n)
        return Match.make_false(("Expected number node", node))

    @staticmethod
    def __match_func_name(node, name):
        return isinstance(node, ast.Call) and \
            isinstance(node.func, ast.Name) and \
            node.func.id == name

    def __match_func(self, node, name, *funcs):
        if not TypeMatcher.__match_func_name(node, name):
            return Match.make_false(("Expected %s" % name, node))
        if len(funcs) != len(node.args):
            return Match.make_false(
                ("Expected %d arguments" % len(funcs), node))
        types = []
        for (arg, func) in zip(node.args, funcs):
            match = func(arg)
            if not match:
                return match
            types.append(match.data)
        return Match(True, types)
