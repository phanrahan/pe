from .config import config
from .pe import PE, ALU, COND

__all__ = ['or_', 'and_', 'xor', 'inv']

def or_():
    code = config('l0dsooooo', o=0x12)
    return PE( code, ALU(lambda a, b, c, d: a | b) )

def and_():
    code = config('l0dsooooo', o=0x13)
    return PE( code, ALU(lambda a, b, c, d: a & b) )

def xor():
    code = config('l0dsooooo', o=0x14)
    return PE( code, ALU(lambda a, b, c, d: a ^ b) )

def inv():
    code = config('l0dsooooo', o=0x15)
    return PE( code, ALU(lambda a, b, c, d: ~a) )


def lshr():
    code = config('l0dsooooo', o=0xf)
    # mask b
    return PE( code, ALU(lambda a, b, c, d: a >> b) )

def ashr():
    code = config('l0dsooooo', o=0x10)
    return PE( code, ALU(lambda a, b, c, d: a >> b) )

def lshl():
    code = config('l0dsooooo', o=0x11)
    return PE( code, ALU(lambda a, b, c, d: a << b) )


def add():
    code = config('l0dsooooo', o=0x0)
    # res_p = full sum has 2 extra bits; cout is 1 if either of those are 1
    return PE( code, ALU(lambda a, b, c, d: a + b) )

def sub():
    code = config('l0dsooooo', o=0x1)
    return PE( code, ALU(lambda a, b, c, d: a - b) )

def abs():
    code = config('l0dsooooo', o=0x3)
    return PE( code, ALU(lambda a, b, c, d: abs(a)) )


def ge(signed):
    code = config('l0dsooooo', o=0x4)
    return PE( code, ALU(lambda a, b, c, d: a-b), 
                     COND(lambda ge, eq, le: ge, signed) )

max = ge

def le(signed):
    code = config('l0dsooooo', o=0x5)
    return PE( code, ALU(lambda a, b, c, d: a-b), 
                     COND(lambda ge, eq, le: le, signed) )

min = le

def eq():
    code = config('l0dsooooo', o=0x6)
    return PE( code, ALU(lambda a, b, c, d: a-b), 
                     COND(lambda ge, eq, le: eq) )


def sel():
    code = config('l0dsooooo', o=0x8)
    return PE( code, ALU(lambda a, b, c, d: a if d else b) )

def const(value):
    code = config('l0dsooooo', o=0x0) # add
    return PE( code, ALU(lambda a, b, c, d: a), raconst=value)

