"""
Proof Engineering Task Prompts.

Provides prompt templates for proof engineering tasks with tool-driven
deep understanding, focusing on mathematical correctness and engineering quality.
"""

LEAN_PROOF_ENGINEERING_USER_PROMPT = """<objective>
Implement or improve Lean4 code with mathematical rigor and engineering excellence. Your implementation must be thorough, evidence-based, and reach expert-level quality.
</objective>

<SUBMISSION_STRATEGY>
**CRITICAL: YOU MUST CALL THE `{submit_tool_name}` TOOL TO SUBMIT YOUR SOLUTION**
- Simply describing your solution or showing code in your message does NOT count as submission
- You MUST actively invoke the `{submit_tool_name}` tool with your final implementation
- Providing results only in text response is INVALID and will NOT be accepted
</SUBMISSION_STRATEGY>

<task_description>
{task_description}
</task_description>
{original_code_section}
<IMPLEMENTATION_STRATEGY>
{implementation_strategy_content}
</IMPLEMENTATION_STRATEGY>

<TASK_SPECIFIC_RULES>
**Single File Task:** Create/modify ONE self-contained file. Do NOT create helper files.

{file_locations}

</TASK_SPECIFIC_RULES>

<critical_reminders>
- Task description is ABSOLUTE—fulfill all requirements precisely
- **INDEPENDENT IMPLEMENTATION**: Your task is to implement the required functionality independently. Do NOT attempt to use, import, or depend on blocked/inaccessible files in the target workspace. If a file is blocked, it means you must implement that functionality from scratch.
- Only modify what is necessary for the task, concentrating on the stated requirements.
- Preserve unrelated code (especially large sections or existing lemmas) unless the task explicitly calls for broader refactoring.
- If verification fails due to missing dependencies, implement those dependencies yourself rather than trying to access blocked files.
</critical_reminders>"""
