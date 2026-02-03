"""
Theorem Proving Task Prompts.

Provides prompt templates for Lean theorem proving tasks
using tool-driven exploration to construct mathematical proofs.
"""

LEAN_THEOREM_PROVING_USER_PROMPT = """<objective>
Prove the following theorem in Lean4:

```lean
{theorem_statement}
```
</objective>

<SUBMISSION_STRATEGY>
**CRITICAL: YOU MUST CALL THE `{submit_tool_name}` TOOL TO SUBMIT YOUR SOLUTION**
- Simply describing your solution or showing code in your message does NOT count as submission
- You MUST actively invoke the `{submit_tool_name}` tool with your final proof code
- Providing results only in text response is INVALID and will NOT be accepted

**VERY CRITICAL: FILE-FIRST DEVELOPMENT**
- Follow the file-centric workflow as specified in your system prompt
- **CREATE FILES FIRST** in scratch workspace for iterative development
- Work incrementally with automatic verification feedback
- **Call `{submit_tool_name}` tool** when proof is complete and verified

**Direct Submission (Only for Trivial Cases):**
- For simple one-line proofs, you may directly call `{submit_tool_name}` without creating files
- Still MUST use the tool—never just describe the solution in text
</SUBMISSION_STRATEGY>

<standards>
**CRITICAL QUALITY STANDARDS:**
- **NO PLACEHOLDERS**: Never use placeholders like `sorry` and `admit` in final submissions—proofs must be complete
- **EXACT STATEMENT**: Preserve the exact theorem statement as given
</standards>"""
