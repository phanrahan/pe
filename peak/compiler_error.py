import ast


class CompilerError(Exception):
    @staticmethod
    def get_line(filename, lineno):
        with open(filename, 'r') as f:
            for i, line in enumerate(f):
                if i + 1 == lineno:
                    return line
        return ""

    def __init__(self, msg : str, filename : str, node : ast.AST):
        self.__msg = msg
        self.__filename = filename
        self.__node = node

    def get_exception(self):
        exception = SyntaxError(self.__msg)
        exception.filename = self.__filename
        exception.lineno = self.__node.lineno
        exception.offset = self.__node.col_offset
        exception.text = CompilerError.get_line(exception.filename,
                                                   exception.lineno)
        return exception

    def __repr__(self):
        return ("{filename: %s, node: %s, msg: %s" %
                (self.__filename, ast.dump(self.__node), self.__msg))
