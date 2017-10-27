from .config import config
from .pe import PE, CONST

__all__  = ['or_', 'and_', 'xor', 'inv']
__all__ += ['lshr', 'lshl', 'ashr']
__all__ += ['add', 'sub']
__all__ += ['min', 'max', 'abs']
__all__ += ['eq', 'ge', 'le']
__all__ += ['sel']
__all__ += ['const']

def or_():
    return PE( 0x12, lambda a, b, c, d: a | b)

def and_():
    return PE( 0x13, lambda a, b, c, d: a & b )

def xor():
    return PE( 0x14, lambda a, b, c, d: a ^ b )

def inv():
    return PE( 0x15, lambda a, b, c, d: ~a )

def neg():
    return PE( 0x15, lambda a, b, c, d: ~a+b ).regb(CONST, 1)


def lshr():
    # b[3:0]
    return PE( 0xf, lambda a, b, c, d: a >> b )

def ashr():
    # b[3:0]
    return PE( 0x10, lambda a, b, c, d: a >> b, signed=1 )

def lshl():
    # b[3:0]
    return PE( 0x11, lambda a, b, c, d: a << b )


def add():
    # res_p = cout
    return PE( 0x0, lambda a, b, c, d: a + b + d )

def sub():
    # res = (a - b) + c
    return PE( 0x1, lambda a, b, c, d: a - b + d )


def eq():
    # res?
    return PE( 0x6, lambda a, b, c, d: a-b ).cond( lambda ge, eq, le: eq )

def ge(signed):
    # res = a >= b ? a : b (comparison should be signed/unsigned)
    return PE( 0x4, lambda a, b, c, d: a if a >= b else b, signed=signed ).cond( lambda ge, eq, le: ge ) 

max = ge

def le(signed):
    # res = a <= b ? a : b 
    return PE( 0x5, lambda a, b, c, d: a if a <= b else b, signed=signed ).cond( lambda ge, eq, le: le )

min = le

def abs():
    # res = abs(a-b) + c
    return PE( 0x3, lambda a, b, c, d: a if a >= 0 else ~a+1 )


def sel():
    return PE( 0x8, lambda a, b, c, d: b if d else a )

def const(value):
    return PE( 0x0, lambda a, b, c, d: a ).rega( CONST, value )

