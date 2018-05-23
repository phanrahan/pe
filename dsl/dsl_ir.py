import ast


class Ir:
    class UserDefinedTypes:
        def __init__(self, types):
            self.__types = types

        @property
        def types(self):
            return self.__types

        def __repr__(self):
            return self.types.__repr__()

    class Io:
        def __init__(self, inputs, outputs):
            self.__inputs = inputs
            self.__outputs = outputs

        @property
        def inputs(self):
            return self.__inputs

        @property
        def outputs(self):
            return self.__outputs

        def __repr__(self):
            return ("{inputs: %s, outputs: %s}" %
                    (self.inputs, self.outputs))

    class Intermediates:
        def __init__(self, intermediates):
            self.__intermediates = intermediates

        @property
        def intermediates(self):
            return self.__intermediates

        def __repr__(self):
            return self.intermediates.__repr__()

    def __init__(self,
                 src_filename : str,
                 user_defined_types : UserDefinedTypes,
                 io : Io,
                 intermediates : Intermediates,
                 module : ast.Module) -> None:
        self.__src_filename = src_filename
        self.__user_defined_types = user_defined_types
        self.__io = io
        self.__intermediates = intermediates
        self.__module = module

    @property
    def src_filename(self):
        return self.__src_filename

    @property
    def user_defined_types(self):
        return self.__user_defined_types

    @property
    def io(self):
        return self.__io

    @property
    def intermediates(self):
        return self.__intermediates

    @property
    def module(self):
        return self.__module
