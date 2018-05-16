# Type System
## Base Types
Our system has two base types:
- User defined enumerated types, similar to `enum` types in C/C++. The only operations allowed on enumerated types are the comparison operators equals and not equals, as well being the subject of a switch-case statement.
- Word types, parameterized by a word-size, which is a positive integer. Word types have equivalent semantics to the `BitVector` type, and therefore support all operations allowed on `BitVectors`, including slicing.

## Qualifiers
The system supports the following qualifiers on base types:
- Register: The *register* qualifier marks the variable as a stateful variable.

## Compound Types
The system has the following templated compound types:
- Array type: This type is templated over 1 other base type and represents a statically sized collection of that type. Array types also require a positive-integer *size* argument. Array types support the slice operation, which takes in either a positive integer or an appropriately sized word, and returns an instance of the underlying base type.
- Encoded type: This type is templated over a collection of base types (with names), and has struct-like semantics, wherein one of the named base types can be accessed using the "." operator.

**A note on nesting types:** For the first version of the type system, we disallow arbitrarily nested compound types. So, array/encoded types can only be templated over base types (not compound types).

## Function Types
A function type is parameterized over a collection of input types and output types. The semantics are similar to function types in C++/Python/etc., in that such types represent functions with a signature derived from the input and output types. Instances of function types are not first-class citizens in the language (this should be an extension in a future version).


```
enum Op { ADD, SUB, ABS, MOV }

array<word(16)> regfile(32)
array<word(16)> memory(65536)

Op op
word(5) ra
word(5) rb
word(5) dst
word(10) imm

instruction = encode(op, ra, rb, dst, imm)

word(16) ra_val = regfile[instruction.ra]
word(16) rb_val = regfile[instruction.rb]

switch (instruction.op) {
    case Op.ADD: {
        regfile[instruction.dst] = ra_val + rb_val
    }
    case Op.SUB: {
        regfile[instruction.dst] = ra_val - rb_val
    }
    case Op.ABS: {
        regfile[instruction.dst] = (ra_val[15] == 1 ? (0 - ra_val) : ra_val)
    }
    default: {
        // Some default logic or error condition.
    }
}
```
