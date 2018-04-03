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

    @property
    def const(self):
        return self.mode == CONST

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

    def __init__(self, op, opcode, width, signed=False, double=False):
        self.op = op
        self.signed = signed
        self.double = double
        self.opcode = opcode
        self.width = width
        self._carry = False

    def __call__(self, op_a=0, op_b=0, c=0, op_d_p=0):
        a = BitVector(op_a, num_bits=self.width, signed=self.signed)
        b = BitVector(op_b, num_bits=self.width, signed=self.signed)
        c = BitVector(c, num_bits=self.width, signed=self.signed)
        d = BitVector(op_d_p, num_bits=self.width, signed=self.signed)
        res = self.op(a, b, c, d)
        if self._carry:
            res_p = BitVector(a._value + b._value >= (2 ** self.width), 1)
            return res, res_p
        return res


    def carry(self):
        self._carry = True


class COND:

    def __init__(self, cond, signed=False):
        self.cond = cond
        self.signed = signed

    def __call__(self, a, b, res):
        return_vals = self.compare(a, b, res)
        return self.cond(*return_vals)

    def compare(self, a, b, res):
        eq = a == b
        eq = eq.as_int()
        a_msb = msb(a)
        b_msb = msb(b)
        c_msb = msb(res)
        if self.signed:
            ge = int((~(a_msb ^ b_msb) & ~c_msb) | (~a_msb & b_msb)) & 1
            le = int((~(a_msb ^ b_msb) & c_msb) | (a_msb & ~b_msb) | eq) & 1
        else:
            ge = int((~(a_msb ^ b_msb) & ~c_msb) | (a_msb & ~b_msb)) & 1
            le = int((~(a_msb ^ b_msb) & c_msb) | (~a_msb & b_msb) | eq) & 1
        return BitVector(ge, num_bits=1), \
               BitVector(eq, num_bits=1), \
               BitVector(le, num_bits=1), \



class PE:

    def __init__(self, opcode, alu=None, signed=0):
        self.alu(opcode, signed, alu)
        self.cond()
        self.reg()
        self.place()
        self._lut = None
        self.flag_sel = 0x0

    def __call__(self, data0=0, data1=0, c=0, bit0=0, bit1=0, bit2=0):

        ra = self.RegA(data0)
        rb = self.RegB(data1)
        rc = self.RegC(c)
        rd = self.RegD(bit0)
        re = self.RegE(bit1)
        rf = self.RegF(bit2)

        res = ZERO
        res_p = BITZERO

        if self._add:
            add = self._add(ra, rb, rc, rd)

        if self._alu:
            res = self._alu(ra, rb, rc, rd)
            if isinstance(res, tuple):
                res, alu_res_p = res[0], res[1]

        lut_out = BITZERO
        if self._lut:
            lut_out = self._lut(rd, re, rf)

        res_p = self.get_flag(ra, rb, rc, rd, res, alu_res_p, lut_out)
        if not isinstance(res_p, BitVector):
            assert res_p in {0, 1}, res_p
            res_p = BitVector(res_p, 1)
        # if self._cond:
        #     res_p = self._cond(ra, rb, res)

        return res.as_int(), res_p.as_int()

    def get_flag(self, ra, rb, rc, rd, alu_res, alu_res_p, lut_out):
        Z = alu_res == 0
        if self.opcode & 0xFF == 0x0: # add
            C = (BitVector(ra, num_bits=17) + BitVector(rb, num_bits=17) + BitVector(rd, num_bits=7))[16]
        elif self.opcode & 0xFF == 0x1: # sub
            C = (BitVector(ra, num_bits=17) + BitVector(~rb, num_bits=17) + 1)[16]
        elif self.opcode & 0xFF == 0x3: # abs
            C = (BitVector(~ra, num_bits=17) + 1)[16]
        else:
            C = (BitVector(ra, num_bits=17) + BitVector(rb, num_bits=17))[16]
        N = alu_res[15]
        if self.opcode & 0xFF == 0x0: # add
            V = (ra[15] == rb[15]) and (ra[15] != (ra + rb + rd)[15])
        elif self.opcode & 0xFF == 0x1: # sub
            V = (ra[15] != rb[15]) and (ra[15] != (ra + ~rb + 1)[15])
        elif self.opcode & 0xFF == 0x3: # abs
            V = ra == 0x8000
            # V = alu_res[15]
        elif self.opcode & 0xFF in [0xb, 0xc]: # mul0, mul1
            V = (ra * rb)[15] if (ra[15] == rb[15]) else (ra * rb)[15] == 0 and (ra != 0 or rb != 0)
        elif self.opcode & 0xFF == 0xd:
            V = 0
        else:
            V = (ra[15] == rb[15]) and (ra[15] != (ra + rb)[15])
        if self.opcode & 0xFF in [0x12, 0x13, 0x14,  # and, or, xor clear overflow flag
                                  0xf, 0x11,         # lshl, lshr
                                  0x8]:              # sel
            V = 0
        if self.flag_sel == 0x0:
            return Z
        elif self.flag_sel == 0x1:
            return not Z
        elif self.flag_sel == 0x2:
            return C
        elif self.flag_sel == 0x3:
            return not C
        elif self.flag_sel == 0x4:
            return N
        elif self.flag_sel == 0x5:
            return not N
        elif self.flag_sel == 0x6:
            return V
        elif self.flag_sel == 0x7:
            return not V
        elif self.flag_sel == 0x8:
            return C and not Z
        elif self.flag_sel == 0x9:
            return not C or Z
        elif self.flag_sel == 0xA:
            return N == V
        elif self.flag_sel == 0xB:
            return N != V
        elif self.flag_sel == 0xC:
            return not Z and (N == V)
        elif self.flag_sel == 0xD:
            return Z or (N != V)
        elif self.flag_sel == 0xE:
            return lut_out
        elif self.flag_sel == 0xF:
            return alu_res_p
        raise NotImplementedError(self.flag_sel)

    def alu(self, opcode, signed, _alu):
        self.opcode = config('0000000l0dsoooooo', o=opcode, s=signed)
        self._signed = signed
        self._alu = ALU(_alu, opcode, DATAWIDTH, signed=signed)
        return self

    def signed(self, _signed=True):
        self._signed = _signed
        self._alu.signed = _signed
        return self

    def flag(self, flag_sel):
        self.opcode &= ~(0xFF << 12)
        self.opcode |= flag_sel << 12
        self.flag_sel = flag_sel
        return self

    def add(self, _add=None):
        self._add = _add
        return self

    def carry(self):
        self._alu.carry()
        return self

    def cond(self, _cond=None):
        self._add = None
        self._cond = None
        if _cond:
            self.add(lambda a, b, c, d: a+b if _cond else None)
            self._cond = COND(_cond, self._signed)
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

    def lut(self, code=None):
        def _lut(bit0, bit1, bit2):
            idx = (bit2.as_int() << 2) | (bit1.as_int() << 1) | bit0.as_int()
            return (code >> idx) & 1
        self._lut = _lut
        # if self.lut:
        #     self.opcode |= 1 << 9
        # else:
        #     self.opcode &= ~(1 << 9)
        return self

    def dual(self):
        self.opcode |= 1 << 7
        return self

    def place(self, x=None, y=None):
        self.x = x
        self.y = y
        return self
