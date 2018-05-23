import ast
import enum
from typing import Dict


'''
Type system abstract grammar:

BaseType ::= BitVector(int w)
           | Enum(str id)

UnqualifiedType ::= BaseType
                  | Array(UnqualifiedType t)
                  | Encoded((BaseType t, str id)+)

QualifiedType ::= UnqualifiedType
                | Register(QualifiedType t)
                | Configuration(QualifiedType t)

TopLevelType ::= Input(QualifiedType t)
               | Output(QualifiedType t)
               | Intermediate(QualifiedType t)
'''

class QualifiedType:
    pass


class UnqualifiedType(QualifiedType):
    pass


class BaseType(UnqualifiedType):
    pass


class Enum(BaseType):
    def __init__(self, enum_cls : enum.EnumMeta):
        if not isinstance(enum_cls, enum.EnumMeta):
            raise TypeError("enum_cls should be an enum.EnumMeta")
        self.__enum_cls = enum_cls

    @property
    def enum_cls(self):
        return self.__enum_cls

    def __repr__(self):
        return "enum %s" % self.enum_cls.__name__


class BitVector(BaseType):
    def __init__(self, width : int):
        if not isinstance(width, int):
            raise TypeError("width should be an int")
        self.__width = width

    @property
    def width(self):
        return self.__width

    def __repr__(self):
        return "BitVector<%d>" % self.width


class Array(UnqualifiedType):
    def __init__(self, t : UnqualifiedType, size : int):
        if not isinstance(t, UnqualifiedType):
            raise TypeError("t should be an UnqualifiedType")
        if not isinstance(size, int):
            raise TypeError("size should be an int")
        self.__t = t
        self.__size = size

    @property
    def t(self):
        return self.__t

    @property
    def size(self):
        return self.__size

    def __repr__(self):
        return "Array<%s, %d>" % (self.t, self.size)


class Encoded(UnqualifiedType):
    def __init__(self, encoding : Dict[str, BaseType]):
        if not isinstance(encoding, dict):
            raise TypeError("encoding should be a dict")
        self.__encoding = encoding

    @property
    def encoding(self):
        return self.__encoding

    def __repr__(self):
        return "Encoded<%s>" % self.encoding


class Configuration(QualifiedType):
    def __init__(self, t : QualifiedType):
        if not isinstance(t, QualifiedType):
            raise TypeError("t should be a QualifiedType")
        self.__t = t

    @property
    def t(self):
        return self.__t

    def __repr__(self):
        return "Configuration<%s>" % self.t


class Register(QualifiedType):
    def __init__(self, t : QualifiedType):
        if not isinstance(t, QualifiedType):
            raise TypeError("t should be a QualifiedType")
        self.__t = t

    @property
    def t(self):
        return self.__t

    def __repr__(self):
        return "Register<%s>" % self.t


class TopLevelType:
    pass


class Input(TopLevelType):
    def __init__(self, t : QualifiedType):
        if not isinstance(t, QualifiedType):
            raise TypeError("t should be a QualifiedType")
        self.__t = t

    @property
    def t(self):
        return self.__t

    def __repr__(self):
        return "Input<%s>" % self.t


class Output(TopLevelType):
    def __init__(self, t : QualifiedType):
        if not isinstance(t, QualifiedType):
            raise TypeError("t should be a QualifiedType")
        self.__t = t

    @property
    def t(self):
        return self.__t

    def __repr__(self):
        return "Output<%s>" % self.t


class Intermediate(TopLevelType):
    def __init__(self, t : QualifiedType):
        if not isinstance(t, QualifiedType):
            raise TypeError("t should be a QualifiedType")
        self.__t = t

    @property
    def t(self):
        return self.__t

    def __repr__(self):
        return "Intermediate<%s>" % self.t


class TypeHelper:
    class TypeInfo:
        @staticmethod
        def create(type_ : QualifiedType):
            if not isinstance(type_, QualifiedType):
                raise TypeError("Expected QualifiedType")
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
            return set([Configuration]) | TypeHelper.get_qualifiers(type_.t)
        if isinstance(type_, Register):
            return set([Register]) | TypeHelper.get_qualifiers(type_.t)
        raise TypeError("Expected type_ to be DSL type")

    @staticmethod
    def get_base_type(type_):
        if isinstance(type_, BaseType):
            return type_
        if isinstance(type_, Array):
            return TypeHelper.get_base_type(type_.t)
        if isinstance(type_, Encoded):
            return None
        if isinstance(type_, QualifiedType):
            return TypeHelper.get_base_type(type_.t)
        raise TypeError("Expected type_ to be DSL type")

    @staticmethod
    def get_unqualified_type(type_):
        if isinstance(type_, UnqualifiedType):
            return type_
        if isinstance(type_, QualifiedType):
            return TypeHelper.get_unqualified_type(type_.t)
        raise TypeError("Expected type_ to be DSL type")

    @staticmethod
    def get_qualified_type(type_):
        if isinstance(type_, QualifiedType):
            return type_
        raise TypeError("Expected type_ to be DSL type")
