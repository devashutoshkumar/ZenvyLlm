from Core.Schemas import (
    AgentAction,
    ExecutionResult,
    VerificationResult
)

from Models.Ollama import OllamaModel


class Verifier:

    def __init__(self):
        self.llm = OllamaModel()
        self.model = "gemma3:4b"

    def verify(
        self,
        original_task: str,
        action: AgentAction,
        result: ExecutionResult
    ) -> VerificationResult:

        # If execution itself failed, verification fails immediately.
        if not result.success:
            return VerificationResult(
                passed=False,
                reason=f"Execution failed: {result.output}"
            )

        prompt = f"""
You are the verification engine of a completely local industrial AI agent.

You are verifying ONE STEP of a multi-step workflow.

Your job is to determine whether the EXECUTION RESULT
successfully completed the CURRENT ACTION.

Do NOT require this single action to satisfy the entire user task.

The original task is provided only for context.

ORIGINAL USER TASK:
{original_task}

CURRENT ACTION:
{action.description}

ACTION TYPE:
{action.action_type}

TOOL:
{action.tool}

EXECUTION SUCCESS:
{result.success}

EXECUTION RESULT:
{result.output}

Verification rules:

1. Verify whether the CURRENT ACTION was successfully completed.
2. A search action passes if it retrieves relevant and useful information.
3. A read_document action passes if the requested document was successfully read.
4. A run_python action passes if the code executed correctly and produced a relevant result.
5. An LLM action passes if it produced a reasonable result for the requested reasoning step.
6. Do NOT fail because additional steps are still required.
7. Do NOT expect a retrieval step to produce the user's final answer.
8. Fail only if:
   - execution failed,
   - the result is irrelevant,
   - the requested operation was not performed,
   - or the result is clearly unusable.
9. Be pragmatic. Useful partial progress is a successful agent step.

Return ONLY:

PASS|short reason

or

FAIL|short reason
"""

        response = self.llm.run(
            self.model,
            prompt
        ).strip()

        if response.upper().startswith("PASS"):
            reason = response.split("|", 1)[1] if "|" in response else response

            return VerificationResult(
                passed=True,
                reason=reason.strip()
            )

        reason = response.split("|", 1)[1] if "|" in response else response

        return VerificationResult(
            passed=False,
            reason=reason.strip()
        )