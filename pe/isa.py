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

def or_(flag_sel=0):
    return PE( 0x12 | flag_sel << 12, lambda a, b, c, d: a | b).carry()

def and_(flag_sel=0):
    return PE( 0x13 | flag_sel << 12, lambda a, b, c, d: a & b ).carry()

def xor(flag_sel=0):
    return PE( 0x14 | flag_sel << 12, lambda a, b, c, d: a ^ b ).carry()

def inv(flag_sel=0):
    return PE( 0x15 | flag_sel << 12, lambda a, b, c, d: ~a )

def neg(flag_sel=0):
    return PE( 0x15 | flag_sel << 12, lambda a, b, c, d: ~a+b ).regb(CONST, 1)


def lshr(flag_sel=0):
    # b[3:0]
    return PE( 0xf | flag_sel << 12, lambda a, b, c, d: a >> b[:4] ).carry()

def ashr(flag_sel=0):
    # b[3:0]
    return PE( 0x10 | flag_sel << 12, lambda a, b, c, d: a >> b, signed=1 )

def lshl(flag_sel=0):
    # b[3:0]
    return PE( 0x11 | flag_sel << 12, lambda a, b, c, d: a << b[:4] ).carry()


def add(flag_sel=0):
    # res_p = cout
    return PE( 0x0 | flag_sel << 12, lambda a, b, c, d: a + b + d ).carry()

def sub(flag_sel=0):
    def _sub(a, b, c, d):
        res_p = BitVector(a, a.num_bits + 1) + BitVector(~b, b.num_bits + 1) + 1 >= 2 ** 16
        return a - b, res_p
    return PE( 0x1 | flag_sel << 12, _sub)


def eq(flag_sel):
    raise NotImplementedError("eq should use sub with Z flag")
    # res?
    # return PE( 0x6, lambda a, b, c, d: a+b ).cond( lambda ge, eq, le: eq )

def ge(signed, flag_sel=0):
    # res = a >= b ? a : b (comparison should be signed/unsigned)
    def _ge(a, b, c, d):
        res = a if a >= b else b
        res_p = a >= b
        return res, res_p
    return PE( 0x4 | flag_sel << 12, _ge, signed=signed )

max = ge

def le(signed, flag_sel=0):
    # res = a <= b ? a : b 
    def _le(a, b, c, d):
        res = a if a <= b else b
        res_p = a <= b
        return res, res_p
    return PE( 0x5 | flag_sel << 12, _le, signed=signed )
min = le

def abs(flag_sel=0):
    # res = abs(a-b) + c
    def _abs(a, b, c, d):
        return a if a >= 0 else -a, a[15]
    return PE( 0x3 | flag_sel << 12, _abs , signed=True).regb(CONST, 0)


def sel(flag_sel=0):
    return PE( 0x8 | flag_sel << 12, lambda a, b, c, d: a if d else b ).carry()

def const(value):
    return PE( 0x0 | flag_sel << 12, lambda a, b, c, d: a ).rega( CONST, value )

def mul2(flag_sel=0):
    def _mul(a, b, c, d):
        res_p = BitVector(a, 17) * BitVector(b, 17) + BitVector(c, 17)
        return a * b, res_p >= 2 ** 16
    return PE(0xd, _mul)

def mul1(flag_sel=0):
    def _mul(a, b, c, d):
        res_p = BitVector(a, 25) * BitVector(b, 25) + c
        return (BitVector(a, 24) * BitVector(b, 24))[8:], res_p >= 2 ** 24
    return PE(0xc, _mul)

def mul0(flag_sel=0):
    def _mul(a, b, c, d):
        return (BitVector(a, 32) * BitVector(b, 32))[16:], 0
    return PE(0xb, _mul)
