"""
DSPy - Declarative Self-improving Language Programs
====================================================

Implements DSPy-style prompt optimization for SmartBerth:
- Signatures: Declarative I/O specifications
- Modules: Composable prompt templates
- Optimizers: Automatic prompt tuning based on examples
- Chain-of-Thought: Reasoning trace generation

Adapted for both Claude (complex) and Qwen3 (fast) execution.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# SIGNATURES - Declarative I/O Specifications
# ============================================================================

@dataclass
class Field:
    """A field in a signature with description and validation"""
    name: str
    description: str
    prefix: str = ""
    format: str = "text"  # text, json, list, number
    required: bool = True


@dataclass
class Signature:
    """
    Declarative specification of a task's inputs and outputs.
    Similar to DSPy signatures but adapted for SmartBerth.
    """
    name: str
    description: str
    input_fields: List[Field]
    output_fields: List[Field]
    instructions: str = ""
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_input_names(self) -> List[str]:
        return [f.name for f in self.input_fields]
    
    def get_output_names(self) -> List[str]:
        return [f.name for f in self.output_fields]
    
    def to_prompt_template(self) -> str:
        """Generate prompt template from signature"""
        parts = [f"Task: {self.description}"]
        
        if self.instructions:
            parts.append(f"\nInstructions: {self.instructions}")
        
        # Input format
        parts.append("\n--- INPUT ---")
        for field in self.input_fields:
            prefix = f"[{field.prefix}] " if field.prefix else ""
            parts.append(f"{prefix}{field.name}: {{{field.name}}}")
        
        # Output format
        parts.append("\n--- OUTPUT ---")
        for field in self.output_fields:
            prefix = f"[{field.prefix}] " if field.prefix else ""
            parts.append(f"{prefix}{field.name}:")
        
        return "\n".join(parts)


# ============================================================================
# PREDEFINED SIGNATURES FOR SMARTBERTH
# ============================================================================

# Signature for berth recommendation
BERTH_RECOMMENDATION_SIG = Signature(
    name="BerthRecommendation",
    description="Recommend optimal berth for a vessel based on constraints",
    input_fields=[
        Field("vessel_info", "Vessel specifications (LOA, beam, draft, type)", prefix="Vessel"),
        Field("available_berths", "List of available berths with specs", prefix="Berths"),
        Field("constraints", "Any additional constraints or preferences", prefix="Constraints")
    ],
    output_fields=[
        Field("recommended_berth", "The recommended berth code", prefix="Recommendation"),
        Field("reasoning", "Explanation for the recommendation", prefix="Reasoning"),
        Field("alternatives", "Alternative berths if primary unavailable", format="list")
    ],
    instructions="Consider vessel dimensions, berth capacity, and any operational constraints."
)

# Signature for ETA prediction
ETA_PREDICTION_SIG = Signature(
    name="ETAPrediction",
    description="Predict vessel arrival time based on AIS data and conditions",
    input_fields=[
        Field("vessel_position", "Current vessel position (lat, lon)", prefix="Position"),
        Field("vessel_speed", "Current speed in knots", prefix="Speed"),
        Field("distance_to_port", "Distance to port in nautical miles", prefix="Distance"),
        Field("weather_conditions", "Current weather affecting travel", prefix="Weather")
    ],
    output_fields=[
        Field("eta_hours", "Estimated time of arrival in hours", format="number"),
        Field("confidence", "Confidence level (0-1)", format="number"),
        Field("factors", "Factors affecting the prediction", format="list")
    ],
    instructions="Account for weather, traffic, and historical patterns."
)

# Signature for query classification
QUERY_CLASSIFICATION_SIG = Signature(
    name="QueryClassification",
    description="Classify user query into task type for routing",
    input_fields=[
        Field("query", "User's natural language query", prefix="Query"),
        Field("context", "Optional conversation context", prefix="Context", required=False)
    ],
    output_fields=[
        Field("task_type", "Classification: BERTH_QUERY, VESSEL_QUERY, OPTIMIZATION, ANALYTICS, GRAPH_QUERY, GENERAL"),
        Field("confidence", "Confidence score 0-1", format="number"),
        Field("entities", "Extracted entities", format="list")
    ],
    instructions="Identify the primary intent and extract any named entities."
)

# Signature for RAG response generation
RAG_RESPONSE_SIG = Signature(
    name="RAGResponse",
    description="Generate response using retrieved context",
    input_fields=[
        Field("question", "User's question", prefix="Question"),
        Field("context", "Retrieved relevant documents", prefix="Context"),
        Field("chat_history", "Previous conversation turns", prefix="History", required=False)
    ],
    output_fields=[
        Field("answer", "Comprehensive answer to the question"),
        Field("sources", "Sources used from context", format="list"),
        Field("confidence", "Answer confidence 0-1", format="number")
    ],
    instructions="Answer based ONLY on the provided context. Cite sources."
)


# ============================================================================
# MODULES - Composable Prompt Components
# ============================================================================

class Module(ABC):
    """Base class for DSPy-style modules"""
    
    def __init__(self, signature: Signature):
        self.signature = signature
        self.compiled_prompt: Optional[str] = None
        self.demonstrations: List[Dict] = []
    
    @abstractmethod
    def forward(self, **kwargs) -> Dict[str, Any]:
        """Execute the module with given inputs"""
        pass
    
    def add_demonstration(self, demo: Dict[str, Any]):
        """Add a demonstration example"""
        self.demonstrations.append(demo)


class Predict(Module):
    """
    Basic prediction module - generates output from signature.
    Equivalent to DSPy's dspy.Predict.
    """
    
    def __init__(
        self,
        signature: Signature,
        llm_caller: Callable[[str], str],
        max_tokens: int = 500
    ):
        super().__init__(signature)
        self.llm_caller = llm_caller
        self.max_tokens = max_tokens
    
    def _build_prompt(self, **kwargs) -> str:
        """Build prompt from signature and inputs"""
        prompt_parts = [f"# {self.signature.name}"]
        prompt_parts.append(f"\n{self.signature.description}")
        
        if self.signature.instructions:
            prompt_parts.append(f"\nInstructions: {self.signature.instructions}")
        
        # Add demonstrations if available
        if self.demonstrations:
            prompt_parts.append("\n## Examples:")
            for i, demo in enumerate(self.demonstrations[:3]):
                prompt_parts.append(f"\n### Example {i+1}:")
                for field in self.signature.input_fields:
                    if field.name in demo:
                        prompt_parts.append(f"{field.name}: {demo[field.name]}")
                for field in self.signature.output_fields:
                    if field.name in demo:
                        prompt_parts.append(f"{field.name}: {demo[field.name]}")
        
        # Add current input
        prompt_parts.append("\n## Current Task:")
        for field in self.signature.input_fields:
            value = kwargs.get(field.name, "")
            if value or field.required:
                prompt_parts.append(f"{field.name}: {value}")
        
        # Request output
        prompt_parts.append("\n## Output (respond with values for each field):")
        for field in self.signature.output_fields:
            prompt_parts.append(f"{field.name}:")
        
        return "\n".join(prompt_parts)
    
    def _parse_output(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured output"""
        result = {}
        
        for field in self.signature.output_fields:
            # Try to find field value in response
            patterns = [
                rf'{field.name}[:\s]+(.+?)(?=\n[A-Za-z_]+:|$)',
                rf'\*\*{field.name}\*\*[:\s]+(.+?)(?=\n|$)',
            ]
            
            value = None
            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    break
            
            if value:
                # Convert based on format
                if field.format == "number":
                    try:
                        # Extract number from string
                        num_match = re.search(r'(\d+\.?\d*)', value)
                        if num_match:
                            value = float(num_match.group(1))
                    except ValueError:
                        pass
                elif field.format == "list":
                    # Try to parse as list
                    if value.startswith("["):
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            value = [v.strip() for v in value.strip("[]").split(",")]
                    else:
                        value = [v.strip() for v in value.split(",")]
                elif field.format == "json":
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass
            
            result[field.name] = value
        
        return result
    
    def forward(self, **kwargs) -> Dict[str, Any]:
        """Execute prediction"""
        prompt = self._build_prompt(**kwargs)
        response = self.llm_caller(prompt)
        return self._parse_output(response)


