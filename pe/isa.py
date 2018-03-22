from .config import config
from .pe import PE, CONST
from .bv import BitVector

__all__  = ['or_', 'and_', 'xor', 'inv']
__all__ += ['lshr', 'lshl', 'ashr']
__all__ += ['add', 'sub']
__all__ += ['min', 'max', 'abs']
__all__ += ['eq', 'ge', 'le']
__all__ += ['sel']
__all__ += ['const']
__all__ += ['mul0', 'mul1', 'mul2']

def or_():
    return PE( 0x12, lambda a, b, c, d: a | b).carry()

def and_():
    return PE( 0x13, lambda a, b, c, d: a & b ).carry()

def xor():
    return PE( 0x14, lambda a, b, c, d: a ^ b ).carry()

def inv():
    return PE( 0x15, lambda a, b, c, d: ~a )

def neg():
    return PE( 0x15, lambda a, b, c, d: ~a+b ).regb(CONST, 1)


def lshr():
    # b[3:0]
    return PE( 0xf, lambda a, b, c, d: a >> b[:4] ).carry()

def ashr():
    # b[3:0]
    return PE( 0x10, lambda a, b, c, d: a >> b, signed=1 )

def lshl():
    # b[3:0]
    return PE( 0x11, lambda a, b, c, d: a << b[:4] ).carry()


def add():
    # res_p = cout
    return PE( 0x0, lambda a, b, c, d: a + b + d ).carry()

def sub():
    def _sub(a, b, c, d):
        res_p = BitVector(a, a.num_bits + 1) + BitVector(~b, b.num_bits + 1) + 1 >= 2 ** 16
        return a - b, res_p
    return PE( 0x1, _sub)


def eq():
    raise NotImplementedError("eq should use sub with Z flag")
    # res?
    # return PE( 0x6, lambda a, b, c, d: a+b ).cond( lambda ge, eq, le: eq )

def ge(signed):
    # res = a >= b ? a : b (comparison should be signed/unsigned)
    def _ge(a, b, c, d):
        res = a if a >= b else b
        res_p = a >= b
        return res, res_p
    return PE( 0x4, _ge, signed=signed ).cond( lambda ge, eq, le: ge ) 

max = ge

def le(signed):
    # res = a <= b ? a : b 
    def _le(a, b, c, d):
        res = a if a <= b else b
        res_p = a <= b
        return res, res_p
    return PE( 0x5, _le, signed=signed ).cond( lambda ge, eq, le: le )

min = le

def abs():
    # res = abs(a-b) + c
    def _abs(a, b, c, d):
        return a if a >= 0 else ~a+1, a[15]
    return PE( 0x3, _abs , signed=True).regb(CONST, 0)


def sel():
    return PE( 0x8, lambda a, b, c, d: a if d else b ).carry()

def const(value):
    return PE( 0x0, lambda a, b, c, d: a ).rega( CONST, value )

def mul2():
    def _mul(a, b, c, d):
        res_p = BitVector(a, 17) * BitVector(b, 17) + BitVector(c, 17)
        return a * b, res_p >= 2 ** 16
    return PE(0xd, _mul)

def mul1():
    def _mul(a, b, c, d):
        res_p = BitVector(a, 25) * BitVector(b, 25) + c
        return (BitVector(a, 24) * BitVector(b, 24))[8:], res_p >= 2 ** 24
    return PE(0xc, _mul)

def mul0():
    def _mul(a, b, c, d):
        return (BitVector(a, 32) * BitVector(b, 32))[16:], 0
    return PE(0xb, _mul)
