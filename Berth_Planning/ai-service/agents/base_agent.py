"""
Base Agent Class for Berth Planning Multi-Agent System
Uses Claude Opus 4.5 API (Anthropic) for LLM reasoning
"""

import os
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
import json
from datetime import datetime


class BaseAgent:
    """
    Base class for all agents in the berth planning system.
    Uses Claude Opus 4.5 for advanced reasoning and decision-making.
    """

    def __init__(
        self,
        name: str,
        model: str = "claude-opus-4-5-20251101",  # Claude Opus 4.5 (latest, most capable)
        temperature: float = 0.3,
        max_tokens: int = 4096
    ):
        self.name = name
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize Claude client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Get your API key from https://console.anthropic.com/"
            )

        self.client = Anthropic(api_key=api_key)

        # Agent metadata
        self.execution_count = 0
        self.total_tokens_used = 0
        self.last_execution_time = None

    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Invoke Claude Opus 4.5 API with a prompt.

        Args:
            prompt: User message/prompt
            system_prompt: Optional system instructions
            temperature: Override default temperature

        Returns:
            Claude's response text
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt or self._get_default_system_prompt(),
                messages=messages
            )

            # Track usage
            self.execution_count += 1
            self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens
            self.last_execution_time = datetime.now()

            # Extract text from response
            return response.content[0].text

        except Exception as e:
            raise RuntimeError(f"Claude API error in {self.name}: {str(e)}")

    def invoke_with_context(
        self,
        prompt: str,
        context: Dict[str, Any],
        format_as_json: bool = False
    ) -> str:
        """
        Invoke Claude with additional context data.

        Args:
            prompt: Main question/task
            context: Dictionary of context data
            format_as_json: Whether to request JSON output

        Returns:
            Claude's response text
        """
        # Format context as readable text
        context_str = json.dumps(context, indent=2)

        full_prompt = f"""Context Data:
{context_str}

Task:
{prompt}
"""

        if format_as_json:
            full_prompt += "\n\nIMPORTANT: Respond with valid JSON only, no markdown code blocks."

        return self.invoke(full_prompt)

    def invoke_structured(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Invoke Claude and parse JSON response.

        Args:
            prompt: Main question/task
            context: Optional context data
            output_schema: Expected JSON schema (for documentation)

        Returns:
            Parsed JSON dictionary
        """
        schema_instruction = ""
        if output_schema:
            schema_instruction = f"\n\nExpected output schema:\n{json.dumps(output_schema, indent=2)}"

        full_prompt = prompt + schema_instruction

        if context:
            response_text = self.invoke_with_context(full_prompt, context, format_as_json=True)
        else:
            response_text = self.invoke(full_prompt + "\n\nRespond with valid JSON only.")

        # Parse JSON from response
        try:
            # Remove markdown code blocks if present
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from {self.name}: {e}\nResponse: {response_text[:200]}")

    def _get_default_system_prompt(self) -> str:
        """
        Get default system prompt for this agent.
        Override in subclasses for agent-specific behavior.
        """
        return f"""You are {self.name}, an AI agent specializing in maritime port operations and berth planning.

You have access to comprehensive knowledge about:
- Vessel physical constraints (LOA, beam, draft, air draft)
- Cargo type compatibility and dangerous goods handling
- Berth physical capabilities and equipment
- Resource availability (pilots, tugs, labor)
- Tidal and weather constraints
- Priority rules and commercial considerations
- Window vessel operations and SLA management
- Under Keel Clearance (UKC) and navigation safety

Your responses should be:
- Factual and based on provided context
- Concise but complete
- Risk-aware (prioritize safety)
- Commercially informed (consider costs and efficiency)

When making decisions:
1. Evaluate HARD constraints first (safety-critical, non-negotiable)
2. Then evaluate SOFT constraints (optimizable, commercial)
3. Provide clear reasoning for your recommendations
4. Cite specific constraint IDs when applicable (e.g., V-DIM-001)"""

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for the agent.
        Must be implemented by subclasses.

        Args:
            state: Current agent state dictionary

        Returns:
            Updated state dictionary
        """
        raise NotImplementedError(f"{self.name} must implement run() method")

    def get_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics"""
        return {
            "agent_name": self.name,
            "model": self.model,
            "executions": self.execution_count,
            "total_tokens": self.total_tokens_used,
            "estimated_cost_usd": self._estimate_cost(),
            "last_execution": self.last_execution_time.isoformat() if self.last_execution_time else None
        }

    def _estimate_cost(self) -> float:
        """
        Estimate API cost based on token usage.
        Claude Opus 4.5 pricing: $15/1M input, $75/1M output tokens
        Assuming 60/40 input/output split
        """
        if self.total_tokens_used == 0:
            return 0.0

        # Estimate split (60% input, 40% output)
        input_tokens = self.total_tokens_used * 0.6
        output_tokens = self.total_tokens_used * 0.4

        cost = (input_tokens / 1_000_000 * 15.0) + (output_tokens / 1_000_000 * 75.0)
        return round(cost, 4)


# Example usage for testing
if __name__ == "__main__":
    # Test basic agent
    agent = BaseAgent(name="TestAgent")

    # Test simple invocation
    response = agent.invoke("What are the key factors for berth allocation?")
    print(f"Response: {response}\n")

    # Test structured output
    eta_factors = agent.invoke_structured(
        prompt="List the 5 main factors affecting vessel ETA prediction.",
        output_schema={
            "factors": [
                {"name": "string", "description": "string", "impact": "string"}
            ]
        }
    )
    print(f"Structured Response: {json.dumps(eta_factors, indent=2)}\n")

    # Print stats
    print(f"Agent Stats: {json.dumps(agent.get_stats(), indent=2)}")