class ChainOfThought(Module):
    """
    Chain-of-thought module - generates reasoning before answer.
    Equivalent to DSPy's dspy.ChainOfThought.
    """
    
    def __init__(
        self,
        signature: Signature,
        llm_caller: Callable[[str], str],
        max_tokens: int = 800
    ):
        super().__init__(signature)
        self.llm_caller = llm_caller
        self.max_tokens = max_tokens
    
    def _build_cot_prompt(self, **kwargs) -> str:
        """Build chain-of-thought prompt"""
        prompt_parts = [f"# {self.signature.name}"]
        prompt_parts.append(f"\n{self.signature.description}")
        
        if self.signature.instructions:
            prompt_parts.append(f"\nInstructions: {self.signature.instructions}")
        
        # Add inputs
        prompt_parts.append("\n## Input:")
        for field in self.signature.input_fields:
            value = kwargs.get(field.name, "")
            if value or field.required:
                prompt_parts.append(f"{field.name}: {value}")
        
        # Request reasoning then output
        prompt_parts.append("\n## Reasoning (think step by step):")
        prompt_parts.append("Let me analyze this step by step...")
        prompt_parts.append("\n## Output:")
        for field in self.signature.output_fields:
            prompt_parts.append(f"{field.name}:")
        
        return "\n".join(prompt_parts)
    
    def forward(self, **kwargs) -> Dict[str, Any]:
        """Execute with chain-of-thought"""
        prompt = self._build_cot_prompt(**kwargs)
        response = self.llm_caller(prompt)
        
        # Parse reasoning and output
        result = {"reasoning": ""}
        
        # Extract reasoning
        reasoning_match = re.search(
            r'reasoning[:\s]*(.*?)(?=\n##\s*output|$)',
            response, re.IGNORECASE | re.DOTALL
        )
        if reasoning_match:
            result["reasoning"] = reasoning_match.group(1).strip()
        
        # Parse output fields
        for field in self.signature.output_fields:
            pattern = rf'{field.name}[:\s]+(.+?)(?=\n[A-Za-z_]+:|$)'
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                result[field.name] = match.group(1).strip()
        
        return result


