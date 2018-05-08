import math
from pe_lib import *

################################################################################
# BEGIN PE Code
################################################################################
# Helper const variables.
FLAG_SELS = set([
    "z", "not_z", "c", "not_c", "n", "not_n", "v", "not_v",
    "c_and_not_z", "not_c_or_z", "n_equal_v", "n_not_equal_v",
    "not_z_and_n_equal_v", "z_or_n_not_equal_v", "lut_code", "comp_res_p"])
REG_MODES = set(["CONST", "VALID", "BYPASS", "DELAY"])
OPS = set([])

# Decalre all configuration state here.
lut_code = Input('configuration', 'quantitative', width=3)
data0_const = Input('configuration', 'quantitative', width=16)
data1_const = Input('configuration', 'quantitative', width=16)
bit0_const = Input('configuration', 'quantitative', width=1)
bit1_const = Input('configuration', 'quantitative', width=1)
bit2_const = Input('configuration', 'quantitative', width=1)
debug_trig = Input('configuration', 'quantitative', width=16)
debug_trig_p = Input('configuration', 'quantitative', width=1)

data0_mode = Input('configuration', 'nominal', value_set=REG_MODES)
data1_mode = Input('configuration', 'nominal', value_set=REG_MODES)
bit0_mode = Input('configuration', 'nominal', value_set=REG_MODES)
bit1_mode = Input('configuration', 'nominal', value_set=REG_MODES)
bit2_mode = Input('configuration', 'nominal', value_set=REG_MODES)

flag_sel = Input('configuration', 'nominal', value_set=FLAG_SELS)

irq_enable_0 = Input('configuration', 'quantitative', width=1)
irq_enable_1 = Input('configuration', 'quantitative', width=1)
acc_en = Input('configuration', 'quantitative', width=1)
signed = Input('configuration', 'quantitative', width=1)

instruction = Input('configuration', 'nominal', value_set=OPS)

# Data and bit registers.
data_regs = RegisterFile(16, 2)  # 2 16-bit registers
bit_regs = RegisterFile(1, 3)  # 3 1-bit registers

# Dynamic arguments.
data0 = Input('dynamic', 'quantitative', width=16)
data1 = Input('dynamic', 'quantitative', width=16)
bit0 = Input('dynamic', 'quantitative', width=1)
bit1 = Input('dynamic', 'quantitative', width=1)
bit2 = Input('dynamic', 'quantitative', width=1)

# Declare 2 outputs which are the result and the predicate.
res = Output('quantitative', width=16)
res_p = Output('quantitative', width=1)

# Flag select logic is factored out since it is common to all ops. Each op
# should call this function to determine the predicate.
def get_flag_sel(z, c, n, v):
    if flag_sel == "z": return z
    elif flag_sel == "not_z": return not z
    elif flag_sel == "c": return c
    elif flag_sel == "not_c": return not c
    elif flag_sel == "n": return n
    # ... specify remaining flag select modes here.

# Register store logic is implemented here. It is fairly simple: for each
# register if its mode is 'VALID' then store the corresponding input data in the
# register.
if data0_mode == 'VALID': data_regs[0] = data0
if data1_mode == 'VALID': data_regs[1] = data1
if bit0_mode == 'VALID': bit_regs[0] = bit0
if bit1_mode == 'VALID': bit_regs[1] = bit1
if bit2_mode == 'VALID': bit_regs[2] = bit2

# Register read logic is implemented here. Based on the mode, each register
# "reads" out a different value (e.g. CONST --> const config value).
def get_data():
    def get_individual(mode, const, reg, dyn):
        if mode == 'CONST': return const
        if mode == 'VALID': return reg
        if mode == 'BYPASS': return dyn
        return None
    return (
        get_individual(data0_mode, data0_const, data_regs[0], data0),
        get_individual(data1_mode, data1_const, data_regs[1], data1),
        get_individual(bit0_mode, bit0_const, bit_regs[0], bit0),
        get_individual(bit1_mode, bit1_const, bit_regs[1], bit1),
        get_individual(bit2_mode, bit2_const, bit_regs[2], bit2))

# Common entry point for all operations. This function handles all the common
# logic for each op. For example, here we call the get_flag_sel() function, as
# well as compute the common flag values, Z and N. An op only needs to define
# the logic for computing: (a) the ALU result, (b) the C flag, and (c) both the
# signed and unsigned versions of the V flag.
def do_op(op_fn, c_fn, v_fn, v_unsigned_fn):
    (d0, d1, b0, b1, b2) = get_data()
    res = op_fn(d0, d1)
    c = c_fn(d0, d1, b1)
    v = v_fn(d0, d1, b1)
    v_unsigned = v_unsigned_fn(data0, data1, bit1)
    v = v if signed == 1 else v_unsigned
    z = res == 0
    n = res[15]
    res_p = get_flag_sel(z, c, n, v)

# Here we specify each op. For most ops all we have to do is call the do_op()
# function and pass in the necessary custom logic for computing results and the
# C and V flags.
if instruction == 'add':
    do_op(
        lambda a, b : return a + b,
        lambda a, b, d: return (a + b + d) >= 2 ** 16,
        lambda a, b, d: return (a[15] == b[15]) and (a[15] != (a + b + d)[15]),
        lambda a, b, d: return (a + b + d) >= 2 ** 16)
elif instruction == 'sub':
    do_op(
        lambda a, b : return a + ~b + 1,
        lambda a, b, d: return (a + ~b + 1) >= 2 ** 16
        lambda a, b, d: return (a[15] != [b15]) and (a[15] != (a + ~b + 1)[15])
        lambda a, b, d: return 0)
# ... specify rest of ops here.
################################################################################
# END PE Code
################################################################################
