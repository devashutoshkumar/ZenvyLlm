from Core.Schemas import AgentAction, PolicyDescision

class PolicyEngine:

    def evaluate(self, action :AgentAction) -> PolicyDescision:
        
        #Normal local LLM stuff
        if action.action_type == "llm":
            return PolicyDescision(
                effect="ALLOW",
                reason="LOCAL LLM inference is allowed.",
                constraints={}
            )

        #Finished task stuff
        if action.action_type == "finish":
            return PolicyDescision(
                effect="ALLOW",
                reason="Task may finish.",
                constraints={}
            )

        #Tool execution
        if action.action_type == "tool":

            if action.tool == "search_knowledge":
                return PolicyDescision(
                    effect="ALLOW",
                    reason="Local knowledge search is allowed.",
                    constraints={
                        "local_only": True    
                    }
                )

            if action.tool == "read_document":
                return PolicyDescision(
                    effect="ALLOW",
                    reason="Local document access is allowed.",
                    constraints={
                        "workspace_only":True
                    }
                )

            if action.tool == "run_python":
                return PolicyDescision(
                    effect="ALLOW_WITH_RESTRICTIONS",
                    reason="Python execution is allowed only inside a restricted local environment.",
                    constraints={
                        "network": False,
                        "timeout": 30,
                        "memory_mb": 512
                    }
                )

            if action.tool == "write_production_db":
                return PolicyDescision(
                    effect="REQUIRE_APPROVAL",
                    reason="Production database modifications require human approval.",
                    constraints={}
                )

        return PolicyDescision(
            effect="DENY",
            reason="No policy exists that permits this action.",
            constraints={}
        )