# ============================================================================
# OPTIMIZERS - Automatic Prompt Tuning
# ============================================================================

@dataclass
class OptimizationExample:
    """Training example for optimization"""
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, Any]
    score: Optional[float] = None


class BootstrapFewShot:
    """
    Bootstrap few-shot optimizer.
    Automatically selects best demonstrations for a signature.
    Similar to DSPy's BootstrapFewShot.
    """
    
    def __init__(
        self,
        metric: Callable[[Dict, Dict], float],
        max_demonstrations: int = 5,
        max_rounds: int = 3
    ):
        """
        Args:
            metric: Function(prediction, expected) -> score
            max_demonstrations: Max demos to include
            max_rounds: Max optimization rounds
        """
        self.metric = metric
        self.max_demonstrations = max_demonstrations
        self.max_rounds = max_rounds
        self.best_demos: List[Dict] = []
    
    def compile(
        self,
        module: Module,
        trainset: List[OptimizationExample]
    ) -> Module:
        """
        Compile module with optimized demonstrations
        
        Args:
            module: Module to optimize
            trainset: Training examples
            
        Returns:
            Optimized module with best demonstrations
        """
        logger.info(f"Optimizing {module.signature.name} with {len(trainset)} examples")
        
        best_score = 0.0
        best_demos = []
        
        for round_num in range(self.max_rounds):
            # Try different demonstration combinations
            for example in trainset:
                # Run module
                try:
                    prediction = module.forward(**example.inputs)
                    score = self.metric(prediction, example.expected_outputs)
                    example.score = score
                except Exception as e:
                    logger.warning(f"Example failed: {e}")
                    example.score = 0.0
            
            # Select best examples as demonstrations
            scored_examples = [e for e in trainset if e.score is not None]
            scored_examples.sort(key=lambda x: x.score, reverse=True)
            
            top_examples = scored_examples[:self.max_demonstrations]
            avg_score = sum(e.score for e in top_examples) / len(top_examples) if top_examples else 0
            
            if avg_score > best_score:
                best_score = avg_score
                best_demos = [
                    {**e.inputs, **e.expected_outputs}
                    for e in top_examples
                ]
        
        # Apply best demonstrations to module
        module.demonstrations = best_demos
        logger.info(f"Optimization complete. Best score: {best_score:.3f}")
        
        return module


class PromptOptimizer:
    """
    High-level optimizer that improves prompts based on feedback.
    Combines signature tuning with demonstration selection.
    """
    
    def __init__(
        self,
        llm_caller: Callable[[str], str],
        metric: Callable[[Dict, Dict], float]
    ):
        self.llm_caller = llm_caller
        self.metric = metric
        self.optimization_history: List[Dict] = []
    
    def optimize_instructions(
        self,
        signature: Signature,
        examples: List[OptimizationExample],
        n_iterations: int = 3
    ) -> Signature:
        """
        Optimize signature instructions using LLM feedback
        
        Args:
            signature: Signature to optimize
            examples: Training examples
            n_iterations: Number of optimization iterations
            
        Returns:
            Signature with optimized instructions
        """
        current_instructions = signature.instructions
        best_score = 0.0
        best_instructions = current_instructions
        
        for iteration in range(n_iterations):
            # Evaluate current instructions
            module = Predict(signature, self.llm_caller)
            scores = []
            
            for example in examples[:5]:  # Use subset for speed
                try:
                    pred = module.forward(**example.inputs)
                    score = self.metric(pred, example.expected_outputs)
                    scores.append(score)
                except Exception:
                    scores.append(0.0)
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            if avg_score > best_score:
                best_score = avg_score
                best_instructions = current_instructions
            
            # Generate improved instructions using LLM
            improve_prompt = f"""Improve these instructions for better task performance.

Current Instructions: {current_instructions}

Task: {signature.description}
Average Score: {avg_score:.3f}

Common failure patterns observed. Generate better instructions (2-3 sentences):"""
            
            new_instructions = self.llm_caller(improve_prompt)
            current_instructions = new_instructions.strip()[:500]  # Limit length
            
            self.optimization_history.append({
                "iteration": iteration,
                "instructions": current_instructions,
                "score": avg_score
            })
        
        # Update signature with best instructions
        signature.instructions = best_instructions
        return signature


