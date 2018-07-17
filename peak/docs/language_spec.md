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

# Programming Model

## Functional Description
Our language enables the specification of a function which describes the functional behavior of a PE. The underlying premise is that for any valid specification, there is a corresponding stateful function (or FSM). The goal of the language is to allow the specification of this function in a natural and high-level way.

## PE's as Functions
In our language, each PE will be described as a function. This function is statically typed, i.e. the type of all inputs and outputs is known ahead of time. The body of the function describes how inputs are consumed, outputs are produced, and state is updated.

### Virtual Cycle
The most important abstraction in the programming model is that of the *virtual cycle*. A virtual cycle is defined as a uniform time period in which all perscriped operations take place atomically. It is important to note that a virtual cycle does not necesarily have any bearing on the clock in the implementation. The only constraint is that for each virtual cycle, there is a corresponding time period in the implementation for which the (outputs, state) pair match that of the end of the virtual cycle. Another important implication of the virtual cycle is that all reads from a stateful variable (i.e. registers and memory) return the same value over the course of the virtual cycle.

### Analogy to RTL
If we were to cast the programming model to an RTL language, it would look as follows: first we would declare all inputs, outputs, and intermediate variables as wires (as well as include inputs and outputs in a sensitivity list). All stateful variables would be declared as registers (or collections of registers). Then **all logic** would fit in a big `always @(posedge clk)` block, with all register assignments being **non-blocking**. A cycle of this `clk` corresponds to a virtual cycle in our language. This description matches almost exactly to our programming model. The only difference is that in our language intermediate values can take on multiple values throughout a virtual cycle, where as in an RTL language, only the last of a series of continuous assignments of a wire takes effect.

# Examples
These examples shows the flavor and usage of the type system and programming model. **The syntax is not important here**, other than to convey the language semantics in a familiar-looking front-end.

## CPU Example
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

## CGRA PE Example
```C++
// User defined enumerated types.
enum FlagSel { Z, NOT_Z, C, NOT_C }
enum RegMode { CONST, VALID, BYPASS, DELAY }
enum Op { ADD, SUB, ABS }

// Convenience typedefs.
using ConfigDataType = configuration Word<16>
using ConfigBitType = configuration Word<1>

(Word<16> res, Word<1> res_p) CgraPe(
    configuration Word<3> lut_code,
    ConfigDataType data0_const,
    ConfigDataType data1_const,
    ConfigBitType bit0_const,
    ConfigBitType bit1_const,
    ConfigBitType bit2_const,
    ConfigDataType debug_trig,
    ConfigBitType debug_trig_p,
    configuration RegMode data0_mode,
    configuration RegMode data1_mode,
    configuration RegMode bit0_mode,
    configuration RegMode bit1_mode,
    configuration RegMode bit2_mode,
    configuration FlagSel flag_sel,
    ConfigBitType irq_enable_0,
    ConfigBitType irq_enable_1,
    ConfigBitType acc_en,
    ConfigBitType signed,
    configuration Op op,
    Word<16> data0,
    Word<16> data1,
    Word<1> bit0,
    Word<1> bit1,
    Word<1> bit2) {
    // We can construct compound types (in this case Arrays) which are
    // "templated" over other base types. We can apply the register qualifier to
    // the template argument type.
    register Word<16> data0_reg
    register Word<16> data1_reg
    register Word<1> bit0_reg
    register Word<1> bit1_reg
    register Word<1> bit2_reg

    // Implement the register mode logic (both store and load). Sets the
    // "effective" value for data0, based on the addressing mode. If the mode is
    // VALID, then the effective value is the output of the register. If the
    // mode IS CONST, then the effective value is the const configuration value.
    // If it is BYPASS, then it its the input data0. This logic should be
    // repeated for each register and input (data and bits).
    Word<16> data0_eff = Word<16>()
    switch (data0_mode) {
        case RegMode.VALID: {
            data0_reg = data0
            data0_eff = data0_reg
        }
        case RegMode.CONST: {
            data0_eff = data0_const
        }
        case RegMode.BYPASS: {
            data0_eff = data0
        }
    }
    // Do the same for data1, bit0, bit1, and bit2.

    // Implement the actual instruction logic.
    Word<1> c = Word<1>()
    Word<1> vs = Word<1>()  // v signed.
    Word<1> vu = Word<1>()  // v unsigned.
    switch (instruction.op) {
        case Op.ADD: {
            res = data0_eff + data1_eff
            c = (data0_eff + data1_eff + bit1_eff) >= 2 ** 16
            vs = (data0_eff[15] == data1_eff[15]) and \
                 (data0_eff[15] != (data0_eff + data1_eff + bit1_eff)[15])
            vu = (data0_eff + data1_eff + bit1_eff) >= 2 ** 16)
        }
        case Op.SUB: {
            res = data0_eff + ~data1_eff + 1,
            c = (data0_eff + ~data1_eff + 1) >= 2 ** 16
            vs = (data0_eff[15] != data1_eff[15]) and \
                 (data0_eff[15] != (data0_eff + ~data1_eff + 1)[15])
            vu = Word<1>(0)
        }
        // Implement the rest of the ops here.
        default: {
            // Some default logic or error condition.
        }
    }
    Word<1> n = signed[15]
    Word<1> v = signed ? vs : vu

    switch (flag_sel) {
        case FlagSel.Z: { res_p = z }
        case FlagSel.NOT_Z: { res_p = ~z }
        case FlagSel.C: { res_p = c }
        case FlagSel.NOT_C { res_p = ~c }
        // Implement rest of cases here.
        default: { /* some default code here */ }        
    }
}
```
