from typing import Any, Literal, Optional
from unittest.mock import Base
from pydantic import BaseModel, Field

class TaskState(BaseModel):
    task :str

    context :list[dict[str, Any]] = Field(default_factory=list)

    completed :bool = False

class AgentAction(BaseModel):
    action_type: Literal[
            "llm",
            "tool",
            "finish"
        ]

    description :str

    capabilities :dict[str, float] = Field(default_factory=dict)

    tool :Optional[str] = None

    action_input :dict[str, Any] = Field(default_factory=dict)

    risk :Literal[
            "low",
            "medium",
            "high"
        ] = "low"

class PolicyDescision(BaseModel):
    effect :Literal[
            "ALLOW",
            "ALLOW_WITH_RESTRICTIONS",
            "REQUIRE_APPROVAL",
            "DENY"
        ]
    
    reason :str

    constraints :dict[str, Any] = Field(default_factory=dict)

class ExecutionResult(BaseModel):
    success :bool

    output: Any = None

    model_used :Optional[str] = None
    tool_used :Optional[str] = None

class VerificationResult(BaseModel):
    passed :bool
    reason :str