# ============================================================================
# DSPY OPTIMIZER - Main Interface
# ============================================================================

class DSPyOptimizer:
    """
    Main DSPy-style optimizer for SmartBerth.
    
    Provides:
    - Signature-based task definition
    - Automatic prompt optimization
    - Chain-of-thought integration
    - Few-shot learning
    """
    
    def __init__(
        self,
        llm_caller: Callable[[str], str],
        use_cot: bool = True
    ):
        """
        Initialize DSPy optimizer
        
        Args:
            llm_caller: Function to call LLM
            use_cot: Use chain-of-thought by default
        """
        self.llm_caller = llm_caller
        self.use_cot = use_cot
        self.signatures: Dict[str, Signature] = {
            "berth_recommendation": BERTH_RECOMMENDATION_SIG,
            "eta_prediction": ETA_PREDICTION_SIG,
            "query_classification": QUERY_CLASSIFICATION_SIG,
            "rag_response": RAG_RESPONSE_SIG
        }
        self.compiled_modules: Dict[str, Module] = {}
    
    def get_signature(self, name: str) -> Optional[Signature]:
        """Get a predefined signature by name"""
        return self.signatures.get(name)
    
    def register_signature(self, name: str, signature: Signature):
        """Register a custom signature"""
        self.signatures[name] = signature
    
    def create_module(
        self,
        signature: Signature,
        use_cot: Optional[bool] = None
    ) -> Module:
        """
        Create a module from signature
        
        Args:
            signature: Signature defining the task
            use_cot: Override default CoT setting
            
        Returns:
            Compiled module ready for execution
        """
        cot = use_cot if use_cot is not None else self.use_cot
        
        if cot:
            return ChainOfThought(signature, self.llm_caller)
        else:
            return Predict(signature, self.llm_caller)
    
    def compile(
        self,
        signature_name: str,
        trainset: List[OptimizationExample],
        metric: Callable[[Dict, Dict], float] = None
    ) -> Module:
        """
        Compile and optimize a module
        
        Args:
            signature_name: Name of signature to compile
            trainset: Training examples
            metric: Evaluation metric function
            
        Returns:
            Optimized module
        """
        signature = self.signatures.get(signature_name)
        if not signature:
            raise ValueError(f"Unknown signature: {signature_name}")
        
        # Default metric: exact match ratio
        if metric is None:
            def metric(pred, expected):
                matches = sum(1 for k, v in expected.items() if pred.get(k) == v)
                return matches / len(expected) if expected else 0
        
        module = self.create_module(signature)
        
        # Optimize with bootstrap few-shot
        optimizer = BootstrapFewShot(metric=metric)
        optimized = optimizer.compile(module, trainset)
        
        self.compiled_modules[signature_name] = optimized
        return optimized
    
    def predict(
        self,
        signature_name: str,
        **inputs
    ) -> Dict[str, Any]:
        """
        Run prediction with compiled or default module
        
        Args:
            signature_name: Which signature to use
            **inputs: Input values
            
        Returns:
            Prediction outputs
        """
        if signature_name in self.compiled_modules:
            module = self.compiled_modules[signature_name]
        else:
            signature = self.signatures.get(signature_name)
            if not signature:
                raise ValueError(f"Unknown signature: {signature_name}")
            module = self.create_module(signature)
        
        return module.forward(**inputs)
    
    def classify_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """Convenience method for query classification"""
        return self.predict(
            "query_classification",
            query=query,
            context=context
        )
    
    def generate_rag_response(
        self,
        question: str,
        context: str,
        chat_history: str = ""
    ) -> Dict[str, Any]:
        """Convenience method for RAG response generation"""
        return self.predict(
            "rag_response",
            question=question,
            context=context,
            chat_history=chat_history
        )
    
    def recommend_berth(
        self,
        vessel_info: str,
        available_berths: str,
        constraints: str = ""
    ) -> Dict[str, Any]:
        """Convenience method for berth recommendation"""
        return self.predict(
            "berth_recommendation",
            vessel_info=vessel_info,
            available_berths=available_berths,
            constraints=constraints
        )


# Factory function
def get_dspy_optimizer(llm_caller: Callable[[str], str], **kwargs) -> DSPyOptimizer:
    """Create a DSPy optimizer instance"""
    return DSPyOptimizer(llm_caller=llm_caller, **kwargs)
