"""
SmartBerth AI - Graph Reasoner
Executes Cypher queries and generates natural language explanations using Claude Opus 4
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .query_templates import CypherQueryTemplates, QueryTemplate, QueryType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReasoningResult:
    """Result from graph reasoning"""
    query_type: str
    query_parameters: Dict[str, Any]
    raw_results: List[Dict[str, Any]]
    explanation: str
    confidence: float
    reasoning_time_ms: float
    recommendations: List[str]
    warnings: List[str]


class GraphReasoner:
    """
    Graph reasoner that:
    1. Executes Cypher queries against Neo4j
    2. Passes results to Claude Opus 4 for natural language explanation
    3. Returns structured reasoning with recommendations
    """
    
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "smartberth123",
        neo4j_database: str = "neo4j",
        anthropic_api_key: Optional[str] = None,
        model: str = "claude-opus-4-20250514"
    ):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.neo4j_database = neo4j_database
        self.model = model
        
        # Initialize Neo4j driver
        self._driver: Optional[Driver] = None
        
        # Initialize Anthropic client
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client: Optional[anthropic.Anthropic] = None
        
        # Query templates
        self.templates = CypherQueryTemplates()
    
    @property
    def driver(self) -> Optional[Driver]:
        """Lazy initialization of Neo4j driver"""
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j driver not available")
            return None
            
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.neo4j_uri,
                    auth=(self.neo4j_user, self.neo4j_password)
                )
                self._driver.verify_connectivity()
                logger.info(f"Connected to Neo4j at {self.neo4j_uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                self._driver = None
        return self._driver
    
    @property
    def client(self) -> Optional[anthropic.Anthropic]:
        """Lazy initialization of Anthropic client"""
        if not ANTHROPIC_AVAILABLE:
            logger.error("Anthropic SDK not available")
            return None
            
        if self._client is None and self.api_key:
            self._client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("Anthropic client initialized")
        return self._client
    
    def close(self):
        """Close connections"""
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def execute_cypher(
        self, 
        cypher: str, 
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results"""
        if not self.driver:
            return []
            
        results = []
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(cypher, parameters)
            for record in result:
                results.append(dict(record))
        
        return results
    
    def _generate_explanation(
        self,
        template: QueryTemplate,
        parameters: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate natural language explanation using Claude"""
        
        if not self.client:
            return {
                "explanation": "Claude API not available for explanation generation.",
                "confidence": 0.5,
                "recommendations": [],
                "warnings": ["AI explanation unavailable"]
            }
        
        # Build the prompt
        system_prompt = """You are SmartBerth AI, an expert maritime logistics assistant specializing in berth planning and vessel scheduling.
        
You have been given results from a graph database query about port operations. Your task is to:
1. Analyze the query results
2. Provide a clear, professional explanation
3. Give actionable recommendations
4. Flag any concerns or warnings

Always be specific with numbers, names, and details from the data.
Format your response as JSON with these keys:
- explanation: A detailed narrative explanation (2-4 paragraphs)
- confidence: A score from 0.0 to 1.0 indicating confidence in recommendations
- recommendations: A list of specific actionable recommendations
- warnings: A list of any concerns or potential issues"""

        user_prompt = f"""Query Type: {template.name}
Query Description: {template.description}

Query Parameters:
{json.dumps(parameters, indent=2, default=str)}

Query Results:
{json.dumps(results, indent=2, default=str)}

Explanation Guidelines:
{template.explanation_prompt}

Provide your analysis as JSON:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Try to parse as JSON
            try:
                # Find JSON in response (may be wrapped in markdown code blocks)
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                parsed = json.loads(response_text)
                return {
                    "explanation": parsed.get("explanation", response_text),
                    "confidence": float(parsed.get("confidence", 0.8)),
                    "recommendations": parsed.get("recommendations", []),
                    "warnings": parsed.get("warnings", [])
                }
            except json.JSONDecodeError:
                # Return raw response if not JSON
                return {
                    "explanation": response_text,
                    "confidence": 0.7,
                    "recommendations": [],
                    "warnings": []
                }
                
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return {
                "explanation": f"Error generating AI explanation: {str(e)}",
                "confidence": 0.0,
                "recommendations": [],
                "warnings": [str(e)]
            }
    
    def reason(
        self,
        query_type: QueryType,
        parameters: Dict[str, Any]
    ) -> ReasoningResult:
        """
        Execute a graph query and generate reasoned explanation
        
        Args:
            query_type: Type of query to execute
            parameters: Query parameters
            
        Returns:
            ReasoningResult with raw data and AI explanation
        """
        import time
        start_time = time.time()
        
        # Get template
        template = self.templates.get_template(query_type)
        if not template:
            return ReasoningResult(
                query_type=query_type.value,
                query_parameters=parameters,
                raw_results=[],
                explanation=f"Unknown query type: {query_type}",
                confidence=0.0,
                reasoning_time_ms=0,
                recommendations=[],
                warnings=[f"Query type '{query_type}' not found"]
            )
        
        # Execute query
        results = self.execute_cypher(template.cypher, parameters)
        
        # Generate explanation
        explanation_result = self._generate_explanation(template, parameters, results)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return ReasoningResult(
            query_type=query_type.value,
            query_parameters=parameters,
            raw_results=results,
            explanation=explanation_result["explanation"],
            confidence=explanation_result["confidence"],
            reasoning_time_ms=round(elapsed_ms, 2),
            recommendations=explanation_result["recommendations"],
            warnings=explanation_result["warnings"]
        )
    
    def find_suitable_berths(
        self,
        vessel_id: int,
        check_time_start: str,
        check_time_end: str
    ) -> ReasoningResult:
        """Find suitable berths for a vessel"""
        return self.reason(
            QueryType.SUITABLE_BERTHS,
            {
                "vessel_id": vessel_id,
                "check_time_start": check_time_start,
                "check_time_end": check_time_end
            }
        )
    
    def explain_berth_recommendation(
        self,
        vessel_id: int,
        berth_id: int
    ) -> ReasoningResult:
        """Explain why a berth is recommended for a vessel"""
        return self.reason(
            QueryType.BERTH_EXPLANATION,
            {
                "vessel_id": vessel_id,
                "berth_id": berth_id
            }
        )
    
    def analyze_conflict_cascade(
        self,
        schedule_id: int
    ) -> ReasoningResult:
        """Analyze cascading effects of a scheduling conflict"""
        return self.reason(
            QueryType.CONFLICT_CASCADE,
            {
                "schedule_id": schedule_id
            }
        )
    
    def detect_resource_contention(
        self,
        port_id: int,
        time_start: str,
        time_end: str
    ) -> ReasoningResult:
        """Detect resource contention at a port"""
        return self.reason(
            QueryType.RESOURCE_CONTENTION,
            {
                "port_id": port_id,
                "time_start": time_start,
                "time_end": time_end
            }
        )
    
    def find_alternative_berths(
        self,
        vessel_id: int,
        exclude_berth_id: Optional[int] = None,
        time_start: Optional[str] = None,
        time_end: Optional[str] = None,
        limit: int = 5
    ) -> ReasoningResult:
        """Find alternative berths with historical preference"""
        return self.reason(
            QueryType.ALTERNATIVE_BERTHS,
            {
                "vessel_id": vessel_id,
                "exclude_berth_id": exclude_berth_id,
                "time_start": time_start or datetime.now().isoformat(),
                "time_end": time_end or datetime.now().isoformat(),
                "limit": limit
            }
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get reasoner status"""
        return {
            "neo4j_connected": self.driver is not None,
            "neo4j_uri": self.neo4j_uri,
            "anthropic_available": self.client is not None,
            "model": self.model,
            "available_queries": list(QueryType.__members__.keys())
        }


@lru_cache()
def get_graph_reasoner() -> GraphReasoner:
    """Get cached graph reasoner instance"""
    return GraphReasoner(
        neo4j_uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        neo4j_user=os.getenv("NEO4J_USERNAME", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", "smartberth123"),
        neo4j_database=os.getenv("NEO4J_DATABASE", "neo4j"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-20250514")
    )


if __name__ == "__main__":
    print("=" * 60)
    print("SmartBerth AI - Graph Reasoner")
    print("=" * 60)
    
    reasoner = get_graph_reasoner()
    
    print("\n📊 Reasoner Status:")
    status = reasoner.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Test if Neo4j is connected
    if status["neo4j_connected"]:
        print("\n🔍 Testing query execution...")
        
        # Try a simple query
        test_results = reasoner.execute_cypher(
            "MATCH (n) RETURN labels(n)[0] as label, count(*) as count LIMIT 10",
            {}
        )
        
        if test_results:
            print("   Graph contains:")
            for r in test_results:
                print(f"      {r['label']}: {r['count']} nodes")
        else:
            print("   No data in graph (run data_loader.py first)")
    else:
        print("\n⚠️ Neo4j not connected")
        print("   Make sure Neo4j is running and accessible")
    
    reasoner.close()
    print("\n✅ Done")
