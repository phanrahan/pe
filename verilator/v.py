from pe import and_
from testvectors import complete
from verilator import compile 

a = and_()

tests = complete(a, 4, 16)
compile('test_pe_comp_unq1',a.opcode,tests)


