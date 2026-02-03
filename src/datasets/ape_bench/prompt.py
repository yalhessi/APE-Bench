"""
APE Bench Instruction Generation Prompt Templates

Generate formalization task instructions from code modifications.
Generalized for any formal language project (Lean, Isabelle, Coq, etc.).
"""

INSTRUCTION_GENERATION_USER_PROMPT = """<objective>
Analyze a file modification in a formal language project to create a formalization task that captures the core objectives, and provide a detailed guide on how to accomplish these objectives.
</objective>

<context>
You are examining a complete file modification. Your task is to:
1. Assess if the modification is substantial enough to warrant a task
2. If substantial, identify the core contributions and express them as clear objectives
3. Provide a detailed implementation guide - instructional content explaining how to accomplish these objectives

CRITICAL: Stay within the scope of what the modification actually does.
</context>

<provided_file_contents>
{file_content_section}
</provided_file_contents>

<execution_flow>
Submit your analysis using submit_result. The system will either accept or provide error feedback for resubmission.
</execution_flow>

<quality_assessment>
**Reject if the modification only involves:**
- Formatting, whitespace, or comment-only changes
- Variable renaming without semantic impact
- Trivial syntax updates with no meaningful significance

**Accept if the modification involves:**
- Changes to proofs or proof techniques
- Clarification of logical dependencies or assumptions
- Generalization or specialization of results
- Structural improvements to theories or modules
- Bug fixes affecting correctness

**For rejected modifications, provide:**
- title, difficulty: "very easy", task_nature: "superficial", reject_reason

**For accepted modifications, provide all fields including implementation_approach.**
</quality_assessment>

<task_formulation>
**Title** (5-20 words): State what the task achieves

**Context**: Brief description of the situation being addressed

**Objectives**: Specific, concrete goals to achieve

**Implementation Approach**: A step-by-step instructional guide for accomplishing the objectives:
- Analysis: Identify what challenges must be addressed and what techniques are applicable
- Strategy: Outline the approach - what to define first, what dependencies exist, what proof techniques to use
- Steps: Provide concrete implementation steps explaining exactly how to write the code

The implementation approach must be INSTRUCTIONAL, not descriptive. A reader following the objectives and implementation approach should understand exactly what to do and how to write the code, without needing to see the actual changes.

**Significance**: Explain the specific benefit of achieving these objectives

**Classification**: Based on the actual work involved
</task_formulation>

<classification_schema>
**task_category**:
- `feature`: New content or functionality
- `refactor`: Reorganization for better structure
- `bug fix`: Corrections to errors
- `chore`: Routine updates
- `testing`: Test cases
- `documentation`: Comments only
- `formatting`: Style changes

**formalization_aspect**:
- `new_content`: Formalizing previously unformalized content
- `proof_technique`: New or improved proof strategies
- `abstraction`: Generalization of existing results
- `structural_design`: Organization of theories or modules
- `technical_implementation`: Performance optimizations

**difficulty**: very easy / easy / medium / hard / very hard

**task_nature**: substantial / superficial
</classification_schema>

<EXAMPLE_SUBSTANTIAL>
Title: "Establish the theory of uniformly continuous functions on metric spaces"

Context: The codebase has extensive theory for continuous functions, but uniform continuity on metric spaces lacks comprehensive formalization.

Objectives:
- Define uniform continuity for functions between metric spaces and establish basic properties
- Prove that uniformly continuous functions preserve Cauchy sequences
- Establish that continuous functions on compact metric spaces are uniformly continuous
- Prove that uniform continuity is preserved under uniform limits
- Demonstrate the relationship between Lipschitz continuity and uniform continuity

Implementation Approach:
- Analysis: Uniform continuity differs from pointwise continuity in that epsilon must be chosen independently of the point. The key challenges are: (1) formulating the definition correctly, (2) proving Cauchy preservation requires relating the uniform delta to sequence convergence, (3) the compactness result needs the Heine-Cantor approach.
- Strategy: Start with the epsilon-delta definition of UniformlyContinuous. Build up from basic properties to preservation theorems. Use the standard epsilon/3 argument pattern for composition and limit proofs.
- Steps:
  1. Define `UniformlyContinuous f` as: for all epsilon > 0, there exists delta > 0 such that for ALL x, y, if d(x,y) < delta then d(f(x), f(y)) < epsilon. Note the universal quantifier on x,y comes AFTER the existential on delta.
  2. For Cauchy preservation: given Cauchy sequence (x_n) and epsilon > 0, obtain delta from uniform continuity, then use that (x_n) is Cauchy to find N such that d(x_m, x_n) < delta for m,n >= N, which gives d(f(x_m), f(x_n)) < epsilon.
  3. For the Heine-Cantor result: given continuous f on compact K and epsilon > 0, for each x in K get delta_x from continuity at x. Cover K with balls B(x, delta_x/2). Extract finite subcover. Take delta = min of the finite deltas divided by 2. Verify this works.
  4. For Lipschitz implication: if |f(x) - f(y)| <= L|x-y|, set delta = epsilon/L.

Significance: Enables formalization of completeness theorems and uniform convergence in function spaces.

task_category: feature
formalization_aspect: new_content
difficulty: medium
task_nature: substantial
</EXAMPLE_SUBSTANTIAL>

<REJECTION_EXAMPLE>
title: "Update import formatting in module"
difficulty: very easy
task_nature: superficial
reject_reason: This modification only updates import statements and formatting without any meaningful impact on functionality or theory.
</REJECTION_EXAMPLE>
"""
