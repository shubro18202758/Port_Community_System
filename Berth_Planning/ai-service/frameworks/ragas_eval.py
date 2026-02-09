"""
RAGAS - RAG Assessment & Evaluation Framework
=============================================

Implements comprehensive evaluation metrics for RAG pipelines:
- Faithfulness: Does the answer use only the retrieved context?
- Answer Relevance: Is the answer relevant to the question?
- Context Precision: Are the retrieved documents relevant and ranked correctly?
- Context Recall: Does the context contain the required information?

Uses Claude Opus 4 for LLM-based evaluation judgments.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class EvaluationSample:
    """A single evaluation sample"""
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result of evaluating a single sample"""
    sample_id: str
    faithfulness: float
    answer_relevance: float
    context_precision: float
    context_recall: float
    overall_score: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BatchEvaluationReport:
    """Aggregated evaluation report for a batch"""
    num_samples: int
    avg_faithfulness: float
    avg_answer_relevance: float
    avg_context_precision: float
    avg_context_recall: float
    avg_overall_score: float
    individual_results: List[EvaluationResult]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    config: Dict[str, Any] = field(default_factory=dict)


class RagasEvaluator:
    """
    RAGAS-style evaluation for SmartBerth RAG pipeline.
    
    Uses Claude Opus 4 for LLM-based judgments with carefully crafted prompts
    that follow RAGAS methodology for each metric.
    """
    
    def __init__(
        self,
        llm_client: Any = None,
        model: str = "claude-opus-4-20250514",
        use_local_llm: bool = False,
        local_llm: Any = None
    ):
        """
        Initialize RAGAS evaluator
        
        Args:
            llm_client: Anthropic client for Claude
            model: Model name for evaluation
            use_local_llm: Use local Qwen3 for simpler evaluations
            local_llm: OllamaLLM instance for local evaluation
        """
        self.llm_client = llm_client
        self.model = model
        self.use_local_llm = use_local_llm
        self.local_llm = local_llm
        
        # Evaluation weights
        self.weights = {
            "faithfulness": 0.30,
            "answer_relevance": 0.25,
            "context_precision": 0.25,
            "context_recall": 0.20
        }
        
        logger.info(f"RagasEvaluator initialized with model: {model}")
    
    def _get_sample_id(self, sample: EvaluationSample) -> str:
        """Generate unique ID for sample"""
        content = f"{sample.question}:{sample.answer[:100]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Call LLM for evaluation judgment"""
        try:
            if self.use_local_llm and self.local_llm:
                # Use local Qwen3 via Ollama
                return self.local_llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.1
                )
            elif self.llm_client:
                # Use Claude
                response = self.llm_client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            else:
                logger.warning("No LLM client available for evaluation")
                return ""
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return ""
    
    def _parse_score(self, response: str) -> float:
        """Parse score from LLM response"""
        # Look for patterns like "Score: 0.85" or just "0.85"
        patterns = [
            r'score[:\s]+(\d+\.?\d*)',
            r'rating[:\s]+(\d+\.?\d*)',
            r'^(\d+\.?\d*)$',
            r'(\d+\.?\d*)\s*/\s*1',
            r'(\d+\.?\d*)\s*/\s*10'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.lower())
            if match:
                score = float(match.group(1))
                # Normalize if needed
                if score > 1:
                    score = score / 10
                return min(1.0, max(0.0, score))
        
        # Fallback: look for yes/no
        if "yes" in response.lower():
            return 1.0
        elif "no" in response.lower():
            return 0.0
        
        return 0.5  # Default uncertain
    
    def evaluate_faithfulness(self, sample: EvaluationSample) -> Tuple[float, Dict]:
        """
        Evaluate faithfulness: Does the answer only use information from contexts?
        
        Methodology:
        1. Extract claims from the answer
        2. Check if each claim is supported by the context
        3. Score = supported_claims / total_claims
        """
        context_text = "\n---\n".join(sample.contexts[:5])
        
        prompt = f"""Evaluate FAITHFULNESS of the answer to the given contexts.

FAITHFULNESS measures whether the answer ONLY uses information present in the provided contexts.
An answer is faithful if every claim in it can be verified from the contexts.

QUESTION: {sample.question}

CONTEXTS:
{context_text}

ANSWER: {sample.answer}

INSTRUCTIONS:
1. Identify all factual claims in the answer
2. For each claim, check if it's supported by the contexts
3. Calculate: (supported claims) / (total claims)

Respond with JSON only:
{{"claims": [
    {{"claim": "claim text", "supported": true/false, "evidence": "quote from context or null"}}
],
"score": 0.0-1.0,
"reasoning": "brief explanation"}}"""

        response = self._call_llm(prompt, max_tokens=800)
        
        try:
            # Try to parse JSON
            if "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                data = json.loads(response[start:end])
                return data.get("score", 0.5), {"claims": data.get("claims", [])}
        except (json.JSONDecodeError, ValueError):
            pass
        
        score = self._parse_score(response)
        return score, {"raw_response": response[:200]}
    
    def evaluate_answer_relevance(self, sample: EvaluationSample) -> Tuple[float, Dict]:
        """
        Evaluate answer relevance: Is the answer relevant to the question?
        
        Methodology:
        1. Generate potential questions from the answer
        2. Compare similarity with original question
        3. High similarity = high relevance
        """
        prompt = f"""Evaluate ANSWER RELEVANCE for the given question-answer pair.

ANSWER RELEVANCE measures how well the answer addresses the question asked.
A relevant answer directly addresses what was asked, without being too vague or off-topic.

QUESTION: {sample.question}

ANSWER: {sample.answer}

INSTRUCTIONS:
1. Does the answer directly address the question?
2. Is the information in the answer useful for answering the question?
3. Is the answer specific enough (not too vague)?

Rate the relevance from 0.0 to 1.0:
- 1.0: Perfectly relevant, directly answers the question
- 0.7-0.9: Mostly relevant, addresses the main point
- 0.4-0.6: Partially relevant, some useful info but misses key points
- 0.1-0.3: Barely relevant, mostly off-topic
- 0.0: Completely irrelevant

Respond with JSON only:
{{"score": 0.0-1.0, "reasoning": "explanation", "addresses_question": true/false}}"""

        response = self._call_llm(prompt, max_tokens=400)
        
        try:
            if "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                data = json.loads(response[start:end])
                return data.get("score", 0.5), {"reasoning": data.get("reasoning", "")}
        except (json.JSONDecodeError, ValueError):
            pass
        
        score = self._parse_score(response)
        return score, {"raw_response": response[:200]}
    
    def evaluate_context_precision(self, sample: EvaluationSample) -> Tuple[float, Dict]:
        """
        Evaluate context precision: Are retrieved contexts relevant and well-ranked?
        
        Methodology:
        1. For each context, judge if it's relevant to the question
        2. Use precision@k weighted by rank (higher ranks matter more)
        """
        if not sample.contexts:
            return 0.0, {"error": "No contexts provided"}
        
        context_list = "\n".join([
            f"[Context {i+1}]: {ctx[:300]}..." if len(ctx) > 300 else f"[Context {i+1}]: {ctx}"
            for i, ctx in enumerate(sample.contexts[:5])
        ])
        
        prompt = f"""Evaluate CONTEXT PRECISION for the retrieved documents.

CONTEXT PRECISION measures whether the retrieved contexts are relevant to answering the question.
Higher-ranked contexts (earlier in the list) should be more relevant.

QUESTION: {sample.question}

RETRIEVED CONTEXTS (ranked):
{context_list}

INSTRUCTIONS:
For each context, rate relevance (1 = relevant, 0 = not relevant):
Precision@k = (relevant contexts in top k) / k

Respond with JSON only:
{{"relevance": [1, 0, 1, 0, 1], "precision_at_k": {{"1": 0.0-1.0, "3": 0.0-1.0, "5": 0.0-1.0}}, "score": 0.0-1.0}}"""

        response = self._call_llm(prompt, max_tokens=400)
        
        try:
            if "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                data = json.loads(response[start:end])
                return data.get("score", 0.5), {"relevance": data.get("relevance", [])}
        except (json.JSONDecodeError, ValueError):
            pass
        
        score = self._parse_score(response)
        return score, {"raw_response": response[:200]}
    
    def evaluate_context_recall(self, sample: EvaluationSample) -> Tuple[float, Dict]:
        """
        Evaluate context recall: Do contexts contain info needed to answer?
        
        Methodology:
        1. If ground truth exists, check if contexts contain the required info
        2. Otherwise, check if contexts provide sufficient info for the answer
        """
        context_text = "\n---\n".join(sample.contexts[:5])
        
        reference = sample.ground_truth if sample.ground_truth else sample.answer
        
        prompt = f"""Evaluate CONTEXT RECALL for the retrieved documents.

CONTEXT RECALL measures whether the contexts contain the information needed to produce the correct answer.

QUESTION: {sample.question}

RETRIEVED CONTEXTS:
{context_text}

REFERENCE ANSWER: {reference}

INSTRUCTIONS:
1. Identify key facts in the reference answer
2. Check if these facts are present in the contexts
3. Score = (facts found in contexts) / (total facts in answer)

Respond with JSON only:
{{"key_facts": ["fact1", "fact2"], "found_facts": ["fact1"], "score": 0.0-1.0}}"""

        response = self._call_llm(prompt, max_tokens=500)
        
        try:
            if "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                data = json.loads(response[start:end])
                return data.get("score", 0.5), {"key_facts": data.get("key_facts", [])}
        except (json.JSONDecodeError, ValueError):
            pass
        
        score = self._parse_score(response)
        return score, {"raw_response": response[:200]}
    
    def evaluate_sample(self, sample: EvaluationSample) -> EvaluationResult:
        """
        Evaluate a single sample across all metrics
        
        Args:
            sample: EvaluationSample to evaluate
            
        Returns:
            EvaluationResult with all scores
        """
        sample_id = self._get_sample_id(sample)
        logger.info(f"Evaluating sample {sample_id}: {sample.question[:50]}...")
        
        # Evaluate each metric
        faithfulness, faith_details = self.evaluate_faithfulness(sample)
        relevance, rel_details = self.evaluate_answer_relevance(sample)
        precision, prec_details = self.evaluate_context_precision(sample)
        recall, rec_details = self.evaluate_context_recall(sample)
        
        # Calculate weighted overall score
        overall = (
            self.weights["faithfulness"] * faithfulness +
            self.weights["answer_relevance"] * relevance +
            self.weights["context_precision"] * precision +
            self.weights["context_recall"] * recall
        )
        
        return EvaluationResult(
            sample_id=sample_id,
            faithfulness=faithfulness,
            answer_relevance=relevance,
            context_precision=precision,
            context_recall=recall,
            overall_score=overall,
            details={
                "faithfulness": faith_details,
                "answer_relevance": rel_details,
                "context_precision": prec_details,
                "context_recall": rec_details
            }
        )
    
    def evaluate_batch(
        self,
        samples: List[EvaluationSample],
        verbose: bool = True
    ) -> BatchEvaluationReport:
        """
        Evaluate a batch of samples
        
        Args:
            samples: List of samples to evaluate
            verbose: Print progress
            
        Returns:
            BatchEvaluationReport with aggregated metrics
        """
        results = []
        
        for i, sample in enumerate(samples):
            if verbose:
                print(f"Evaluating {i+1}/{len(samples)}: {sample.question[:40]}...")
            
            result = self.evaluate_sample(sample)
            results.append(result)
        
        # Aggregate metrics
        n = len(results)
        if n == 0:
            return BatchEvaluationReport(
                num_samples=0,
                avg_faithfulness=0,
                avg_answer_relevance=0,
                avg_context_precision=0,
                avg_context_recall=0,
                avg_overall_score=0,
                individual_results=[]
            )
        
        report = BatchEvaluationReport(
            num_samples=n,
            avg_faithfulness=sum(r.faithfulness for r in results) / n,
            avg_answer_relevance=sum(r.answer_relevance for r in results) / n,
            avg_context_precision=sum(r.context_precision for r in results) / n,
            avg_context_recall=sum(r.context_recall for r in results) / n,
            avg_overall_score=sum(r.overall_score for r in results) / n,
            individual_results=results,
            config={"weights": self.weights, "model": self.model}
        )
        
        if verbose:
            self.print_report(report)
        
        return report
    
    def print_report(self, report: BatchEvaluationReport):
        """Print formatted evaluation report"""
        print("\n" + "=" * 60)
        print("RAGAS EVALUATION REPORT")
        print("=" * 60)
        print(f"Samples evaluated: {report.num_samples}")
        print(f"Timestamp: {report.timestamp}")
        print("-" * 60)
        print(f"Average Faithfulness:      {report.avg_faithfulness:.3f}")
        print(f"Average Answer Relevance:  {report.avg_answer_relevance:.3f}")
        print(f"Average Context Precision: {report.avg_context_precision:.3f}")
        print(f"Average Context Recall:    {report.avg_context_recall:.3f}")
        print("-" * 60)
        print(f"OVERALL SCORE:             {report.avg_overall_score:.3f}")
        print("=" * 60)
    
    def to_dict(self, report: BatchEvaluationReport) -> Dict[str, Any]:
        """Convert report to dictionary for JSON serialization"""
        return {
            "num_samples": report.num_samples,
            "metrics": {
                "avg_faithfulness": report.avg_faithfulness,
                "avg_answer_relevance": report.avg_answer_relevance,
                "avg_context_precision": report.avg_context_precision,
                "avg_context_recall": report.avg_context_recall,
                "avg_overall_score": report.avg_overall_score
            },
            "timestamp": report.timestamp,
            "config": report.config,
            "individual_results": [asdict(r) for r in report.individual_results]
        }


# Factory function
def get_ragas_evaluator(llm_client=None, local_llm=None, use_local_llm=False, **kwargs) -> RagasEvaluator:
    """Create a RAGAS evaluator instance"""
    return RagasEvaluator(llm_client=llm_client, local_llm=local_llm, use_local_llm=use_local_llm, **kwargs)
