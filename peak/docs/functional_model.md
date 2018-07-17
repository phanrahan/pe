# Functional Model Notes
**What is a functional model?** A functional model is a description of the input-output + state transition behavior of a processor. That it is, given a current state and a set of inputs, it describes the outputs as well as the new state (similar to a state machine description). For different processors and design tasks, this might have different interpretations, mostly in terms of the level of detail of the model. For example, in some functional models, auxiliary state (e.g. branch predictor state) may be of importance to the designer. For other tasks, this may be deemed implementation details. We argue that for specifying processors, it is most useful to think about functional models at the level of memory, register files, configuration inputs (for spatial architectures) and dynamic inputs. Our language, however, is able to capture a wide range of levels of detail, modulo timing semantics.

## Digital Functional Model

There is another important choice to make when defining a functional model. In our other document we have already explained the distinction between `nominal` and `quantitative` inputs. The former mirror `enum` types in C/C++, while the latter are exactly `n`-bit bit-vectors, where `n` is specified ahead of time. Furthermore, nominal inputs can only be used in comparisons, not in general arithmetic/logic. Of course, in any synthesizable hardware design, there are only `n`-bit bit-vectors. Therefore, any RTL implementation must define a mapping from each enum value to a bit-level representation (either implicitly or explicitly). It could be argued that this mapping is purely an implementation detail and outside of the scope of the functional model. However, we define another entity called a *Digital Functional Model* which essentially layers this mapping on top of a regular functional model. A digital functional model presents an interface in which all entities are bit-vectors.

To make this concrete, we might have the following functional model (here `BV` stands for `BitVector`):

    enum Op { ADD, SUB, AND, OR, XOR }
    
    func Cpu(Op op, BV src0, BV src1, BV dst, BV imm) {
        ...
    }

along with the following digital functional model:

    func CpuDigital(BV op, BV src0, BV src1, BV dst, BV imm) {
        ...
    }

A functional model `a` and digital functional model `b` are *semantically equivalent* if there exists a deterministic mapping `f` from bit-vectors to their respective enum type, such that `a(f(i)) == b(i)` for all set of inputs `i` (where the `i`'s are bit-vectors). Note that `f` can be different for each enum type.

Given a functional model, one way to derive a semantically equivalent digital functional model would be to explicitly define the function `f`, and then call the original functional model:

    func CpuDigital(BV op, BV src0, BV src1, BV dst, BV imm) {
        Op op_as_enum = MapOp(op)
        return Cpu(op_as_enum, src0, src1, dst, imm)
    }

Here, `MapOp` is an explicitly defined function which returns the enum-type value for a given bit-vector. To be clear, one could directly write a digital functional model from scratch. However, we claim it is most useful to construct two orthogonal components: (i) a regular functional model, and (ii) a mapping from bit-vectors to enum-type values. From these two components, we can directly derive a digital functional model.

**A note about outputs:** We excluded any discussion of outputs thus far. The ideas presented thus far extend naturally to outputs. First we require that `f` be invertible; let `f_inv` represent the inverse of `f`. Then we can change the definition of semantic equivalence to `f_inv(a(f(i))) == b(i)`. Finally, we change the derived digital functional model to:

    func CpuDigital(BV op, BV src0, BV src1, BV dst, BV imm) {
        Op op_as_enum = MapOp(op)
        ret = Cpu(op_as_enum, src0, src1, dst, imm)
        return InverseMap(ret)
    }

**A note about invalid values:** We note that in the case that a nominal type does not have exactly `2^n` choices, there are bit-vectors which are *invalid*, or do not map to any enum-type value. Formally, this means that the domain of `f` of restricted. As long as this information is clearly encoded in the definition of `f`, this does not change anything. Most importantly, for semantic equivalence, the equality condition only needs to hold for all inputs `i` which are in the domain of `f`.

## Workflows

Given a processor spec, we argue we should design for the following workflows, where the arrows are automatic generation steps:
- spec --> functional model
- functional model + explicit mapping --> digitial functional model
- spec --> naive explicit mapping
- spec --> optimized explicit mapping

From these base workflows, an important derived workflow is

    spec --> (functional model, optimized digital functional model)

The use of *optimized* here does not refer to anything about an RTL implementation, just the aggregate size of bit-vectors in the interface of a digital functional model. Also, we claim that automatically generating a naive explicit mapping is trivial. We leave automatic generation of an optimized explicit mapping for future work.
