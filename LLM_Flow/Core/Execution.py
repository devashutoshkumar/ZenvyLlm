import subprocess
import tempfile
import os

from Core.Schemas import(
    AgentAction,
    PolicyDescision,
    ExecutionResult
)
from Core.Documents import KnowledgeBase
from Models.Ollama import OllamaModel

class Executor:
    def __init__(self):
        self.llm = OllamaModel()
        self.knowledge = KnowledgeBase()

    def execute(self, action :AgentAction, policy :PolicyDescision) -> ExecutionResult:
        #Policy block
        if policy.effect == "DENY":
            return ExecutionResult(
                success=False,
                output=f"Execution denied: {policy.reason}"
            )

        #LLM action
        if policy.effect == "REQUIRE_APPROVAL":
            return ExecutionResult(
                success=False,
                output=f"Approval required: {policy.reason}"
            )

        #LLM
        if action.action_type == "llm":

            result = self.llm.run(
                model="gemma3:4b",
                prompt=action.description
            )

            return ExecutionResult(
                success=True,
                output=result,
                model_used="gemma3:4b"
            )

        #tool
        if action.action_type == "tool":

        # ----------------------------------------
        # SEARCH KNOWLEDGE
        # ----------------------------------------

            if action.tool == "search_knowledge":
                query = action.action_input.get(
                    "query"
                )

                if not query:

                    return ExecutionResult(
                        success=False,
                        output="No knowledge search query supplied.",
                        tool_used="search_knowledge"
                    )

                results = self.knowledge.search(
                    query
                )

                if not results:

                    return ExecutionResult(
                        success=False,
                        output="No relevant local documents found.",
                        tool_used="search_knowledge"
                    )

                return ExecutionResult(
                    success=True,
                    output=results,
                    tool_used="search_knowledge"
                )

            # ----------------------------------------
            # READ DOCUMENT
            # ----------------------------------------

            if action.tool == "read_document":

                filename = action.action_input.get(
                    "filename"
                )

                if not filename:

                    return ExecutionResult(
                        success=False,
                        output="No filename supplied.",
                        tool_used="read_document"
                    )

                try:

                    contents = self.knowledge.read_document(
                        filename
                    )

                    return ExecutionResult(
                        success=True,
                        output=contents,
                        tool_used="read_document"
                    )

                except Exception as error:

                    return ExecutionResult(
                        success=False,
                        output=str(error),
                        tool_used="read_document"
                    )

            # ----------------------------------------
            # PYTHON
            # ----------------------------------------

            if action.tool == "run_python":

                code = action.action_input.get(
                    "code"
                )

                if not code:

                    return ExecutionResult(
                        success=False,
                        output="No Python code supplied."
                    )

                return self.run_python(
                    code,
                    policy
                )

            #Finish
        if action.action_type == "finish":

            return ExecutionResult(
                success=True,
                output=action.description
            )

        return ExecutionResult(
            success=False,
            output="Unknown action."
        )


    def run_python(self, code :str, policy: PolicyDescision) -> ExecutionResult:
        timeout = policy.constraints.get(
            "timeout",
            30
        )

        temp_file = None

        try:

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8"
            ) as f:

                f.write(code)

                temp_file = f.name

            result = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:

                return ExecutionResult(
                    success=True,
                    output=result.stdout,
                    tool_used="run_python"
                )

            return ExecutionResult(
                success=False,
                output=result.stderr,
                tool_used="run_python"
            )

        except subprocess.TimeoutExpired:

            return ExecutionResult(
                success=False,
                output="Python execution timed out.",
                tool_used="run_python"
            )

        finally:

            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
