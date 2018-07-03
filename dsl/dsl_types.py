import enum
from typing import Dict


'''
Type system abstract grammar:

BaseType ::= BitVector(int width)
           | Enum(enum.EnumMeta enum_cls)

UnqualifiedType ::= BaseType
                  | Array(UnqualifiedType type, int size)
                  | Encoded(Dict[str, BaseType])

QualifiedType ::= UnqualifiedType
                | Register(QualifiedType type)
                | Configuration(QualifiedType type)

TopLevelType ::= Input(QualifiedType type)
               | Output(QualifiedType type)
               | Intermediate(QualifiedType type)
'''


class QualifiedType():
    pass


class UnqualifiedType(QualifiedType):
    pass


class BaseType(UnqualifiedType):
    pass


class BitVector(BaseType):
    def __init__(self, width : int):
        if not isinstance(width, int):
            raise TypeError("expected width to be int")
        self.__width = width

    @property
    def width(self):
        return self.__width

    def __repr__(self):
        return "BitVector<%d>" % self.width


class Enum(BaseType):
    def __init__(self, enum_cls : enum.EnumMeta):
        if not isinstance(enum_cls, enum.EnumMeta):
            raise TypeError("expected enum_cls to be enum.EnumMeta")
        self.__enum_cls = enum_cls

    @property
    def enum_cls(self):
        return self.__enum_cls

    def __repr__(self):
        return "enum %s" % self.enum_cls.__name__


class Array(UnqualifiedType):
    def __init__(self, type : BaseType, size : int):
        if not isinstance(type, BaseType):
            raise TypeError("expected type to be BaseType")
        if not isinstance(size, int):
            raise TypeError("expected size to be int")
        self.__type = type
        self.__size = size

    @property
    def type(self):
        return self.__type

    @property
    def size(self):
        return self.__size

    def __repr__(self):
        return "Array<%s, %d>" % (self.type, self.size)


class Encoded(UnqualifiedType):
    def __init__(self, encoding : Dict[str,BaseType]):
        if not isinstance(encoding, dict):
            raise TypeError("expected encoding to be Dict[str,BaseType]")
        self.__encoding = encoding

    @property
    def encoding(self):
        return self.__encoding

    def __repr__(self):
        return "Encoded<%s>" % self.encoding


class Register(QualifiedType):
    def __init__(self, type : QualifiedType):
        if not isinstance(type, QualifiedType):
            raise TypeError("expected type to be QualifiedType")
        self.__type = type

    @property
    def type(self):
        return self.__type

    def __repr__(self):
        return "Register<%s>" % self.type


class Configuration(QualifiedType):
    def __init__(self, type : QualifiedType):
        if not isinstance(type, QualifiedType):
            raise TypeError("expected type to be QualifiedType")
        self.__type = type

    @property
    def type(self):
        return self.__type

    def __repr__(self):
        return "Configuration<%s>" % self.type


class TopLevelType():
    pass


class Input(TopLevelType):
    def __init__(self, type : QualifiedType):
        if not isinstance(type, QualifiedType):
            raise TypeError("expected type to be QualifiedType")
        self.__type = type

    @property
    def type(self):
        return self.__type

    def __repr__(self):
        return "Input<%s>" % self.type


class Output(TopLevelType):
    def __init__(self, type : QualifiedType):
        if not isinstance(type, QualifiedType):
            raise TypeError("expected type to be QualifiedType")
        self.__type = type

    @property
    def type(self):
        return self.__type

    def __repr__(self):
        return "Output<%s>" % self.type


class Intermediate(TopLevelType):
    def __init__(self, type : QualifiedType):
        if not isinstance(type, QualifiedType):
            raise TypeError("expected type to be QualifiedType")
        self.__type = type

    @property
    def type(self):
        return self.__type

    def __repr__(self):
        return "Intermediate<%s>" % self.type


class TypeHelper:
    class TypeInfo:
        @staticmethod
        def create(type_ : QualifiedType):
            if not isinstance(type_, QualifiedType):
                raise TypeError("expected QualifiedType")
            return TypeHelper.TypeInfo(
                TypeHelper.get_qualifiers(type_),
                TypeHelper.get_base_type(type_),
                TypeHelper.get_unqualified_type(type_),
                TypeHelper.get_qualified_type(type_))

        def __init__(self, qualifiers : set,
                     base_type : BaseType,
                     unqualified_type : UnqualifiedType,
                     qualified_type : QualifiedType):
            self.__qualifiers = qualifiers
            self.__base_type = base_type
            self.__unqualified_type = unqualified_type
            self.__qualified_type = qualified_type

        @property
        def qualifiers(self):
            return self.__qualifiers

        @property
        def base_type(self):
            return self.__base_type

        @property
        def unqualified_type(self):
            return self.__unqualified_type

        @property
        def qualified_type(self):
            return self.__qualified_type

        def __repr__(self):
            out = {}
            for k, v in self.__dict__.items():
                out[k.replace("_TypeInfo__", "")] = v
            return str(out)

    @staticmethod
    def get_qualifiers(type_):
        if isinstance(type_, (BaseType, UnqualifiedType)):
            return set()
        if isinstance(type_, Configuration):
            return set([Configuration]) | TypeHelper.get_qualifiers(type_.type)
        if isinstance(type_, Register):
            return set([Register]) | TypeHelper.get_qualifiers(type_.type)
        raise TypeError("expected type_ to be DSL type")

    @staticmethod
    def get_base_type(type_):
        if isinstance(type_, BaseType):
            return type_
        if isinstance(type_, Array):
            return TypeHelper.get_base_type(type_.type)
        if isinstance(type_, Encoded):
            return None
        if isinstance(type_, QualifiedType):
            return TypeHelper.get_base_type(type_.type)
        raise TypeError("expected type_ to be DSL type")

    @staticmethod
    def get_unqualified_type(type_):
        if isinstance(type_, UnqualifiedType):
            return type_
        if isinstance(type_, QualifiedType):
            return TypeHelper.get_unqualified_type(type_.type)
        raise TypeError("Expected type_ to be DSL type")

    @staticmethod
    def get_qualified_type(type_):
        if isinstance(type_, QualifiedType):
            return type_
        raise TypeError("Expected type_ to be DSL type")
