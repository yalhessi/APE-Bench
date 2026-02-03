"""
Arithmetic Task - Minimal Task Contract Example.

This example demonstrates how to create a custom task using the APE task contract.
The task asks the model to compute a simple arithmetic expression and verify the result.
"""

from typing import Optional
from pydantic import Field

from ape.tasks.base import BaseTask, BaseTaskData, BaseTaskConfig, BaseTaskResult, EvaluationResult, register_task


class ArithmeticTaskData(BaseTaskData):
    """Data model for arithmetic tasks."""

    expression: str = Field(..., description="Arithmetic expression to evaluate (e.g., '123 + 456')")
    expected_result: float = Field(..., description="Expected result of the expression")


class ArithmeticTask(BaseTask):
    """Task for evaluating arithmetic expressions.

    The agent receives an arithmetic expression and must compute the correct result.
    The agent can use Python (via bash tool) to perform calculations.
    """

    # Required class variables
    task_type = "arithmetic"
    data_class = ArithmeticTaskData
    task_config_class = BaseTaskConfig
    task_result_class = BaseTaskResult

    async def create_user_prompt(self) -> str:
        """Create the prompt for the agent.

        Returns:
            Prompt asking the agent to compute the arithmetic expression.
        """
        return f"""Please compute the following arithmetic expression and submit the result:

Expression: {self.data.expression}

You can use Python to calculate it. When you have the answer, use the submit_result tool to submit your answer as a number.

Example:
- If the expression is "10 + 5", you should submit 15.0
- If the expression is "100 / 4", you should submit 25.0
"""

    async def evaluate(self, submission: str) -> Optional[EvaluationResult]:
        """Evaluate the submitted result.

        Args:
            submission: The result submitted by the agent (as a string).

        Returns:
            EvaluationResult indicating success/failure and score.
        """
        try:
            # Parse the submitted result
            submitted_value = float(submission.strip())

            # Check if the result is correct (with small tolerance for floating point)
            tolerance = 1e-6
            is_correct = abs(submitted_value - self.data.expected_result) < tolerance

            if is_correct:
                return EvaluationResult(
                    success=True,
                    score=1.0,
                    message=f"Correct! {self.data.expression} = {submitted_value}"
                )
            else:
                return EvaluationResult(
                    success=False,
                    score=0.0,
                    message=f"Incorrect. Expected {self.data.expected_result}, got {submitted_value}"
                )

        except ValueError:
            # If the submission cannot be parsed as a number
            return EvaluationResult(
                success=False,
                score=0.0,
                message=f"Invalid submission: '{submission}' is not a valid number"
            )


# Register the task type
register_task("arithmetic", ArithmeticTask)
