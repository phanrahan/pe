import bit_vector


class ConfigurationRegisterSpecification:
    def __init__(self):
        self.__mapping = {}

    def add_register(self, name : str, address : bit_vector.BitVector):
        self.__mapping[name] = address

    @property
    def mapping(self):
        return self.__mapping
