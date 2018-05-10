# PE DSL Semantics Specification
This document includes a pseudo-formal specification of the language semantics. Note that this document **does not** describe the details of the syntax of the language. We begin with a discussion of the language atoms and their usage.

## Atoms
The language atoms essentially enumerate AST nodes/sub-trees. The language consists of the following atoms:

### Variables
Variables encompass a large set of atoms in the language. They can be categorized as follows:

#### Input Variables
Input variables are immutable and have two orthogonal qualifiers:
  1. Dynamic/Configuration qualifier. This qualifier can take on one of two values:
    1. Dynamic inputs are inputs which come into the PE "dynamically" at run-time. These correspond to real inputs; drawing an analogy to an RTL, these would be declared inputs of the top-level module, and appear in the sensitivity list.
    2. Configuration inputs are inputs which **do not** come into the PE dynamically; instead these inputs come from *configuration registers* which can be set (written to) at configuration time. The underlying explicit way to configure the PE (i.e. the exact configuration addresses and values to set each configuration register) is not implied by the specification itself. However, any implementation of a PE should adhere to the configuration semantics defined in the specification program.

  Once declared, dynamic and configuration inputs can be used in the same exact manner. There is no distinction downstream in their semantics.
  2. Nominal/Quantitative qualifier. This qualifier can take on one of two values:
    1. Nominal inputs are inputs which can take on exactly one of a discrete and finite set of values, similar to `enum` variables in C or C++. This set must be supplied at declaration time. Nominal inputs only support the `Equals` and `NotEquals` operators (i.e. arithmetic, logical, and greater/less than comparators are not allowed). Nominal inputs can also be the subject of `switch-case` statements (this is essentially sugar on top of `if-else` statements + the `Equals` operator).
    2. Quantintative inputs are inputs which can take on any value in the range `[0, 2^n - 1]` where `n`, must be supplied at declaration time. Essentially, quantitative inputs are general `n`-bit input wires. Quantintative inputs support all valid operators in the language, i.e. arithmetic and logic operations, and general comparison are allowed on quantintative inputs.

The qualifiers are orthogonal (both in terms of declaration and semantics), and must be specified at the time of declaration.

**A note on the nominal/quantitative qualifier design decision:** In any realizable digital design, *all* entities are n-bit wires, so in that domain, there is no distinction between nominal and quantitative variables, as we've defined them. However, there are 2 important aspects to the decision to make this distinction explicit in our language. First, this decouples the semantics/specification from the implementation. It allows the programmer/designer to think purely in terms of semantics when using nominal inputs, rather than the bit-level implementation. Second, it allows downstream backends (e.g. RTL generator) to perform optimizations on the encoding of these variables.

