from bit_vector import BitVector
from pe_pure_function import *
from pe_as_closure import *

x = BitVector(0, 16)

out = pe(x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x)
print (out)

my_pe = generate_pe(x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x, x)

out = my_pe(x, x, x, x, x)
print (out)
