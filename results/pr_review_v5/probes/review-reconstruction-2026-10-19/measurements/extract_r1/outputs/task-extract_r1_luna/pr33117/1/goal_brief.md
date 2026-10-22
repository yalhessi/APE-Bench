## 1. Kind of contribution
A new mathematical notion, together with new closure results for that notion.

## 2. Capability
Provide a whole-domain notion of meromorphy for functions: a function has the property when it is meromorphic at every point of its domain, corresponding to meromorphy on the entire domain. Supply closure results for negation, addition and subtraction, finite sums, and (for scalar-valued functions) multiplication, division, finite products, and natural- and integer-valued powers. Also supply closure under differentiation and repeated differentiation for functions with complete codomain. The results should cover the mathematical families just listed, without imposing a broader scope not supported by the inputs.

## 3. What must keep working
The existing notions of meromorphy at a point and on a set must retain their meanings. In particular, the whole-domain notion must agree with meromorphy on the universal set. The pointwise operations and derivative results on which the new closure properties build should remain available, and the stated closure properties must apply to their described special cases, including finite sums and products and repeated derivatives.

## 4. Open questions
The inputs do not establish a need for closure under composition, infinite sums or products, or other operations. They do not settle whether the scalar-valued multiplication, division, and power results should extend to broader algebraic settings, or whether derivative results can hold with weaker completeness assumptions. Nor do they prescribe how the global notion and its closure results should be packaged as an API.

## 5. Where the requirements come from
The whole-domain capability comes from paragraph 1 of the description, which states the intended mathematical scope. The title (the current value, not verified to be the one at review time) supports that this is a new notion. The change itself adds closure results for the listed arithmetic operations and derivatives, and changes no pre-existing local or set-based results; those facts motivate the preservation requirements and the stated scope of the new results.