#### Intermediate Variables
Intermediate variables are atoms built by composing other variables using the operators supported on them. Intermediate variables do not carry the dynamic/configuration qualifier, since this is specific for input variables. They do, however, carry the nominal/quantitative qualifier. This qualifier is inferred through construction, rather than specified explicitly. For example, if an intermediate variable is assigned to be the value of another nominal variable, then it is of course nominal. If it is assigned to the sum of two other quantitative variables, then it is quantitative. This is one way in which variables are "strictly" typed (see the [Type System](#type-system)). Intermediate variables **are mutable** but that carries two important caveats:
  - Recursive assignments are not allowed. In short, an intermediate variable can not appear both on the left side **and** right side of an assignment. For example, if `x` and `y` are intermediate variables, then `Assign(x, BinaryOp(x, y, ...))` would not be allowed, for example. See [Combinational Loops](#combinational-loops) for more details.
  - The value produced by an intermediate variable is defined by the most recently executed assignment above it. Therefore, over the course of a [virtual cycle](#virtual-cycle), an intermediate variable can produce multiple variables.

  ** TODO(raj): Is this the right semantics to have here?? Would it just be easier to say that even intermediate variables are immutable and add this^ as an optimization later if it makes sense?? **
  - The nominal/quantitative qualifier is inferred upon declaration and **can not** be modified downstream. Therefore, all assignments of an intermediate variable must match the nominal/quantitative-ness of the initial declaration. **This implies that intermediate variables must be assigned at declaration time.** In particular, there is no notion of default values for intermediate variables.

As an aside, we claim that intermediate variables are not fundamental to the language, but rather a feature to enable programmer productivity. Specifically, we claim that for any program containing intermediate variables, there is a functionally equivalent program **without** any intermediate variables. We design the language such that this is the case.

#### Output Variables
Outputs of the PE are declared explicitly as output variables. All output variables carry the nominal/quantitative qualifier, and this qualifier has the same declaration semantics as for inputs (i.e. for nominal output variables, all possible variables must be supplied, and for quantitative output variables, a bit-width must be specified). The nominal/quantitative qualifier must be provided at declaration time. The dynamic/config qualifier does not apply to output variables. After declaration, outputs have identical semantics to intermediate variables. An output is not allowed to be *dangling* (i.e. unassigned); each output variable must be assigned to at least once every virtual cycle. However, output variables do not require an assignment upon declaration (in contrast to intermediate variables, which **do** impose such a requirement).

** Any RTL implementation or derived functional model must have a one-to-one mapping between output variables and module and function outputs, respectively.** 

** A note on output variables: ** Semantically, output variables are not different than intermediate variables. We include this distinction because hardware designers are used to thinking in terms of modules which have outputs. Also, this distinction (along with input variables) allows for a well-defined interface for both derived functional models and RTL implementations. Without output variables, there is no general notion of the surface area or interface of the PE being specified.

#### Stateful Variables
To capture the state of PE's, the language contains stateful variables. The salient characteristics of stateful variables are as follows:
  - For a given stateful variable, all appearances of that stateful variable on the right side of an assignment statement produce the same value.
  - For a given stateful variable, the last executed assignment is the only one that affects the value of the variable.

See [Programming Model](#programming-model) for more details on the semantics of stateful variables. Stateful variables can further be categorized into 3 types:
##### Nominal Registers
Nominal registers are mainly used to capture FSM state. Similar to nominal inputs, nominal registers require that the set of possible values be supplied at declaration time. The same restrictions on nominal inputs apply to nominal registers: they can only be used in `Equals` and `NotEquals` operations and `switch-case` statements. Furthermore, they can only be assigned to with values from the relevant set of possible values (i.e. the set supplied at declaration time).

##### Quantitative Register Files
Quantitative register files are analogous to standard register files. A quantitative register file can be considered a collection of `m` quantitative registers. Similar to other quantitative variables, quantitative registers can be used in all supported operations. Quantitative register files themselves only support the `[]` operator. All quantitative registers in a single quantitative register file are assumed to be the of the same type (i.e. have the same bit-width `n`). Both `n` and `m` (the width and height of the register file, respectively) must be supplied at declaration time. All quantitative registers in a quantitative register file are assumed to produce a value of zero on the first virtual cycle.

##### Memory
Within the language, memory variables are semantically equivalent to quantitative register files. This distinction exists only as a "hint" to RTL generators that such components are to live "off-chip".

### Declarations
All variables must be declared before being used in an assignment or expression (besides compound declaration-assignments), and each variable can only be declared once. Each type of variable has its own rules regarding declaration. Though listed above, we repeat the most important ones here:
  - When declaring input variables, both the dynamic/configuration and nominal/quantitative qualifiers must be specified.
  - When declaring output variables, the nominal/quantitative qualifier must be supplied.
  - When declaring nominal input/output/register variables, the set of possible values must be supplied. Note that any abstract finite set suffices here (containing any underlying types).
  - When declaring quantitative input/output variables, the bit-width must be supplied.
  - When declaring intermediate variables, no qualifiers can be supplied. Instead an initialization expression must be supplied. The nominal/quantitative qualifier is inferred from this expression.
  - When declaring quantitative register files and memory variables, both the bit-width and size must be specified.

### Literals
There are only 2 types of literals: "enum" values that come from the sets supplied to nominal variables, and constant bit-vectors. See [Type System](#type-system) for more details.

### Assignment
Assignment can be used to set the value of variables. All assignments are of the form `Assign(Variable, Expression)`. We refer to the first argument as the *left side* of an assignment, and the second argument as the *right side*. See [Expressions](#expressions) for more details about the semantics of expressions. Similar to declaration, each variable type imposes its own rules for assignment. Though listed above, we repeat the most important ones here:
  - Input variables can not be appear on the left side of assignments; however, they can appear on the right side of assignments.
  - Intermediate/Output variables can appear on the left or right side of assignments. However, the same intermediate/output variable can not appear on both the left and right side of a single assignment.
  - Intermediate/Output variables can appear on the left side of an assignment of multiple assignments. The value produced by the intermediate/output variable maybe different in different portions of the program in that case.
  - If a nominal output/register variable appears on the left side of an assignment, then only expressions which produce values in the possible-value set for that variable can appear on the right side.
  - Quantitative register files and memory variables can not appear in the left side of assignments.
  - If the same nominal register/quantitative register (register, not register file) appears on the left side of multiple assignments, then only the last executed one will take effect.

### Expressions
We derive most of the expression semantics from python expression semantics, as well as the semantics of the `BitVector` class. Most importantly we inherit operator precedence and evaluation order from python. See [Type System](#type-system) for type-based restrictions on operations. Generally, the language is "strictly" typed. Arbitrarily nested expressions are allowed in the language. Beyond standard arithmetic, logic, and comparison operators, the language also includes explicit signed- and zero-extend operations, as well as bit-level splicing operations. (We refer to these operations as cast operations.) Expressions in our language are trees where non-leaf nodes are arithmetic/logic/comparison/cast operations, and leaf nodes are variables and literals.

### Control Flow
The language supports two kinds of control flow constructs:

#### If
If statements in the language have standard `if-else` semantics from other langauges. In particular, they are triples of the form `(ConditionExpr, IfBody, ElseBody)`. `ConditionExpr` is any expression which produces a 1-bit value (see [Type System](#type-system) for more details).

#### Switch-Case
Switch-Case statements in the language have standard `switch-case` semantics from other languages. In particular they are triples of the form `(SwitchExpr, CaseMap)` where `SwitchExpr` is any valid exprssion in the language, and `CaseMap` is a map from values to case bodies.

## Type System
There are 2 fundamental types in the language: enumerated types and bit-vectors. Enumerated types are parameterized by the set of possible values a variable of that type can assume (similar to `enum` types in C/C++). Bit-vectors are parameterized by a bit-width. Almost all variables are subtypes of these two high-level types - see [Quantitative Register Files and Memory Variables](#quantitative-register-files-and-memory-variables). The language is strictly typed in that type-checks are performed at compile time and implicit conversions are not allowed. The type-system implies the following specific rules (many of these have been mentioned above):
  - Enumerated types only support the `Equals` and `NotEquals` operations. Also, they can only be assigned values from the relevant set of possible values.
  - Bit-vectors support all operations.
  - Unless otherwise noted, all operations which take in multiple bit-vectors require that all bit-vector arguments have the same bit-width. For example, a 4-bit bit-vector can not be added to a 2-bit bit-vector. The cast operations exist to support such use cases.

Note that there is no boolean type. Any operation which would normally require a boolean value will instead require a 1-bit bit-vector. `If` statements are the prevelant example of this. All comparison operations return 1-bit bit vectors.

### Quantitative Register Files and Memory Variables
Quantitative Register Files and Memory Variables are actually their own types that are neither subtypes of enumerated types nor bit-vectors. Instead, they emulate a collection of bit-vectors. They **only** support the `[]` operation, which returns a quantitative variable type (i.e. a bit-vector subtype).

## Programming Model
The programming model in this language most closely resembles an RTL langauge, but there are several important differences. The way that it is most like RTL, is in how variables are declared, used and assigned. The important distinctions arise in how we constrain the program.

### Virtual Cycle
The most important concept in the programming model is that of the **virtual cycle**. A virtual cycle is defined as a uniform time period in which all perscriped operations take place atomically. In this way, each program corresponds to a large FSM. The state is collectively described by all stateful variables. Dynamic input variables are FSM inputs, while configuration input variables are meta-parameters of the FSM (i.e. each set of configuration values correspond to a different FSM). Program outputs are FSM outputs. The program statements (after input/output/stateful variable declaration) describe the state transitions of the FSM. One virtual cycle corresponds to one "step" or state transition of the FSM (which incorporates a set of inputs).

The most important aspect of a virtual cycle is that the same value is "read" from stateful components for the entirety of a virtual cycle, and a "write" to a stateful component does not take place until the end of the virtual cycle. So stateful components change exactly once at the end of each virtual cycle.

### Analogy to RTL
If we were to cast the programming model to an RTL description, it would look as follows: first we would declare all inputs, outputs, intermediate variables as wires (as well as include inputs and outputs in a sensitivity list). All stateful variables would be declared as registers (or collections of registers). Then *all logic* would fit in a big `always @(posedge clk)` block, with all register assignments being **non-blocking**. A cycle of this `clk` corresponds to a virtual cycle in our language. This description matches almost exactly to our programming model. The only difference is that in our language intermediate values can take on multiple values throughout a virtual cycle, where as in an RTL language, only the last of a series of continuous assignments of a wire takes effect.

### Combinational vs Sequential Logic
Our language does not explictly differentiate between sequential and combinational logic. Instead, the nature of the logic is inferred from the variables involved. In fact, the only "sequential" logic occurs when a stateful variable is on the left side of an assignment. For example, expressions/assignments involving only input/output/intermediate variables is purely sequential. The appearance of stateful variables on only the right side of an assignment is also considered combinational.

### Combinational Loops
** TODO: what to say here?? **
