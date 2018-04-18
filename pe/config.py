class Field:
    def __init__(self, start):
        self.start = start
        self.width = 1

    def __call__(self, value):
        mask = (1 << (self.width)) - 1
        return (value & mask) << (self.start - self.width)

def config(format, **args):
    n = len(format)
    bits = 0
    fields = {}
    field = None
    for i in range(n):
        c = format[i]
        if c != ' ' and c != '\t':
            bits <<= 1
            if c == '0' or c == '1':
                field = None
                bits |= (c == '1')
            else:
                # should check that c's are consecutive
                if c not in fields:
                    field = Field(n-i)
                    fields[c] = field
                else:
                    field.width += 1

    for c, field in fields.items():
        value = args[c] if c in args else 0
        bits |= field(value)

    return bits

#print(bin(config('11bb', b=2)))
#print(bin(config('aabb', a=1, b=2)))
#print(bin(config('l0dsooooo', o=0x8)))

