from bit_vector import BitVector

# Here we model the pe as a pure (stateless) function. For this reason, we
# ignore stateful components such as reigsters, memory, etc.

def pe(lut_code, data0_const, data1_const, bit0_const, bit1_const, bit2_const, debug_trig, debug_trig_p, bit2_mode, bit1_mode, bit0_mode, data1_mode, data0_mode, flag_sel, irq_en, acc_en, signed, operation, data0_in, data1_in, bit0_in, bit1_in, bit2_in):
    # Compute effective input data based on the register modes. Note that we
    # ignore the valid and delay modes because this a pure (stateless) function.
    # NOTE(raj): Subsequently, all functions should use data_in as input
    # data_values.
    data_in = [data0_in, data1_in, bit0_in, bit1_in, bit2_in]
    reg_modes = [data0_mode, data1_mode, bit0_mode, bit1_mode, bit2_mode]
    reg_const_values = [data0_const, data1_const, bit0_const, bit1_const, bit2_const]
    for i in range(5):
        if reg_modes[i] == 0:  # const mode
            data_in[i] = reg_const_values[i]
    (data0, data1, bit0, bit1, bit2) = data_in
     # get_flag_sel captures the flag selection logic as a function of
     # underlying flags z, c, n, v, and comp_res_v. It is basically a multiplex
     # of functions of these values, using @flag_sel as the select signal.
    def get_flag_sel(z, c, n, v, comp_res_p):
        if flag_sel == 0:
            return z
        elif flag_sel == 1:
            return ~z
        elif flag_sel == 2:
            return c
        elif flag_sel == 3:
            return ~c
        elif flag_sel == 4:
            return n
        elif flag_sel == 5:
            return ~n
        elif flag_sel == 6:
            return v
        elif flag_sel == 7:
            return ~v
        elif flag_sel == 8:
            return c & ~z
        elif flag_sel == 9:
            return ~c | z
        elif flag_sel == 10:
            return n == v
        elif flag_sel == 11:
            return n != v
        elif flag_sel == 12:
            return ~z & (n == v)
        elif flag_sel == 13:
            return z | (n != v)
        elif flag_sel == 14:
            return lut_code[[bit2, bit1, bit0]]
        elif flag_sel == 15:
            return comp_res_p
    # We define internal flags c, v(signed), and v(unsigned) as well as common
    # flags n and z (see below) which are all used as input by the function
    # get_flag_sel(). Here we declare their default values. The function
    # compute() should change the values of these internal flags based on the
    # operation.
    c = data0 + data1 >= BitVector(2 ** 16)
    v_signed = 0
    v_unsigned = 0
    # NOTE(raj): There are many more op's here that are similar in flavor to
    # these. For completeness we should include these, but we exclude this for
    # brevity and the sake of exposition.
    def compute():
        if operation == 0:  # add
            res = data0 + data1 + bit1
            c = res >= BitVector(2 ** 16)
            v_signed = (data0[15] == data1[15]) and (data0[15] != (data0 + data1 + bit1)[15])
            v_unsigned = c
            return res, c
        elif operation == 1:  # sub
            res = data0 + ~data1 + 1
            c = (data0 + ~data1 + 1) >= BitVector(2 ** 16)
            v_signed = (data0[15] != data1[15]) and (data0[15] != (data0 + ~data1 + 1)[15])
            v_unsigned = 0
            return res, c
        elif operation == 3:  # abs
            res = (0 - data0) if data0[15] else data0
            c = (~data0 + 1) >= BitVector(2**16)
            v_signed = (~data0 + 1)[15]
            v_unsigned = v_signed
            return res, data0[15]
    res, res_p = compute()
    z = (res == 0)
    n = res[15]
    v_eff = v_signed if signed else v_unsigned
    flag = get_flag_sel(z, c, n, v_eff, res_p)
    # We capture the irq logic explicitly since it is simple and not reused.
    irq_trigger = \
                  (irq_en[0] and (flag != debug_trig_p)) or \
                  (irq_en[1] and (res != debug_trig))
    # The final output of this function is a tuple containing the actual ALU
    # output, the 1 bit predicate (determined by the @flag_sel input), and the
    # interrupt trigger debug signal
    return res, flag, irq_trigger
