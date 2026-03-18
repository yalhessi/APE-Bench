"""Prompt template for Lean spec generation tasks."""

LEAN_SPEC_GENERATION_USER_PROMPT = """<objective>
Formalize the provided HumanEval prompt into executable Lean 4. The canonical Python solution is intentionally hidden; use only the visible prompt, signature, and examples to derive the Lean implementation.
</objective>

<SUBMISSION_STRATEGY>
**CRITICAL: YOU MUST CALL THE `{submit_tool_name}` TOOL TO SUBMIT YOUR SOLUTION**
- Simply describing your solution or showing code in your message does NOT count as submission
- You MUST actively invoke the `{submit_tool_name}` tool with your final Lean code
- Providing results only in text response is INVALID and will NOT be accepted

**VERY CRITICAL: FILE-FIRST DEVELOPMENT**
- Put your Lean formalization in a file under `scratch/`
- Use Lean verification iteratively while you develop
- Call `{submit_tool_name}` only when the formalization compiles cleanly
</SUBMISSION_STRATEGY>

<task_description>
{task_description}
</task_description>

<translation_contract>
{translation_contract}
</translation_contract>

<visible_prompt>
```python
{source_prompt}
```
</visible_prompt>

<TASK_SPECIFIC_RULES>
- Single file task: create one self-contained Lean file
- Input file: `scratch/{source_file}` (read-only)
- Suggested output file: `scratch/{target_file}`
- The canonical Python implementation is NOT provided
- Use the HumanEval prompt, docstring, and examples as the visible specification
- Preserve the benchmark entry point name `{entry_point}`
- You may adapt the Lean signature slightly when needed, as long as the entry point remains callable for the encoded benchmark inputs
- Hidden HumanEval-derived behavior checks will run after compilation, so do not hardcode example outputs
</TASK_SPECIFIC_RULES>

<critical_reminders>
- Implement executable Lean behavior, not just a theorem statement or partial specification
- Translate the whole visible prompt into a proof-friendly Lean program structure
- Match the requested representation contract exactly, especially for container types
- Do not depend on hidden benchmark tests or assume the canonical solution
</critical_reminders>"""

