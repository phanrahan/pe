# Type System
## Base Types
Our system has two kinds of base types:
- User defined enumerated kind, similar to `enum` types in C/C++. Types of the enumerated kind only allow for the comparison operators *equals* and *not equals*, as well being the subject of a *switch-case* statement.
- Word kind, parameterized by a word-size, which is a positive integer. Types of the word kind allow for all operations allowed on CoreIR primitive types. These are also similar to the *BitVector* type.

## Qualifiers
The system supports the following qualifiers on types:
- Register: The *register* qualifier marks the variable as a stateful variable. Note that the *register* qualifier is not allowed to be applied on nested types, only on base types. The *register* qualifier is ignored (anywhere that it appears) for input and output types.
- Configuration: The *configuration* qualifier marks the variable as being a configuration input. Note that the *configuration* qualifier can only be used on function inputs (i.e. it can not be used on outputs or intermediate variables). The configuration qualifier can be applied on all types, including nested types.

## Compound Types
The system has the following templated compound types:
- Array type: This type is templated over 1 other base type and represents a statically sized collection of that type. Array types also require a positive-integer *size* argument. Array types support the slice operation, which takes in either a positive integer or an appropriately sized word, and returns an instance of the underlying base type.
- Encoded type: This type is templated over a collection of base types (with names), and has struct-like semantics, wherein one of the named base types can be accessed using the "." operator.

**A note on nesting types:** For the first version of the type system, we disallow arbitrarily nested compound types. So, array/encoded types can only be templated over base types (not compound types).

## Function Types
A function type is parameterized over a collection of input types and output types. The semantics are similar to function types in C++/Python/etc., in that such types represent functions with a signature derived from the input and output types. Instances of function types are not first-class citizens in the language (this should be an extension in a future version).

Function input types are not allowed to carry the *register* qualifier.

## Operations on Types
Here are a collection of rules on types (**TODO(raj): make this more organized and principled**):
- Types of the enumerated kind can only be used in equality comparison. That is, it only supports the *equals* and *not equals* operators. Also, it can be used as the subject of a *switch-case* statement.
- Types of the word kind can be used in any way that CoreIR primitives can. They can also thought of as being similar to the *BitVector* type.
- Variables which appear in the input list of a function are completely immutable. This **both** means that the programmer is not allowed to modify the variable and that the value will not change for the lifetime of a virtual cycle.
- Variables which appear in the output list of a function **must** be assigned to in the function. Not doing so will result in a compile-time error. In other words, dangling output wires are not allowed.
- Inputs which carry the *configuration* qualifier can be assumed to not change between virtual cycles.

## Example
This example shows the flavor and usage of the type system. **The syntax is not important here**, other than to convey the usages of the various types in a familiar-looking front-end.
```C++
// A user defined enumerated type.
enum Op { ADD, SUB, ABS, MOV }

// An encoded type, which is parameterized over a named-tuple of types.
using InstructionType = Encoded<Op op,
                                Word<5> ra,
                                Word<5> rb,
                                Word<5> dst,
                                Word<10> imm>

void Cpu(InstructionType instruction) {
    // We can construct compound types (in this case Arrays) which are
    // "templated" over other base types. We can apply the register qualifier to
    // the template argument type.
    Array<register Word<16>> regfile(32)
    Array<register Word<16>> memory(65536)

    Word<16> ra_val = regfile[instruction.ra]
    Word<16> rb_val = regfile[instruction.rb]

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
}
```
