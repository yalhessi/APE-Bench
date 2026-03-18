"""Prompt template for Lean code generation tasks."""

LEAN_CODE_GENERATION_USER_PROMPT = """<objective>
Translate the provided Python program into Lean 4 so it remains executable, preserves behavior, and is ready for downstream proof work.
</objective>

<SUBMISSION_STRATEGY>
**CRITICAL: YOU MUST CALL THE `{submit_tool_name}` TOOL TO SUBMIT YOUR SOLUTION**
- Simply describing your solution or showing code in your message does NOT count as submission
- You MUST actively invoke the `{submit_tool_name}` tool with your final Lean code
- Providing results only in text response is INVALID and will NOT be accepted

**VERY CRITICAL: FILE-FIRST DEVELOPMENT**
- Put your Lean translation in a file under `scratch/`
- Use Lean verification iteratively while you develop
- Call `{submit_tool_name}` only when the translation compiles cleanly
</SUBMISSION_STRATEGY>

<task_description>
{task_description}
</task_description>

<translation_contract>
{translation_contract}
</translation_contract>

<source_program>
```python
{source_program}
```
</source_program>

<TASK_SPECIFIC_RULES>
- Single file task: create one self-contained Lean file
- Input file: `scratch/{source_file}` (read-only)
- Suggested output file: `scratch/{target_file}`
- Translate the entire visible Python program, not just the benchmark entry point
- Preserve the benchmark entry point name `{entry_point}`
- You may adjust the Lean signature slightly when needed, as long as the entry point remains callable for the encoded benchmark inputs
- Hidden HumanEval-derived behavior checks will run after compilation, so do not hardcode example outputs
</TASK_SPECIFIC_RULES>

<critical_reminders>
- Keep the translation executable, not just a specification
- Match the requested representation contract exactly, especially for container types
- Use proof-friendly, total Lean definitions when possible
- Do not depend on hidden benchmark tests; only the provided source program is visible
</critical_reminders>"""
