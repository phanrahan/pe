from typing import Dict


class EnumEncoding:
    def __init__(self, bit_width : int, mapping : Dict[str, int]):
        self.__bit_width = bit_width
        self.__mapping = mapping

    @property
    def bit_width(self):
        return self.__bit_width

    @property
    def mapping(self):
        return self.__mapping

    def __repr__(self):
        return ("{bit_width: %s, mapping: %s}" %
                (self.__bit_width, self.__mapping))


class DslDecodeSpecification:
    def __init__(self):
        self.__enums = {}
        self.__encoded = {}

    @property
    def enums(self):
        return self.__enums

    @property
    def encoded(self):
        return self.__encoded

    def add_enum(self, name : str, enum_encoding : EnumEncoding):
        self.__enums[name] = enum_encoding

    def add_encoded(self, encoded : str,
                    encoding : Dict[str, range],
                    bit_width = None):
        max_bit = max([v.stop for k, v in encoding.items()])
        if bit_width is None:
            bit_width = max_bit + 1
        if bit_width <= max_bit:
            raise ValueError("bit_width must be >= max bit in encoding")
        self.__encoded[encoded] = (encoding, bit_width)

    def __repr__(self):
        return "{enums: %s, encoded: %s}" % (self.__enums, self.__encoded)
