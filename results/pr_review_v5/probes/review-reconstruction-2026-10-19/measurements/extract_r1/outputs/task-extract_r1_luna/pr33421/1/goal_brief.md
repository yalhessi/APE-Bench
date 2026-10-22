# Goal brief

## 1. Kind of contribution
New results; generalization of existing results; API reorganization; maintenance of imports and variable scopes.

## 2. Capability
In the existing ordered setting with an integer floor, give useful mathematical characterizations of rounding to the nearest integer, with ties assigned to the larger integer. Express the rounded value using the floor of twice the input; away from fractional part one-half, express it using the ceiling of twice the input; and relate the excluded half-fraction condition to twice the input being an odd integer. In the field setting, characterize the inputs rounded to any given integer by a half-unit interval. Supply the corresponding integer-translation identities for ceilings, including natural-number shifts.

For the existing floor, ceiling, and fractional-part operations, provide continuity results in the applicable order-topological ring settings: integer-valued floor and ceiling are continuous on their constant-value unit intervals and locally away from integer inputs; fractional part remains continuous on the stated intervals and away from integers. Give the one-sided limiting behavior of rounding (from the right at every input and from the left with the corresponding half-ceiling value), and continuity of rounding away from its half-fraction boundary. Also establish continuity after composing the fractional-part map with a function continuous on the interval relevant to that map and having equal endpoint values.

## 3. What must keep working
Preserve the existing nearest-integer behavior, including the values at positive and negative one-half, integer translation, the half-unit error bound, and the existing zero-value interval characterization. Existing floor, ceiling, and fractional-part results and their mathematical meanings must remain usable while integer-valued continuity is made available.

## 4. Open questions
The inputs do not establish whether the alternate floor-based characterization should remain only a theorem or become the implementation of rounding. They also do not settle whether the new continuity API should be stated more generally than the order-topological ring settings used here, or whether further points/domains should be covered.

## 5. Where the requirements come from
The description is absent: the PR had no description at review start. The current title, not verified to be the title at review time, identifies the topic as a review of the rounding API. The rounding formulas, interval criterion, half-fraction exception, and ceiling-shift identities come from additions and proof changes in `Mathlib/Algebra/Order/Floor/Ring.lean` and `Mathlib/Algebra/Order/Round.lean`. The continuity, one-sided-limit, and fractional-part composition requirements come from the changes in `Mathlib/Topology/Algebra/Order/Floor.lean`. Import and scope maintenance comes from the import and section changes across the files listed in the packet.
