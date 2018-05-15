import pe_ir_atom


# Base interface for all ops.
class Op(pe_ir_atom.Atom):
    def __init__(self):
        super().__init__()


# Unary logic ops.
class Not(Op):
    def __init__(self):
        super().__init__()


# Binary arithmetic ops.
class Add(Op):
    def __init__(self):
        super().__init__()


class Sub(Op):
    def __init__(self):
        super().__init__()


# Special ops.
class Ternary(Op):
    def __init__(self):
        super().__init__()


class Slice(Op):
    def __init__(self):
        super().__init__()
