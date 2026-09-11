import json

from .Schemas import TaskState, AgentAction
from Models.Ollama import OllamaModel


class Manager:

    def __init__(self):
        self.llm = OllamaModel()
        self.model = "gemma3:4b"

    def next_action(self, state: TaskState) -> AgentAction:

        prompt = f"""
You are the manager of a completely local industrial AI agent.

Your job is to decide ONLY the NEXT action required
to complete the user's task.

Possible action types:

- llm
- tool
- finish

Available tools:

- search_knowledge
- read_document
- run_python

Tool meanings:

search_knowledge:
Search local industrial/refinery documents when information
must be found.

read_document:
Read a specific local document when its filename is known.

run_python:
Execute Python for calculations or data processing.

Available capabilities:

- reasoning
- vision
- ocr
- coding
- document_search

IMPORTANT:

"action_type" MUST be ONLY:

"llm"
"tool"
"finish"

Tool names NEVER go inside action_type.

CORRECT:

{{
    "action_type": "tool",
    "description": "Search refinery documents for maintenance failures.",
    "capabilities": {{
        "document_search": 0.9
    }},
    "tool": "search_knowledge",
    "action_input": {{
        "query": "refinery failures inadequate maintenance"
    }},
    "risk": "low"
}}

WRONG:

{{
    "action_type": "search_knowledge"
}}

For normal reasoning:

{{
    "action_type": "llm",
    "description": "Interpret the available information.",
    "capabilities": {{
        "reasoning": 0.9
    }},
    "tool": null,
    "action_input": {{}},
    "risk": "low"
}}

If the task is complete:

{{
    "action_type": "finish",
    "description": "Task completed.",
    "capabilities": {{}},
    "tool": null,
    "action_input": {{}},
    "risk": "low"
}}

Rules:

1. Return valid JSON only.
2. Decide only ONE next action.
3. Look at PREVIOUS RESULTS before choosing an action.
4. Do not repeat a successful previous action.
5. Do not invent document information.
6. Use search_knowledge if refinery information must be retrieved.
7. Use run_python for accurate calculations.
8. Use llm for reasoning over information already retrieved.
9. Use finish only when the complete user task is satisfied.
10. Everything runs locally.

USER TASK:

{state.task}

PREVIOUS RESULTS:

{json.dumps(state.context, indent=2)}
"""

        response = self.llm.run(
            self.model,
            prompt
        )

        response = (
            response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        print("\nRAW MANAGER RESPONSE:")
        print(response)

        data = json.loads(response)

        # Small safety correction only.
        # Do NOT build a big normalization system yet.
        known_tools = {
            "search_knowledge",
            "read_document",
            "run_python"
        }

        if data.get("action_type") in known_tools:
            data["tool"] = data["action_type"]
            data["action_type"] = "tool"

        return AgentAction(**data)