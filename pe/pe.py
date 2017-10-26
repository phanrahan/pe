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
        return self.op(a, b, c, d)


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

    def __init__(self, opcode, alu=None, cond=None, signed=0):
        self.alu(opcode, signed, alu, cond)
        self.reg()
        self.place()

    def __call__(self, a, b=0, c=0, d=0, e=0, f=0):

        ra = self.RegA(a)
        rb = self.RegB(b)
        rc = self.RegC(c)
        rd = self.RegD(d)
        re = self.RegE(e)
        rf = self.RegF(f)

        res = ZERO
        if self.op:
            res = self.op(ra, rb, rc, rd).as_int()

        res_p = BITZERO
        if self.cond:
            res_p = self.cond(a, b, res).as_int()

        return res, res_p

    def alu(self, opcode, signed, op, cond):
        self.opcode = config('0000000l0dsoooooo', o=opcode, s=signed)
        self.op = op
        self.cond = cond
        return self

    def reg(self):
        self.regcode = 0
        self.rega()
        self.regb()
        self.regc()
        self.regd()
        self.rege()
        self.regf()
        return self

    def rega(self, regmode=BYPASS, regvalue=0):
        self.RegA = Register(regmode, regvalue, DATAWIDTH)
        self.raconst = regvalue
        self.regcode &= ~(3 << 0)
        self.regcode |= config('aa', a=regmode)
        return self

    def regb(self, regmode=BYPASS, regvalue=0):
        self.RegB = Register(regmode, regvalue, DATAWIDTH)
        self.rbconst = regvalue
        self.regcode &= ~(3 << 2)
        self.regcode |= config('aa', a=regmode) << 2
        return self

    def regc(self, regmode=BYPASS, regvalue=0):
        self.RegC = Register(regmode, regvalue, DATAWIDTH)
        self.rcconst = regvalue
        self.regcode &= ~(3 << 4)
        self.regcode |= config('aa', a=regmode) << 4
        return self

    def regd(self, regmode=BYPASS, regvalue=0):
        self.RegD = Register(regmode, regvalue, 1)
        self.rdconst = regvalue
        self.regcode &= ~(3 << 8)
        self.regcode |= config('aa', a=regmode) << 8
        return self

    def rege(self, regmode=BYPASS, regvalue=0):
        self.RegE = Register(regmode, regvalue, 1)
        self.reconst = regvalue
        self.regcode &= ~(3 << 10)
        self.regcode |= config('aa', a=regmode) << 10
        return self

    def regf(self, regmode=BYPASS, regvalue=0):
        self.RegF = Register(regmode, regvalue, 1)
        self.rfconst = regvalue
        self.regcode &= ~(3 << 12)
        self.regcode |= config('aa', a=regmode) << 12
        return self

    def lut(self, table=None):
        self.lut = table
        if self.lut:
            self.opcode |= 1 << 9
        else:
            self.opcode &= ~(1 << 9)
        return self

    def dual(self):
        self.opcode |= 1 << 7
        return self

    def place(self, x=None, y=None):
        self.x = x
        self.y = y
        return self
