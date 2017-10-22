from .bv import BitVector
from .config import config

__all__ = ['PE']

DATAWIDTH = 16

CONST = 0
VALID = 1
BYPASS = 2
DELAY = 3

BITZERO = BitVector(0, num_bits=1)
ZERO = BitVector(0, num_bits=DATAWIDTH)

def msb(value):
    return value[-1]

def signed(value):
    return BitVector(value._value, value.num_bits, signed=True)

class Register:
    def __init__(self, mode, init, width):
        self.mode = mode
        self.value = BitVector(init, num_bits=width)
        self.width = width

    def __call__(self, value):
        if not isinstance(value, BitVector):
            value = BitVector(value, self.width)

        retvalue = value
        if self.mode == DELAY:
            self.value = value
        elif self.mode == CONST:
            retvalue = self.value
        return retvalue

class ALU:
    def __init__(self, op, signed=False, double=False):
        self.op = op
        self.signed = signed
        self.double = double

    def __call__(self, a, b, c, d):
        if self.signed:
            a = signed(a)
            b = signed(b)
            c = signed(c)
            d = signed(d)
        return self.op(a,b,c,d)

class COND:
    def __init__(self, cond, signed=False):
        self.cond = cond
        self.signed = signed

    def __call__(self, a, b, res):
        ge, eq, le = self.compare(a, b, res)
        return self.cond(ge, eq, le)

    def compare(self, a, b, res):
        eq = a == b
        a_msb = msb(a)
        b_msb = msb(b)
        res_msb = msb(res)
        if self.signed:
            ge = int((~(a_msb ^ b_msb) & ~c_msb) | (~a_msb & b_msb)) & 1
            te = int((~(a_msb ^ b_msb) & c_msb) | (a_msb & ~b_msb) | eq) & 1
        else:
            ge = int((~(a_msb ^ b_msb) & ~c_msb) | (a_msb & ~b_msb)) & 1
            le = int((~(a_msb ^ b_msb) & c_msb) | (~a_msb & b_msb) | eq) & 1
        return BitVector(ge, num_bits=1), \
               BitVector(eq, num_bits=1), \
               BitVector(le, num_bits=1)


class PE:
    def __init__(self, inst, \
        alu=None, cond=None, lut=None, \
        ra=BYPASS, raconst=0, \
        rb=BYPASS, rbconst=0, \
        rc=BYPASS, rcconst=0, \
        rd=BYPASS, rdconst=0, \
        re=BYPASS, reconst=0, \
        rf=BYPASS, rfconst=0, \
        x=None, y=None):

        self.inst = inst

        self.alu = alu
        self.cond = cond
        self.lut = lut

        self.RegA = Register(ra, raconst, DATAWIDTH)
        self.RegB = Register(rb, rbconst, DATAWIDTH)
        self.RegC = Register(rc, rcconst, DATAWIDTH)
        self.RegD = Register(rd, rdconst, 1)
        self.RegE = Register(re, reconst, 1)
        self.RegF = Register(rf, rfconst, 1)

        self.x = x
        self.y = y

    def __call__(self, a, b=0, c=0, d=0, e=0, f=0):
        ra = self.RegA(a)
        rb = self.RegB(b)
        rc = self.RegC(c)
        rd = self.RegD(d)
        re = self.RegE(e)
        rf = self.RegF(f)

        res = ZERO
        if self.alu:
            res = self.alu(ra, rb, rc, rd).as_int()

        res_p = BITZERO
        if self.cond:
            res_p = self.cond(a, b, res).as_int()

        return res, res_p
