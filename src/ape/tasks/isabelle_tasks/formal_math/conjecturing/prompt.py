"""Prompt template for Isabelle conjecturing tasks."""

ISABELLE_CONJECTURING_USER_PROMPT = """<objective>
Produce an Isabelle conjecture that is accepted by Isabelle in the provided context and contains every required symbol literally.

Required symbols:
{symbols_block}
</objective>

{task_description_block}<context>
Validation session: `{session_name}`

Default imports for snippet submissions:
```isabelle
imports {imports_line}
```

Draft file:
```text
{draft_file_path}
```
{theory_prelude_block}</context>

<validation>
- You may submit either a theorem/lemma declaration snippet or a full `.thy` theory.
- `sorry` is allowed for this task. Validation checks that Isabelle accepts the conjecture in context.
- Every required symbol must appear literally in the submitted conjecture.
- Use `{validate_tool_name}` to test candidates before calling `{submit_tool_name}`.
</validation>

<submission_strategy>
**CRITICAL: YOU MUST CALL THE `{submit_tool_name}` TOOL TO SUBMIT YOUR FINAL RESULT**
- Plain text responses do not count as submission.
- Prefer a file-first workflow in scratch workspace.
- Draft in `{draft_file_path}` and iterate with `{validate_tool_name}`.
</submission_strategy>"""
