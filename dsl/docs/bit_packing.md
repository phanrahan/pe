# Bit Packing Notes

The issue we wish to address is follows: we want to decouple the semantic and functional representation of PE inputs from the mechanisms used to encode them in an implementation. To make this concrete, say we have an input `op` to our processor. The semantics of `op` are such that it can take on exactly one of several values, say `[add, sub, and, or, xor]`. We argue that from the programmers perspective, this is the only information that needs to be provided to derive a functional model. Furthermore, we argue that it is an *implementation decision* how to represent `op` as a series of bits, as well as the mapping from the bit-level representations of `op` to the values it can take on -- this is outside of the scope of a PE specification. That is, we only want the programmer to specify that `op` can be one of `[add, sub, and, or, xor]` **not** that `op = 0011` means `or`. There are several reasons for this; most importantly, it allows an implementer a wide range of options, and allows for low-level optimizations without affecting the functional model.

Along these lines, there is another paradigm for decoupling these two things. Imagine that we want an input to the PE called `instruction`, and we want that this input contains the following sub-fields: `[op, src0, src1, dst, imm]`. That is we want to dynamically be able to access the field `instruction.op` etc. It may very well be the case that the usage of these sub-fields is non-overlapping, e.g. any time we use `instruction.imm` we will not access `instruction.src1`. The programmer should have the flexibility of using whichever sub-fields are necessary, without having to think of the repurcussions on the bit-level encoding of `instruction`. Either a manual implementer or compiler should have the room to perform optimizations that reduce the footprint of `instruction` (likely by instrospecting and analyzing the sub-field usage patterns) while **not changing the functional model**.

## Proposal

We propose a methodology with the following goals in mind:
- Clearly decouple the meaning of inputs in the functional model from their bit-level representations
- Allow implementations to choose a specific bit-level representation from a space of valid representations. I.e. allow implementations to choose a bit-level implementation while not violating the functional model.
- Allow packing several sub-fields into a larger input and accessing those sub-fields dynamically.
- (*Stretch Goal*) Allow the programmer to input any knowledge they may have to guide a compiler/automatically derived implementation. Basically, we want to allow the programmer to provide "hints" that could lead to an optimized implementation (or so that the implementation matches a pre-existing spec).

A non-goal of this document is a methodology for automatically computing optimized bit-level representations. We leave that for future work, but argue that the decoupling presented in this document, along with the ability for the programmer to provide "hints" is a beneficial abstraction.

In our other document we have already explained the distinction between `nominal` and `quantitative` inputs. The former mirror `enum` types in C/C++, while the latter are exactly `n`-bit bit-vectors, where `n` is specified ahead of time. Furthermore, nominal inputs can only be used in comparisons, not in general arithmetic/logic. With this in place, we have already decoupled semantics from implementation for individual inputs. What remains is supporting packing of these fields into a single input. For this we propose simple struct-like semantics, where in an input variable can be declared using a collection of other input variables, ala

    instruction = Input({
        "op" : NominalInput(values=['add', 'sub', 'and', 'or', 'xor']),
        "src0" : QuantitativeInput(width=16),
        "src1" : QuantitativeInput(width=16),
        "imm" : QuantitativeInput(width=10)
    })
    ...
    switch (instruction.op) {
      ...
    }
    ...

This methodology is simple and explicit, yet is flexible enough to capture all use cases. Most importantly, it allows combining arbitary types of inputs. The only restriction we impose is that all sub-fields are either dynamic or configuration (i.e. they can not be mixed within a struct).
