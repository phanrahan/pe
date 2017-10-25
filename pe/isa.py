from .config import config
from .pe import PE, ALU, COND, CONST

__all__ = ['or_', 'and_', 'xor', 'inv']

def or_():
    return PE( 0x12, ALU(lambda a, b, c, d: a | b) )

def and_():
    return PE( 0x13, ALU(lambda a, b, c, d: a & b) )

def xor():
    return PE( 0x14, ALU(lambda a, b, c, d: a ^ b) )

def inv():
    return PE( 0x15, ALU(lambda a, b, c, d: ~a) )


def lshr():
    # b[3:0]
    return PE( 0xf, ALU(lambda a, b, c, d: a >> b) )

def ashr():
    # b[3:0]
    return PE( 0x10, ALU(lambda a, b, c, d: a >> b), signed=1 )

def lshl():
    # b[3:0]
    return PE( 0x11, ALU(lambda a, b, c, d: a << b) )


def add():
    # res_p = cout
    return PE( 0x0, ALU(lambda a, b, c, d: a + b + d) )

def sub():
    # res = (a - b) + c
    return PE( 0x1, ALU(lambda a, b, c, d: a - b + d) )

def abs():
    # res = abs(a-b) + c
    return PE( 0x3, ALU(lambda a, b, c, d: a if a >= 0 else -a) )


# this isn't correct
def ge(signed):
    # res = a >= b ? a : b (comparison should be signed/unsigned)
    return PE( 0x4, ALU(lambda a, b, c, d: a-b), 
                    COND(lambda ge, eq, le: ge, signed), signed=signed )

max = ge

def le(signed):
    # res = a <= b ? a : b (comparison should be signed/unsigned)
    return PE( 0x5, ALU(lambda a, b, c, d: a-b), 
                    COND(lambda ge, eq, le: le, signed), signed=signed )

min = le

def eq():
    # res?
    return PE( 0x6, ALU(lambda a, b, c, d: a-b), 
                    COND(lambda ge, eq, le: eq) )


def sel():
    return PE( 0x8, ALU(lambda a, b, c, d: a if d else b) )

def const(value):
    return PE( 0x0, ALU(lambda a, b, c, d: a) ).reg( ra=CONST, raconst=value )

