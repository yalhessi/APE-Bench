"""
Prompts for semantic annotation of Lean declarations (per file).

The user prompt lists target declarations as list entries with signatures.
The model returns semantic explanations via submit_result tool.
"""

ANNOTATION_USER_PROMPT = """<objective>
Annotate Lean declarations with **natural language explanations** of their mathematical meaning. Transform technical Lean syntax into SELF-CONTAINED mathematical statements that capture the actual content, not the implementation details. Each annotation must be understandable without reference to Lean syntax or programming concepts.
</objective>

<context>
You are working on a specific Mathlib commit. Annotate ONLY the provided declarations.
</context>{file_content_section}

<execution_flow>
**Submission Process:**
Submit annotations using submit_result. Failed submissions will return:
- Specific error message
- Brief guidance on how to fix

Common issues: missing fields, invalid ids, poor formatting.
Read errors and adjust submissions accordingly.
</execution_flow>

<CRITICAL_PARALLELISM_REQUIREMENT>
**YOU MUST SUBMIT ALL ANNOTATIONS IN ONE RESPONSE**
- Use MULTIPLE submit_result calls in PARALLEL
- DO NOT submit declarations one by one
- DO NOT wait between submissions
- Submit all annotations simultaneously
- Example: submit_result(...) for decl 1, submit_result(...) for decl 2, submit_result(...) for decl 3, etc. ALL IN ONE RESPONSE

**IMPORTANT: CONTEXT MANAGEMENT**
- File content is displayed based on declaration ranges and may be truncated
- If you need additional context (imports, related definitions, broader mathematical context), use file reading tools
- Only read what you actually need - avoid importing excessive context
- Focus on understanding the mathematical meaning within the provided ranges first
</CRITICAL_PARALLELISM_REQUIREMENT>

<critical_requirements>
**THREE-PART MATHEMATICAL ANNOTATION**

For **LABEL**:
- A SHORT descriptive title (3-8 words)
- Captures the main concept or purpose
- Uses standard mathematical terminology
- Think of it as a section heading or index entry

For **SEMANTIC_STATEMENT**:
- Write ONE self-contained sentence that fully explains the mathematical meaning
- Include the essential mathematical context without being verbose
- Use standard mathematical terminology, NOT Lean syntax
- Make each concept clear through natural phrasing, not lengthy explanations
- The sentence must be complete and understandable on its own

For **KEYWORDS**:
- List searchable mathematical terms independently
- Include specific objects, general concepts, and applications
- Focus on what mathematicians would search for
- Cover different levels of mathematical abstraction

<writing_style_guide>
**LABEL EXAMPLES**:
- GOOD: "Translation-equivariant maps"
- GOOD: "Prime divisibility property"
- GOOD: "Continuous function spaces"
- BAD: "AddConstMap structure"
- BAD: "Theorem about primes"

**COMPLETE and EXPLANATORY SEMANTIC STATEMENTS**:
BAD semantic_statement: "An AddConstMap from G to H with constants a and b is a function f : G → H such that f(x + a) = f(x) + b"
GOOD semantic_statement: "A function between additive groups that exhibits translation equivariance: shifting the input by a fixed constant 'a' causes the output to shift by a corresponding constant 'b', establishing a semiconjugacy between the translation operations on the domain and codomain"
</writing_style_guide>

**AVOID THESE PATTERNS**:
- "This theorem/lemma/definition states that..."
- "A type/class/structure that..."
- Using Lean syntax like "f : G → H" or type annotations
- Meta-descriptions about what the code does
- Overly technical jargon when simpler terms exist
</critical_requirements>

<BATCH_PROCESSING_STRATEGY>
**MANDATORY PARALLEL SUBMISSION**:
1. Read ALL declarations first
2. Formulate ALL annotations mentally
3. Submit ALL annotations AT ONCE using multiple submit_result calls
4. DO NOT process declarations sequentially
5. Your response should contain MULTIPLE tool calls, not just one

**EXAMPLE OF CORRECT BEHAVIOR**:
If there are 10 declarations, your response should have:
- submit_result(declaration_id="1", label="...", semantic_statement="...", keywords="...")
- submit_result(declaration_id="2", label="...", semantic_statement="...", keywords="...")
- submit_result(declaration_id="3", label="...", semantic_statement="...", keywords="...")
- ... and so on, ALL IN THE SAME RESPONSE
</BATCH_PROCESSING_STRATEGY>

<DECLARATIONS_FOR_ANNOTATION>
{declarations_list}
</DECLARATIONS_FOR_ANNOTATION>

**IMPORTANT NOTE ON DECLARATIONS:**
- Some declarations (particularly instances) may have an empty "name" field
- You MUST still annotate these declarations - use the "kind" field and code content to understand what they declare
- For instance declarations without names, focus on what type class instance is being provided and for which types
- All declarations in the list above MUST be annotated, regardless of whether they have a name

**REMINDER: Submit ALL annotations NOW in PARALLEL. Do not submit them one by one.**
"""


