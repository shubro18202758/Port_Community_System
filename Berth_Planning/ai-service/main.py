"""
SmartBerth AI Service - FastAPI Application
Main entry point for the AI-powered berth planning service
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import asyncio
import json

from config import get_settings
from model import get_model
from database import get_db_service
from services import get_eta_predictor, get_berth_allocator, get_constraint_validator
from rag import get_rag_pipeline
from chatbot import get_chatbot

# Import weather scheduler
from weather_scheduler import get_weather_scheduler, start_weather_scheduler, stop_weather_scheduler

# Import legacy agents (rule-based)
from agents_legacy import (
    get_orchestrator_agent, 
    get_eta_predictor_agent,
    get_berth_optimizer_agent,
    get_conflict_resolver_agent
)

# Import new Claude-powered agents
from agents import (
    BaseAgent,
    ETAPredictorAgent as ClaudeETAAgent,
    BerthOptimizerAgent as ClaudeBerthAgent,
    ConflictResolverAgent as ClaudeConflictAgent
)

# Import hybrid RAG retriever
from rag_hybrid import HybridRetriever, get_retriever

# Import enhanced ML services
from enhanced_services import (
    get_prediction_service,
    get_optimization_service,
    get_traffic_service,
    SmartBerthPrediction,
    ScheduleOptimizationResult
)

# Import SmartBerth Core (Claude-powered)
from smartberth_core import get_smartberth_core

# Configure logging early for import error reporting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Alert Service (Agentic Monitoring)
try:
    from alert_service import (
        get_alert_service,
        AlertService,
        AlertCategory,
        AlertType,
        AlertSeverity,
        ActivityEntry,
        ConfidenceFactors
    )
    ALERT_SERVICE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Alert Service not available: {e}")
    ALERT_SERVICE_AVAILABLE = False
    get_alert_service = None

# Import Browser Agent (Agentic System)
try:
    from browser_agent import (
        AgenticBrowserController,
        AgentTask,
        AgentState,
        ActionType,
        AgentStep,
        create_browser_agent,
        TOOLS_AVAILABLE as AGENT_TOOLS_AVAILABLE
    )
    BROWSER_AGENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Browser Agent not available: {e}")
    BROWSER_AGENT_AVAILABLE = False
    AGENT_TOOLS_AVAILABLE = False
    create_browser_agent = None

# Import Unified Pipeline API
try:
    from pipeline_api import router as pipeline_router, get_pipeline
    PIPELINE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Unified Pipeline not available: {e}")
    PIPELINE_AVAILABLE = False
    pipeline_router = None

# Settings
settings = get_settings()


# ==================== PYDANTIC MODELS ====================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model_status: str
    database_status: str
    rag_status: str


class ModelInfo(BaseModel):
    status: str
    model_name: str
    model_type: Optional[str] = None
    provider: Optional[str] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None


class GenerationRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = Field(default=512, ge=1, le=2048)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)


class GenerationResponse(BaseModel):
    success: bool
    text: str
    tokens_generated: Optional[int] = None
    model: Optional[str] = None
    error: Optional[str] = None


class ETAPredictionResponse(BaseModel):
    vessel_id: int
    vessel_name: str
    original_eta: Optional[str] = None
    predicted_eta: Optional[str] = None
    deviation_minutes: int
    confidence_score: float
    status: str
    factors: Dict[str, Any]
    ai_explanation: str


class BerthSuggestionResponse(BaseModel):
    berth_id: int
    berth_name: str
    terminal_name: str
    total_score: float
    constraint_score: float
    utilization_score: float
    waiting_time_score: float
    priority_score: float
    violations: List[Dict[str, Any]]
    is_feasible: bool
    explanation: str


class ConstraintValidationRequest(BaseModel):
    vessel_id: int
    berth_id: int
    eta: Optional[str] = None


class ConstraintValidationResponse(BaseModel):
    is_feasible: bool
    violations: List[Dict[str, Any]]
    priority_score: float


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    text: str
    intent: str
    entities: Dict[str, Any]
    structured_data: Optional[Dict[str, Any]] = None
    actions: List[Dict[str, Any]]
    confidence: float


class ExplanationRequest(BaseModel):
    query: str
    context_category: Optional[str] = None
    additional_context: Optional[str] = None


class ExplanationResponse(BaseModel):
    success: bool
    explanation: str
    context_used: List[str]
    model: str


# New: Multi-Agent System Request/Response Models
class VesselArrivalProcessRequest(BaseModel):
    vessel_id: int


class OptimizationRequest(BaseModel):
    algorithm: str = Field(default="greedy", description="Algorithm: greedy or genetic")
    time_horizon_hours: int = Field(default=48, ge=6, le=168)


class WhatIfScenarioRequest(BaseModel):
    scenario_type: str = Field(..., description="Type: delay, berth_closure, or surge")
    vessel_id: Optional[int] = None
    berth_id: Optional[int] = None
    delay_hours: Optional[int] = 4
    duration_hours: Optional[int] = 24
    additional_vessels: Optional[int] = 5


# Alert Service Models
class CreateAlertRequest(BaseModel):
    category: str = Field(..., description="Alert category: VESSEL_TRACKING, ETA_PREDICTION, etc.")
    alert_type: str = Field(..., description="Specific alert type")
    severity: str = Field(default="INFO", description="Severity: DEBUG, INFO, WARNING, HIGH, CRITICAL")
    title: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    affected_vessels: List[int] = Field(default_factory=list)
    affected_berths: List[int] = Field(default_factory=list)


class ActivityFeedResponse(BaseModel):
    activities: List[Dict[str, Any]]
    total_count: int
    unread_counts: Dict[str, int]


class MonitoringStatusResponse(BaseModel):
    is_active: bool
    interval_seconds: int
    last_check: Optional[str] = None
    alerts_generated_today: int


class ConflictResolutionRequest(BaseModel):
    conflict_id: int
    resolution_action: str


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting SmartBerth AI Service...")
    
    # Test database connection
    db = get_db_service()
    if db.test_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.warning("⚠️ Database connection failed - some features may be unavailable")
    
    # Initialize model (can be done later via endpoint)
    model = get_model()
    logger.info(f"Model configured: {settings.claude_model} via Anthropic Claude API")
    logger.info("Note: Model will be loaded on first inference or via /model/load endpoint")
    
    # Initialize RAG pipeline
    rag = get_rag_pipeline()
    if rag.initialize():
        logger.info("✅ RAG pipeline initialized")
    else:
        logger.warning("⚠️ RAG pipeline initialization failed")

    # Start weather scheduler (if weather API key is configured)
    if settings.weather_api_key:
        try:
            await start_weather_scheduler()
            logger.info("✅ Weather scheduler started (hourly updates enabled)")
        except Exception as e:
            logger.warning(f"⚠️ Weather scheduler failed to start: {e}")
    else:
        logger.warning("⚠️ Weather API key not configured - weather updates disabled")

    logger.info("SmartBerth AI Service started successfully!")

    yield

    # Cleanup
    logger.info("Shutting down SmartBerth AI Service...")

    # Stop weather scheduler
    try:
        await stop_weather_scheduler()
        logger.info("Weather scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping weather scheduler: {e}")

    model.cleanup()
    logger.info("Cleanup complete")


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="SmartBerth AI Service",
    description="AI-powered berth planning and allocation optimization using Claude API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Unified Pipeline Router
if PIPELINE_AVAILABLE and pipeline_router:
    app.include_router(pipeline_router)
    logger.info("✓ Unified Pipeline API routes registered at /pipeline/*")


# ==================== HEALTH ENDPOINTS ====================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check service health status"""
    model = get_model()
    db = get_db_service()
    rag = get_rag_pipeline()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        model_status="loaded" if model._model_loaded else "not_loaded",
        database_status="connected" if db.test_connection() else "disconnected",
        rag_status="initialized" if rag._initialized else "not_initialized"
    )


# ==================== MODEL ENDPOINTS ====================

@app.get("/model/info", response_model=ModelInfo, tags=["Model"])
async def get_model_info():
    """Get model information and status"""
    model = get_model()
    info = model.get_model_info()
    return ModelInfo(**info)


@app.post("/model/load", tags=["Model"])
async def load_model(background_tasks: BackgroundTasks):
    """Load the AI model into GPU memory"""
    model = get_model()
    
    if model._model_loaded:
        return {"status": "already_loaded", "message": "Model is already loaded"}
    
    # Load in background to not block
    def load():
        success = model.initialize()
        if success:
            logger.info("Model loaded successfully via API")
        else:
            logger.error("Model loading failed")
    
    background_tasks.add_task(load)
    return {"status": "loading", "message": "Model loading started in background"}


@app.post("/model/unload", tags=["Model"])
async def unload_model():
    """Unload the AI model from GPU memory"""
    model = get_model()
    model.cleanup()
    return {"status": "unloaded", "message": "Model unloaded and GPU memory cleared"}


@app.post("/model/generate", response_model=GenerationResponse, tags=["Model"])
async def generate_text(request: GenerationRequest):
    """Generate text using the AI model"""
    model = get_model()
    
    if not model._model_loaded:
        # Try to load model
        if not model.initialize():
            raise HTTPException(status_code=503, detail="Model not loaded and failed to initialize")
    
    result = model.generate_text(
        prompt=request.prompt,
        system_prompt=request.system_prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=request.top_p
    )
    
    return GenerationResponse(**result)


# ==================== PREDICTION ENDPOINTS ====================

@app.get("/predictions/eta/{vessel_id}", response_model=ETAPredictionResponse, tags=["Predictions"])
async def predict_eta(
    vessel_id: int,
    schedule_id: Optional[int] = Query(None, description="Optional schedule ID")
):
    """Predict ETA for a vessel"""
    predictor = get_eta_predictor()
    result = predictor.predict_eta(vessel_id, schedule_id)
    
    return ETAPredictionResponse(
        vessel_id=result.vessel_id,
        vessel_name=result.vessel_name,
        original_eta=result.original_eta.isoformat() if result.original_eta else None,
        predicted_eta=result.predicted_eta.isoformat() if result.predicted_eta else None,
        deviation_minutes=result.deviation_minutes,
        confidence_score=result.confidence_score,
        status=result.status,
        factors=result.factors,
        ai_explanation=result.ai_explanation
    )


@app.get("/predictions/eta/batch", tags=["Predictions"])
async def predict_eta_batch(
    vessel_ids: str = Query(..., description="Comma-separated vessel IDs")
):
    """Predict ETA for multiple vessels"""
    predictor = get_eta_predictor()
    ids = [int(x.strip()) for x in vessel_ids.split(",")]
    
    results = []
    for vid in ids:
        result = predictor.predict_eta(vid)
        results.append({
            "vessel_id": result.vessel_id,
            "vessel_name": result.vessel_name,
            "predicted_eta": result.predicted_eta.isoformat() if result.predicted_eta else None,
            "deviation_minutes": result.deviation_minutes,
            "confidence_score": result.confidence_score,
            "status": result.status
        })
    
    return {"predictions": results}


# ==================== ALLOCATION ENDPOINTS ====================

@app.get("/suggestions/berth/{vessel_id}", response_model=List[BerthSuggestionResponse], tags=["Allocation"])
async def get_berth_suggestions(
    vessel_id: int,
    preferred_eta: Optional[str] = Query(None, description="Preferred ETA in ISO format"),
    top_n: int = Query(5, ge=1, le=20, description="Number of suggestions to return")
):
    """Get ranked berth suggestions for a vessel"""
    allocator = get_berth_allocator()
    
    eta = None
    if preferred_eta:
        try:
            eta = datetime.fromisoformat(preferred_eta)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format for preferred_eta")
    
    suggestions = allocator.get_berth_suggestions(vessel_id, eta, top_n)
    
    if not suggestions:
        raise HTTPException(status_code=404, detail="No berth suggestions available")
    
    return [
        BerthSuggestionResponse(
            berth_id=s.berth_id,
            berth_name=s.berth_name,
            terminal_name=s.terminal_name,
            total_score=s.total_score,
            constraint_score=s.constraint_score,
            utilization_score=s.utilization_score,
            waiting_time_score=s.waiting_time_score,
            priority_score=s.priority_score,
            violations=s.violations,
            is_feasible=s.is_feasible,
            explanation=s.explanation
        )
        for s in suggestions
    ]


@app.post("/validate/constraints", response_model=ConstraintValidationResponse, tags=["Allocation"])
async def validate_constraints(request: ConstraintValidationRequest):
    """Validate berth allocation constraints"""
    validator = get_constraint_validator()
    db = get_db_service()
    
    vessel = db.get_vessel_by_id(request.vessel_id)
    if not vessel:
        raise HTTPException(status_code=404, detail="Vessel not found")
    
    berths = db.get_all_berths()
    berth = next((b for b in berths if b['BerthId'] == request.berth_id), None)
    if not berth:
        raise HTTPException(status_code=404, detail="Berth not found")
    
    eta = None
    if request.eta:
        try:
            eta = datetime.fromisoformat(request.eta)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format for eta")
    
    schedule = {'Priority': vessel.get('Priority', 2)}
    is_feasible, violations, priority_score = validator.validate_all_constraints(
        vessel, berth, schedule, eta
    )
    
    return ConstraintValidationResponse(
        is_feasible=is_feasible,
        violations=[
            {
                'constraint_name': v.constraint_name,
                'category': v.category.value,
                'type': v.constraint_type.value,
                'description': v.description,
                'severity': v.severity
            }
            for v in violations
        ],
        priority_score=priority_score
    )


# ==================== CHATBOT ENDPOINTS ====================

@app.post("/chat", response_model=ChatResponse, tags=["Chatbot"])
async def chat(request: ChatRequest):
    """Send a message to the SmartBerth AI chatbot"""
    chatbot = get_chatbot()
    
    response = chatbot.process_message(request.message)
    
    return ChatResponse(
        text=response.text,
        intent=response.intent.value,
        entities=response.entities,
        structured_data=response.structured_data,
        actions=response.actions,
        confidence=response.confidence
    )


@app.get("/chat/history", tags=["Chatbot"])
async def get_chat_history():
    """Get conversation history"""
    chatbot = get_chatbot()
    return {"history": chatbot.get_history()}


@app.post("/chat/clear", tags=["Chatbot"])
async def clear_chat_history():
    """Clear conversation history"""
    chatbot = get_chatbot()
    chatbot.clear_history()
    return {"status": "cleared"}


# ==================== RAG ENDPOINTS ====================

@app.post("/rag/explain", response_model=ExplanationResponse, tags=["RAG"])
async def generate_explanation(request: ExplanationRequest):
    """Generate an AI explanation using RAG"""
    rag = get_rag_pipeline()
    
    if not rag._initialized:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    result = rag.generate_explanation(
        query=request.query,
        context_category=request.context_category,
        additional_context=request.additional_context
    )
    
    return ExplanationResponse(**result)


@app.get("/rag/search", tags=["RAG"])
async def search_knowledge_base(
    query: str = Query(..., description="Search query"),
    k: int = Query(5, ge=1, le=20, description="Number of results"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Search the knowledge base"""
    rag = get_rag_pipeline()
    
    if not rag._initialized:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    results = rag.retrieve_context(query, k, category)
    return {"results": results}


@app.post("/rag/add-document", tags=["RAG"])
async def add_document(
    content: str = Query(..., description="Document content"),
    title: str = Query(..., description="Document title"),
    category: str = Query("general", description="Document category")
):
    """Add a document to the knowledge base"""
    rag = get_rag_pipeline()
    
    if not rag._initialized:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    success = rag.add_document(
        content=content,
        metadata={'title': title, 'category': category, 'source': 'api'}
    )
    
    return {"success": success}


# ==================== HYBRID RAG ENDPOINTS ====================

class HybridSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    method: str = Field(default="hybrid", description="Search method: vector, bm25, or hybrid")


@app.post("/rag/hybrid-search", tags=["RAG"])
async def hybrid_search(request: HybridSearchRequest):
    """
    Search knowledge base using hybrid retrieval (vector + BM25).
    Combines semantic similarity with keyword matching for better results.
    """
    try:
        retriever = get_retriever()
        results = retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            method=request.method
        )
        
        return {
            "success": True,
            "query": request.query,
            "method": request.method,
            "results": [
                {
                    "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                    "source": doc.source,
                    "category": doc.category,
                    "score": round(doc.score, 4),
                    "retrieval_method": doc.retrieval_method
                }
                for doc in results
            ],
            "total_results": len(results)
        }
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/hybrid-stats", tags=["RAG"])
async def get_hybrid_stats():
    """Get statistics about the hybrid retriever"""
    try:
        retriever = get_retriever()
        return retriever.get_collection_stats()
    except Exception as e:
        logger.error(f"Failed to get hybrid stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CLAUDE-POWERED AGENT ENDPOINTS ====================

class ClaudeETARequest(BaseModel):
    vessel_id: int
    include_rag_context: bool = Field(default=True, description="Include knowledge base context")


class ClaudeBerthRequest(BaseModel):
    vessel_id: int
    include_rag_context: bool = Field(default=True)
    time_horizon_hours: int = Field(default=48, ge=6, le=168)


class ClaudeConflictRequest(BaseModel):
    time_start: Optional[str] = None  # ISO format, defaults to now
    time_end: Optional[str] = None    # ISO format, defaults to +48h
    include_rag_context: bool = Field(default=True)


@app.post("/agents/claude/eta", tags=["Claude Agents"])
async def claude_predict_eta(request: ClaudeETARequest):
    """
    Get ETA prediction using Claude-powered agent with RAG context.
    Uses Anthropic Claude Opus 4 for intelligent reasoning.
    """
    try:
        agent = ClaudeETAAgent()
        
        # Get RAG context if requested
        rag_context = None
        if request.include_rag_context:
            retriever = get_retriever()
            db = get_db_service()
            vessel = db.get_vessel_by_id(request.vessel_id)
            vessel_name = vessel.get("VesselName", "") if vessel else ""
            
            rag_context = retriever.retrieve_for_context(
                f"ETA prediction vessel arrival {vessel_name} weather impact delays",
                top_k=5
            )
        
        result = agent.predict_eta(request.vessel_id, rag_context)
        return result
        
    except Exception as e:
        logger.error(f"Claude ETA prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/claude/berth", tags=["Claude Agents"])
async def claude_optimize_berth(request: ClaudeBerthRequest):
    """
    Get optimal berth allocation using Claude-powered agent with RAG context.
    Uses Anthropic Claude Opus 4 for constraint-aware optimization.
    """
    try:
        agent = ClaudeBerthAgent()
        
        # Get RAG context if requested
        rag_context = None
        if request.include_rag_context:
            retriever = get_retriever()
            db = get_db_service()
            vessel = db.get_vessel_by_id(request.vessel_id)
            vessel_type = vessel.get("VesselType", "") if vessel else ""
            
            rag_context = retriever.retrieve_for_context(
                f"berth allocation {vessel_type} terminal constraints requirements",
                top_k=5
            )
        
        result = agent.optimize_allocation(
            request.vessel_id,
            rag_context,
            request.time_horizon_hours
        )
        return result
        
    except Exception as e:
        logger.error(f"Claude berth optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/claude/conflicts", tags=["Claude Agents"])
async def claude_resolve_conflicts(request: ClaudeConflictRequest):
    """
    Detect and resolve scheduling conflicts using Claude-powered agent.
    Uses Anthropic Claude Opus 4 for intelligent conflict resolution.
    """
    try:
        from datetime import datetime, timedelta
        
        agent = ClaudeConflictAgent()
        
        # Parse time window
        time_start = datetime.fromisoformat(request.time_start) if request.time_start else datetime.now()
        time_end = datetime.fromisoformat(request.time_end) if request.time_end else datetime.now() + timedelta(hours=48)
        
        # Get RAG context if requested
        rag_context = None
        if request.include_rag_context:
            retriever = get_retriever()
            rag_context = retriever.retrieve_for_context(
                "conflict resolution scheduling overlap berth allocation priority",
                top_k=5
            )
        
        result = agent.resolve_all(time_start, time_end, rag_context)
        return result
        
    except Exception as e:
        logger.error(f"Claude conflict resolution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MULTI-AGENT SYSTEM ENDPOINTS ====================

@app.post("/agents/process-arrival", tags=["Agents"])
async def process_vessel_arrival(request: VesselArrivalProcessRequest):
    """
    Complete vessel arrival processing using multi-agent orchestration.
    Coordinates ETA prediction, berth optimization, resource scheduling, and conflict detection.
    """
    orchestrator = get_orchestrator_agent()
    result = orchestrator.process_vessel_arrival(request.vessel_id)
    
    if "error" in result and not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@app.get("/agents/eta/{vessel_id}", tags=["Agents"])
async def agent_predict_eta(vessel_id: int):
    """Get ETA prediction from the ETA Predictor Agent"""
    agent = get_eta_predictor_agent()
    result = agent.predict_eta(vessel_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@app.get("/agents/berth-suggestions/{vessel_id}", tags=["Agents"])
async def agent_get_berth_suggestions(
    vessel_id: int,
    top_k: int = Query(5, ge=1, le=20),
    eta: Optional[str] = Query(None, description="Override ETA in ISO format")
):
    """Get berth suggestions from the Berth Optimizer Agent"""
    agent = get_berth_optimizer_agent()
    suggestions = agent.get_berth_suggestions(vessel_id, top_k=top_k, eta_override=eta)
    
    if suggestions and "error" in suggestions[0]:
        raise HTTPException(status_code=400, detail=suggestions[0].get("error"))
    
    return {"suggestions": suggestions}


@app.post("/agents/optimize-schedule", tags=["Agents"])
async def agent_optimize_schedule(request: OptimizationRequest):
    """
    Run schedule optimization using the Berth Optimizer Agent.
    Supports greedy heuristics and genetic algorithm.
    """
    agent = get_berth_optimizer_agent()
    db = get_db_service()
    
    # Get scheduled vessels
    vessels = db.get_vessels_by_status('Scheduled')
    
    if not vessels:
        return {"message": "No scheduled vessels to optimize", "allocations": []}
    
    result = agent.optimize_schedule(
        vessels=vessels,
        time_horizon_hours=request.time_horizon_hours,
        algorithm=request.algorithm
    )
    
    return result


@app.get("/agents/conflicts", tags=["Agents"])
async def agent_detect_conflicts(
    hours: int = Query(48, ge=6, le=168, description="Time window in hours")
):
    """Detect scheduling conflicts using the Conflict Resolver Agent"""
    agent = get_conflict_resolver_agent()
    conflicts = agent.detect_conflicts(time_window_hours=hours)
    
    return {
        "time_window_hours": hours,
        "conflicts_found": len(conflicts),
        "conflicts": conflicts
    }


@app.post("/agents/resolve-conflict", tags=["Agents"])
async def agent_resolve_conflict(request: ConflictResolutionRequest):
    """Apply a resolution to a detected conflict"""
    agent = get_conflict_resolver_agent()
    result = agent.resolve_conflict(request.conflict_id, request.resolution_action)
    
    return result


# ==================== SIMULATION (WHAT-IF) ENDPOINTS ====================

@app.post("/simulation/what-if", tags=["Simulation"])
async def run_what_if_simulation(request: WhatIfScenarioRequest):
    """
    Run what-if simulation for impact analysis.
    
    Scenario Types:
    - delay: Simulate vessel delay impact
    - berth_closure: Simulate berth maintenance closure
    - surge: Simulate arrival surge capacity
    """
    orchestrator = get_orchestrator_agent()
    
    scenario = {
        "type": request.scenario_type,
        "vessel_id": request.vessel_id,
        "berth_id": request.berth_id,
        "delay_hours": request.delay_hours,
        "duration_hours": request.duration_hours,
        "additional_vessels": request.additional_vessels
    }
    
    result = orchestrator.run_what_if_simulation(scenario)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@app.get("/simulation/delay-impact/{vessel_id}", tags=["Simulation"])
async def simulate_delay_impact(
    vessel_id: int,
    delay_hours: int = Query(4, ge=1, le=48, description="Delay in hours")
):
    """Simulate the impact of a vessel delay on downstream operations"""
    orchestrator = get_orchestrator_agent()
    
    result = orchestrator.run_what_if_simulation({
        "type": "delay",
        "vessel_id": vessel_id,
        "delay_hours": delay_hours
    })
    
    return result


@app.get("/simulation/berth-closure/{berth_id}", tags=["Simulation"])
async def simulate_berth_closure(
    berth_id: int,
    duration_hours: int = Query(24, ge=1, le=168, description="Closure duration in hours")
):
    """Simulate the impact of berth closure for maintenance"""
    orchestrator = get_orchestrator_agent()
    
    result = orchestrator.run_what_if_simulation({
        "type": "berth_closure",
        "berth_id": berth_id,
        "duration_hours": duration_hours
    })
    
    return result


@app.get("/simulation/capacity-surge", tags=["Simulation"])
async def simulate_capacity_surge(
    additional_vessels: int = Query(5, ge=1, le=20, description="Number of additional vessels")
):
    """Simulate port capacity under arrival surge conditions"""
    orchestrator = get_orchestrator_agent()
    
    result = orchestrator.run_what_if_simulation({
        "type": "surge",
        "additional_vessels": additional_vessels
    })
    
    return result


# ==================== ALERT SERVICE & MONITORING ENDPOINTS ====================

# Global WebSockets list for alert broadcasting
_alert_websockets: List[WebSocket] = []


async def broadcast_alert_to_websockets(alert_data: dict):
    """Broadcast an alert to all connected WebSocket clients"""
    if not _alert_websockets:
        return
    
    message = json.dumps({
        "type": "alert",
        "data": alert_data,
        "timestamp": datetime.now().isoformat()
    })
    
    for ws in list(_alert_websockets):
        try:
            await ws.send_text(message)
        except Exception as e:
            logger.warning(f"Failed to send alert to WebSocket: {e}")
            try:
                _alert_websockets.remove(ws)
            except:
                pass


@app.get("/monitoring/activity-feed", tags=["Monitoring & Alerts"])
async def get_activity_feed(
    limit: int = Query(50, ge=1, le=200),
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    include_read: bool = Query(True)
):
    """
    Get the activity feed with explainable insights.
    Each activity includes LLM-generated reasoning and dynamic confidence scores.
    """
    if not ALERT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    service = get_alert_service()
    
    cat_filter = AlertCategory(category) if category else None
    sev_filter = AlertSeverity(severity) if severity else None
    
    activities = service.get_activity_feed(
        limit=limit,
        category=cat_filter,
        severity=sev_filter,
        include_read=include_read
    )
    
    unread = service.get_unread_count()
    
    return ActivityFeedResponse(
        activities=activities,
        total_count=len(activities),
        unread_counts=unread
    )


@app.get("/monitoring/activity/{activity_id}", tags=["Monitoring & Alerts"])
async def get_activity_detail(activity_id: str):
    """Get detailed information about a specific activity including full explanation"""
    if not ALERT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    service = get_alert_service()
    activity = service.get_activity_by_id(activity_id)
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    return activity


@app.post("/monitoring/activity/{activity_id}/read", tags=["Monitoring & Alerts"])
async def mark_activity_read(activity_id: str):
    """Mark an activity as read"""
    if not ALERT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    service = get_alert_service()
    success = service.mark_as_read(activity_id)
    
    return {"success": success, "activity_id": activity_id}


@app.post("/monitoring/alerts", tags=["Monitoring & Alerts"])
async def create_alert(request: CreateAlertRequest):
    """
    Create a new alert with LLM-generated explanation.
    The system will automatically:
    - Generate an AI explanation for the alert
    - Calculate dynamic confidence based on data quality
    - Broadcast to connected WebSocket clients
    - Persist to database
    """
    if not ALERT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    service = get_alert_service()
    
    try:
        category = AlertCategory(request.category)
        alert_type = AlertType(request.alert_type)
        severity = AlertSeverity(request.severity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {e}")
    
    # Calculate confidence based on context
    confidence_factors = ConfidenceFactors()
    if request.context.get('data_freshness'):
        confidence_factors.data_freshness = request.context['data_freshness']
    
    entry = await service.create_alert(
        category=category,
        alert_type=alert_type,
        severity=severity,
        title=request.title,
        message=request.message,
        context=request.context,
        affected_entities={
            "vessels": request.affected_vessels,
            "berths": request.affected_berths,
            "schedules": []
        },
        confidence_factors=confidence_factors
    )
    
    # Broadcast to WebSocket clients
    await broadcast_alert_to_websockets(entry.to_dict())
    
    return entry.to_dict()


@app.post("/monitoring/start", tags=["Monitoring & Alerts"])
async def start_monitoring(
    interval_seconds: int = Query(30, ge=10, le=300, description="Monitoring interval in seconds")
):
    """
    Start the agentic monitoring system.
    The system will continuously watch for:
    - ETA changes and delays
    - Scheduling conflicts
    - Berth availability changes
    - Weather impacts
    - Optimization opportunities
    
    Each detected event generates an alert with LLM-powered explanation.
    """
    if not ALERT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    service = get_alert_service()
    await service.start_monitoring(interval_seconds)
    
    return {
        "status": "monitoring_started",
        "interval_seconds": interval_seconds,
        "message": "Agentic monitoring is now active"
    }


@app.post("/monitoring/stop", tags=["Monitoring & Alerts"])
async def stop_monitoring():
    """Stop the agentic monitoring system"""
    if not ALERT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    service = get_alert_service()
    await service.stop_monitoring()
    
    return {"status": "monitoring_stopped"}


@app.get("/monitoring/status", tags=["Monitoring & Alerts"])
async def get_monitoring_status():
    """Get the current status of the monitoring system"""
    if not ALERT_SERVICE_AVAILABLE:
        return MonitoringStatusResponse(
            is_active=False,
            interval_seconds=0,
            last_check=None,
            alerts_generated_today=0
        )
    
    service = get_alert_service()
    
    # Count today's alerts
    today_count = sum(
        1 for a in service.activity_feed
        if a.timestamp.date() == datetime.utcnow().date()
    )
    
    return MonitoringStatusResponse(
        is_active=service._monitoring_active,
        interval_seconds=30,  # Default
        last_check=service.activity_feed[0].timestamp.isoformat() if service.activity_feed else None,
        alerts_generated_today=today_count
    )


@app.get("/monitoring/confidence/{entity_type}/{entity_id}", tags=["Monitoring & Alerts"])
async def get_confidence_breakdown(
    entity_type: str,
    entity_id: int
):
    """
    Get detailed confidence score breakdown for an entity.
    This shows exactly WHY a confidence score has a particular value.
    """
    if not ALERT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Alert service not available")
    
    service = get_alert_service()
    db = get_db_service()
    
    if entity_type == "vessel":
        # Get vessel position data from AIS_DATA table
        query = f"""
        SELECT TOP 1 Latitude, Longitude, Speed, Course, Heading, RecordedAt as timestamp, 'AIS' as source 
        FROM AIS_DATA 
        WHERE VesselId = {entity_id} 
        ORDER BY RecordedAt DESC
        """
        position = db.execute_query(query)
        
        if position:
            factors = service.calculate_eta_confidence(
                entity_id,
                position[0] if position else {},
                None
            )
        else:
            factors = ConfidenceFactors()
        
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "confidence_score": factors.calculate_score(),
            "factors": {
                "data_freshness": {
                    "value": factors.data_freshness,
                    "weight": 0.20,
                    "contribution": factors.data_freshness * 0.20 * 100
                },
                "historical_accuracy": {
                    "value": factors.historical_accuracy,
                    "weight": 0.25,
                    "contribution": factors.historical_accuracy * 0.25 * 100
                },
                "data_completeness": {
                    "value": factors.data_completeness,
                    "weight": 0.15,
                    "contribution": factors.data_completeness * 0.15 * 100
                },
                "source_reliability": {
                    "value": factors.source_reliability,
                    "weight": 0.15,
                    "contribution": factors.source_reliability * 0.15 * 100
                },
                "weather_certainty": {
                    "value": factors.weather_certainty,
                    "weight": 0.10,
                    "contribution": factors.weather_certainty * 0.10 * 100
                },
                "constraint_satisfaction": {
                    "value": factors.constraint_satisfaction,
                    "weight": 0.15,
                    "contribution": factors.constraint_satisfaction * 0.15 * 100
                }
            },
            "explanation": factors.get_explanation()
        }
    
    elif entity_type == "berth":
        factors = service.calculate_berth_confidence(
            entity_id,
            vessel_id=0,
            constraints_checked=5,
            constraints_passed=5,
            availability_horizon_hours=24
        )
        
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "confidence_score": factors.calculate_score(),
            "factors": {
                "constraint_satisfaction": factors.constraint_satisfaction,
                "data_freshness": factors.data_freshness,
                "data_completeness": factors.data_completeness
            },
            "explanation": factors.get_explanation()
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown entity type: {entity_type}")


@app.websocket("/monitoring/ws")
async def monitoring_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert streaming.
    Clients will receive alerts as they are generated by the monitoring system.
    """
    await websocket.accept()
    _alert_websockets.append(websocket)
    
    logger.info(f"Alert WebSocket connected. Total clients: {len(_alert_websockets)}")
    
    # Register as subscriber to alert service
    if ALERT_SERVICE_AVAILABLE:
        service = get_alert_service()
        
        async def on_alert(entry: ActivityEntry):
            try:
                await websocket.send_text(json.dumps({
                    "type": "new_alert",
                    "alert": entry.to_dict()
                }))
            except:
                pass
        
        service.subscribe(on_alert)
    
    # Send initial status
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": "Real-time alert monitoring connected",
        "timestamp": datetime.now().isoformat()
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
                elif message.get("type") == "get_feed":
                    if ALERT_SERVICE_AVAILABLE:
                        service = get_alert_service()
                        feed = service.get_activity_feed(limit=20)
                        await websocket.send_text(json.dumps({
                            "type": "feed",
                            "activities": feed
                        }))
                
                elif message.get("type") == "mark_read":
                    if ALERT_SERVICE_AVAILABLE:
                        service = get_alert_service()
                        service.mark_as_read(message.get("activity_id"))
                        await websocket.send_text(json.dumps({
                            "type": "marked_read",
                            "activity_id": message.get("activity_id")
                        }))
                        
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        _alert_websockets.remove(websocket)
        logger.info(f"Alert WebSocket disconnected. Total clients: {len(_alert_websockets)}")


# ==================== SCHEDULE CHANGE NOTIFICATION ENDPOINTS ====================

class ScheduleChangeEvent(BaseModel):
    """Model for schedule change events from frontend"""
    event_type: str  # 'berth_allocation', 'eta_update', 'arrival', 'berthing', 'departure'
    vessel_id: int
    vessel_name: Optional[str] = None
    berth_id: Optional[int] = None
    berth_name: Optional[str] = None
    previous_value: Optional[str] = None  # For updates (e.g., old ETA)
    new_value: Optional[str] = None  # For updates (e.g., new ETA)
    performed_by: Optional[str] = "System"
    additional_context: Optional[Dict[str, Any]] = None


async def broadcast_to_websockets(message: Dict):
    """Broadcast message to all connected WebSocket clients"""
    disconnected = []
    for ws in _alert_websockets:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            disconnected.append(ws)
    
    # Cleanup disconnected clients
    for ws in disconnected:
        if ws in _alert_websockets:
            _alert_websockets.remove(ws)


@app.post("/monitoring/notify/schedule-change", tags=["Notifications"])
async def notify_schedule_change(event: ScheduleChangeEvent):
    """
    Notify stakeholders about schedule changes.
    Called by frontend after successful CRUD operations.
    Generates LLM-powered explanations and broadcasts alerts.
    """
    db = get_db_service()
    
    try:
        # Gather context for better explanations
        vessel_details = None
        berth_details = None
        
        if event.vessel_id:
            vessels = db.get_all_vessels()
            vessel_details = next((v for v in vessels if v.get('VesselId') == event.vessel_id), None)
        
        if event.berth_id:
            berths = db.get_all_berths()
            berth_details = next((b for b in berths if b.get('BerthId') == event.berth_id), None)
        
        # Determine alert type and create entry
        alert_type_map = {
            'berth_allocation': AlertType.BERTH_ASSIGNED,
            'eta_update': AlertType.ETA_UPDATED,
            'arrival': AlertType.VESSEL_ENTERED_ZONE,
            'berthing': AlertType.BERTH_ASSIGNED,
            'departure': AlertType.BERTH_AVAILABILITY_CHANGE
        }
        
        alert_type = alert_type_map.get(event.event_type, AlertType.BERTH_ASSIGNED)
        
        # Generate LLM-powered explanation if available
        explanation = None
        if ALERT_SERVICE_AVAILABLE:
            service = get_alert_service()
            
            # Build event description for LLM
            event_descriptions = {
                'berth_allocation': f"Vessel {event.vessel_name or event.vessel_id} has been allocated to berth {event.berth_name or event.berth_id}",
                'eta_update': f"ETA for vessel {event.vessel_name or event.vessel_id} changed from {event.previous_value} to {event.new_value}",
                'arrival': f"Vessel {event.vessel_name or event.vessel_id} has arrived at port",
                'berthing': f"Vessel {event.vessel_name or event.vessel_id} has begun berthing at {event.berth_name or event.berth_id}",
                'departure': f"Vessel {event.vessel_name or event.vessel_id} has departed from berth {event.berth_name or event.berth_id}"
            }
            
            event_description = event_descriptions.get(event.event_type, f"Schedule event: {event.event_type}")
            
            # Create an activity entry for generating explanation
            category_map = {
                'berth_allocation': AlertCategory.BERTH_ALLOCATION,
                'eta_update': AlertCategory.ETA_PREDICTION,
                'arrival': AlertCategory.VESSEL_TRACKING,
                'berthing': AlertCategory.BERTH_ALLOCATION,
                'departure': AlertCategory.VESSEL_TRACKING
            }
            
            temp_confidence_factors = ConfidenceFactors()
            temp_context = {
                "event_type": event.event_type,
                "vessel_id": event.vessel_id,
                "vessel_name": event.vessel_name or (vessel_details.get('VesselName') if vessel_details else f"Vessel {event.vessel_id}"),
                "berth_id": event.berth_id,
                "berth_name": event.berth_name or (berth_details.get('BerthName') if berth_details else None),
                "description": event_description,
                "previous_value": event.previous_value,
                "new_value": event.new_value,
                "performed_by": event.performed_by,
                "additional_context": event.additional_context or {}
            }
            
            explanation = await service.generate_alert_explanation(
                alert_type=alert_type,
                context=temp_context,
                confidence_factors=temp_confidence_factors
            )
        
        # Determine stakeholders to notify based on event type
        stakeholders = _get_stakeholders_for_event(event, vessel_details, berth_details)
        
        # Build activity entry
        activity_entry = {
            "id": f"schedule_{event.event_type}_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "alert_type": alert_type.value,
            "severity": "low" if event.event_type == 'departure' else "medium",
            "title": _get_event_title(event, vessel_details, berth_details),
            "description": _get_event_description(event, vessel_details, berth_details),
            "entity_type": "vessel",
            "entity_id": str(event.vessel_id),
            "entity_name": event.vessel_name or (vessel_details.get('VesselName') if vessel_details else f"Vessel {event.vessel_id}"),
            "confidence_score": 0.95,
            "factors": {},
            "predicted_impact": _get_event_impact(event),
            "recommended_actions": _get_event_actions(event, vessel_details, berth_details),
            "explanation": explanation,
            "stakeholders": stakeholders,
            "performed_by": event.performed_by,
            "is_read": False
        }
        
        # Save to database for persistence
        try:
            insert_query = """
            INSERT INTO ALERTS_NOTIFICATIONS 
            (AlertType, Severity, Title, Message, VesselId, BerthId, CreatedAt, IsRead, Explanation)
            VALUES (?, ?, ?, ?, ?, ?, GETDATE(), 0, ?)
            """
            db.execute_query(insert_query, (
                alert_type.value,
                activity_entry['severity'],
                activity_entry['title'],
                activity_entry['description'],
                event.vessel_id,
                event.berth_id,
                explanation
            ))
        except Exception as e:
            logger.warning(f"Could not save notification to DB: {e}")
        
        # Broadcast to WebSocket clients
        await broadcast_to_websockets({
            "type": "schedule_change",
            "alert": activity_entry
        })
        
        # Also add to alert service feed if available
        if ALERT_SERVICE_AVAILABLE:
            service = get_alert_service()
            category_map = {
                'berth_allocation': AlertCategory.BERTH_ALLOCATION,
                'eta_update': AlertCategory.ETA_PREDICTION,
                'arrival': AlertCategory.VESSEL_TRACKING,
                'berthing': AlertCategory.BERTH_ALLOCATION,
                'departure': AlertCategory.VESSEL_TRACKING
            }
            entry = ActivityEntry(
                id=activity_entry['id'],
                timestamp=datetime.now(),
                category=category_map.get(event.event_type, AlertCategory.SYSTEM),
                alert_type=alert_type,
                severity=AlertSeverity.INFO if event.event_type == 'departure' else AlertSeverity.WARNING,
                title=activity_entry['title'],
                message=activity_entry['description'],
                explanation=explanation,
                confidence_score=0.95,
                confidence_factors=ConfidenceFactors(),
                affected_entities={"vessels": [event.vessel_id], "berths": [event.berth_id] if event.berth_id else []},
                metadata=event.additional_context or {},
                is_read=False,
                is_actionable=True,
                recommended_actions=activity_entry['recommended_actions']
            )
            service.activity_feed.insert(0, entry)
            if len(service.activity_feed) > 100:
                service.activity_feed = service.activity_feed[:100]
        
        logger.info(f"Schedule change notification sent: {event.event_type} for vessel {event.vessel_id}")
        
        return {
            "success": True,
            "notification_id": activity_entry['id'],
            "stakeholders_notified": stakeholders,
            "explanation": explanation,
            "message": f"Notification sent for {event.event_type}"
        }
        
    except Exception as e:
        logger.error(f"Error sending schedule change notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_stakeholders_for_event(event: ScheduleChangeEvent, vessel_details: Dict, berth_details: Dict) -> List[str]:
    """Determine which stakeholders should be notified for an event"""
    stakeholders = ["Port Operations"]
    
    if event.event_type in ['berth_allocation', 'berthing']:
        stakeholders.extend(["Berth Manager", "Terminal Operator"])
        if berth_details:
            stakeholders.append(f"Berth {berth_details.get('BerthName', '')} Supervisor")
    
    if event.event_type in ['arrival', 'departure']:
        stakeholders.extend(["Harbor Master", "Pilot Service"])
        if vessel_details:
            agent = vessel_details.get('ShippingAgent')
            if agent:
                stakeholders.append(f"Agent: {agent}")
    
    if event.event_type == 'eta_update':
        stakeholders.extend(["Planning Team", "Resource Coordinator"])
    
    return list(set(stakeholders))  # Remove duplicates


def _get_event_title(event: ScheduleChangeEvent, vessel_details: Dict, berth_details: Dict) -> str:
    """Generate a descriptive title for the event"""
    vessel_name = event.vessel_name or (vessel_details.get('VesselName') if vessel_details else f"Vessel {event.vessel_id}")
    berth_name = event.berth_name or (berth_details.get('BerthName') if berth_details else f"Berth {event.berth_id}")
    
    titles = {
        'berth_allocation': f"🚢 Berth Allocated: {vessel_name} → {berth_name}",
        'eta_update': f"⏱️ ETA Updated: {vessel_name}",
        'arrival': f"✅ Vessel Arrived: {vessel_name}",
        'berthing': f"⚓ Berthing Started: {vessel_name} at {berth_name}",
        'departure': f"🚀 Vessel Departed: {vessel_name} from {berth_name}"
    }
    
    return titles.get(event.event_type, f"Schedule Update: {vessel_name}")


def _get_event_description(event: ScheduleChangeEvent, vessel_details: Dict, berth_details: Dict) -> str:
    """Generate detailed description for the event"""
    vessel_name = event.vessel_name or (vessel_details.get('VesselName') if vessel_details else f"Vessel {event.vessel_id}")
    berth_name = event.berth_name or (berth_details.get('BerthName') if berth_details else f"Berth {event.berth_id}")
    
    if event.event_type == 'berth_allocation':
        desc = f"Vessel '{vessel_name}' has been allocated to {berth_name}."
        if vessel_details:
            desc += f" Vessel type: {vessel_details.get('VesselType', 'Unknown')}, LOA: {vessel_details.get('LOA', 'N/A')}m."
        if berth_details:
            desc += f" Berth max capacity: {berth_details.get('MaxVesselLength', 'N/A')}m."
    
    elif event.event_type == 'eta_update':
        desc = f"ETA for vessel '{vessel_name}' has been updated from {event.previous_value} to {event.new_value}."
        if event.additional_context:
            reason = event.additional_context.get('reason')
            if reason:
                desc += f" Reason: {reason}."
    
    elif event.event_type == 'arrival':
        desc = f"Vessel '{vessel_name}' has arrived at port and is awaiting berth assignment."
        if vessel_details:
            desc += f" Cargo type: {vessel_details.get('CargoType', 'General')}."
    
    elif event.event_type == 'berthing':
        desc = f"Vessel '{vessel_name}' has commenced berthing operations at {berth_name}."
        if vessel_details and berth_details:
            desc += f" Expected operations duration based on cargo: {vessel_details.get('CargoVolume', 'N/A')} tons."
    
    elif event.event_type == 'departure':
        desc = f"Vessel '{vessel_name}' has completed operations and departed from {berth_name}."
        desc += f" Berth is now available for the next vessel."
    
    else:
        desc = f"Schedule event '{event.event_type}' occurred for vessel '{vessel_name}'."
    
    return desc


def _get_event_impact(event: ScheduleChangeEvent) -> Dict:
    """Determine the predicted impact of the event"""
    impacts = {
        'berth_allocation': {
            "type": "resource_utilization",
            "description": "Berth capacity allocated, reducing available slots for incoming vessels",
            "affected_systems": ["Berth Schedule", "Resource Planning", "Cargo Handling"]
        },
        'eta_update': {
            "type": "schedule_adjustment",
            "description": "May require downstream schedule adjustments for berth and resource planning",
            "affected_systems": ["Berth Schedule", "Pilot Service", "Tug Service", "Cargo Operations"]
        },
        'arrival': {
            "type": "operational_trigger",
            "description": "Triggers arrival procedures including documentation, customs, and berth preparation",
            "affected_systems": ["Port Authority", "Customs", "Berth Operations", "Pilot Service"]
        },
        'berthing': {
            "type": "operations_start",
            "description": "Cargo operations begin, resources committed to this vessel",
            "affected_systems": ["Cargo Handling", "Terminal Operations", "Equipment Allocation"]
        },
        'departure': {
            "type": "resource_release",
            "description": "Berth becomes available, resources freed for next vessel",
            "affected_systems": ["Berth Schedule", "Resource Pool", "Next Vessel Queue"]
        }
    }
    
    return impacts.get(event.event_type, {"type": "unknown", "description": "Schedule change processed"})


def _get_event_actions(event: ScheduleChangeEvent, vessel_details: Dict, berth_details: Dict) -> List[str]:
    """Generate recommended follow-up actions for the event"""
    actions = {
        'berth_allocation': [
            "Confirm berth preparation status",
            "Notify cargo handling team",
            "Verify pilot and tug availability",
            "Update vessel with berthing instructions"
        ],
        'eta_update': [
            "Review and adjust berth schedule if needed",
            "Notify affected stakeholders of timing change",
            "Re-confirm resource availability",
            "Update downstream operations timeline"
        ],
        'arrival': [
            "Initiate port entry procedures",
            "Assign pilot for berthing",
            "Confirm berth readiness",
            "Prepare documentation for customs clearance"
        ],
        'berthing': [
            "Deploy cargo handling equipment",
            "Begin cargo operations checklist",
            "Monitor berthing completion",
            "Update status in tracking systems"
        ],
        'departure': [
            "Confirm vessel departure clearance",
            "Update berth availability status",
            "Process port departure documentation",
            "Trigger billing and invoicing"
        ]
    }
    
    return actions.get(event.event_type, ["Review and acknowledge notification"])


@app.post("/monitoring/notify/bulk", tags=["Notifications"])
async def notify_bulk_changes(events: List[ScheduleChangeEvent]):
    """
    Send notifications for multiple schedule changes at once.
    Useful for batch updates or system synchronization.
    """
    results = []
    for event in events:
        try:
            result = await notify_schedule_change(event)
            results.append({"event": event.event_type, "vessel_id": event.vessel_id, "success": True})
        except Exception as e:
            results.append({"event": event.event_type, "vessel_id": event.vessel_id, "success": False, "error": str(e)})
    
    return {
        "total": len(events),
        "successful": sum(1 for r in results if r.get('success')),
        "failed": sum(1 for r in results if not r.get('success')),
        "results": results
    }


@app.get("/monitoring/stakeholders/{vessel_id}", tags=["Notifications"])
async def get_stakeholders_for_vessel(vessel_id: int):
    """
    Get the list of stakeholders associated with a vessel.
    Used for targeted notifications.
    """
    db = get_db_service()
    
    try:
        vessels = db.get_all_vessels()
        vessel = next((v for v in vessels if v.get('VesselId') == vessel_id), None)
        
        if not vessel:
            raise HTTPException(status_code=404, detail=f"Vessel {vessel_id} not found")
        
        # Get current berth assignment if any
        schedules = db.execute_query(f"""
            SELECT BerthId FROM VESSEL_SCHEDULE 
            WHERE VesselId = {vessel_id} AND Status IN ('Scheduled', 'Berthed')
        """)
        
        berth_id = schedules[0].get('BerthId') if schedules else None
        berth_details = None
        if berth_id:
            berths = db.get_all_berths()
            berth_details = next((b for b in berths if b.get('BerthId') == berth_id), None)
        
        stakeholders = {
            "vessel_id": vessel_id,
            "vessel_name": vessel.get('VesselName'),
            "primary_stakeholders": [
                {"role": "Shipping Agent", "name": vessel.get('ShippingAgent', 'Not Assigned')},
                {"role": "Port Operations", "name": "Port Control Center"},
                {"role": "Harbor Master", "name": "Harbor Master Office"}
            ],
            "operational_stakeholders": [
                {"role": "Pilot Service", "name": "Marine Pilot Services"},
                {"role": "Tug Service", "name": "Harbor Tug Operations"}
            ]
        }
        
        if berth_details:
            stakeholders["berth_stakeholders"] = [
                {"role": "Terminal Operator", "name": berth_details.get('TerminalName', 'Terminal Ops')},
                {"role": "Berth Manager", "name": f"Berth {berth_details.get('BerthName', '')} Manager"}
            ]
        
        return stakeholders
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stakeholders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DASHBOARD & ANALYTICS ENDPOINTS ====================

@app.get("/dashboard/overview", tags=["Dashboard"])
async def get_dashboard_overview():
    """Get dashboard overview with key metrics including AI service status"""
    db = get_db_service()
    
    try:
        vessels_scheduled = db.get_vessels_by_status('Scheduled')
        vessels_at_berth = db.get_vessels_by_status('Berthed')
        berths = db.get_all_berths()
        active_berths = [b for b in berths if b.get('IsActive')]
        conflicts = db.get_active_conflicts()
        
        # Calculate utilization
        occupied_berths = len(vessels_at_berth)
        total_berths = len(active_berths)
        utilization = (occupied_berths / total_berths * 100) if total_berths > 0 else 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "aiServiceStatus": "active",  # AI service is running
            "metrics": {
                "vessels_in_queue": len(vessels_scheduled),
                "vessels_at_berth": len(vessels_at_berth),
                "total_berths": total_berths,
                "berth_utilization_percent": round(utilization, 1),
                "active_conflicts": len(conflicts) if conflicts else 0
            },
            "vesselStatus": {
                "scheduled": len(vessels_scheduled),
                "berthed": len(vessels_at_berth),
                "approaching": 0
            },
            "vessels_scheduled": vessels_scheduled[:10],  # Top 10
            "vessels_at_berth": vessels_at_berth[:10]
        }
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "aiServiceStatus": "active",  # Service is running but had error fetching data
            "error": str(e),
            "metrics": {}
        }


@app.get("/dashboard/timeline", tags=["Dashboard"])
async def get_berth_timeline(
    hours: int = Query(48, ge=6, le=168, description="Time window in hours")
):
    """Get berth timeline for visualization"""
    db = get_db_service()
    
    try:
        start = datetime.now()
        end = start + timedelta(hours=hours)
        
        schedules = db.get_schedules_in_range(start.isoformat(), end.isoformat())
        berths = db.get_all_berths()
        
        # Group schedules by berth
        timeline = {}
        for berth in berths:
            berth_id = berth.get('BerthId')
            berth_schedules = [s for s in schedules if s.get('BerthId') == berth_id]
            timeline[berth.get('BerthName', f'Berth {berth_id}')] = {
                "berth_id": berth_id,
                "terminal": berth.get('TerminalName'),
                "occupancy": berth_schedules
            }
        
        return {
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "timeline": timeline
        }
    except Exception as e:
        logger.error(f"Timeline error: {e}")
        return {"error": str(e)}


# ==================== DATABASE ENDPOINTS ====================

@app.get("/db/vessels", tags=["Database"])
async def get_vessels():
    """Get all vessels from database"""
    db = get_db_service()
    return {"vessels": db.get_all_vessels()}


@app.get("/db/berths", tags=["Database"])
async def get_berths():
    """Get all berths from database"""
    db = get_db_service()
    return {"berths": db.get_all_berths()}


@app.get("/db/schedules/active", tags=["Database"])
async def get_active_schedules():
    """Get active vessel schedules"""
    db = get_db_service()
    return {"schedules": db.get_active_schedules()}


@app.get("/db/weather", tags=["Database"])
async def get_weather():
    """Get current weather conditions"""
    db = get_db_service()
    weather = db.get_current_weather()
    if not weather:
        raise HTTPException(status_code=404, detail="No weather data available")
    return weather


@app.get("/db/conflicts", tags=["Database"])
async def get_conflicts():
    """Get active conflicts"""
    db = get_db_service()
    return {"conflicts": db.get_active_conflicts()}


# ==================== ENHANCED ML ENDPOINTS ====================

@app.get("/ml/comprehensive-prediction/{vessel_id}", tags=["ML Predictions"])
async def get_comprehensive_prediction(
    vessel_id: int,
    include_berth_suggestions: bool = Query(True, description="Include berth recommendations"),
    include_ukc: bool = Query(True, description="Include UKC safety analysis"),
    include_anomaly_check: bool = Query(True, description="Include anomaly detection")
):
    """
    Get comprehensive AI-powered predictions for a vessel.
    
    Combines:
    - Feature Engineering (Temporal, Spatial, Vessel, Weather, UKC features)
    - ML Models (Hybrid ETA, Dwell Time, Anomaly Detection, Berth Scoring)
    - Natural Language Explanations via LLM
    
    Returns a complete analysis including ETA, dwell time, UKC safety,
    anomaly status, berth recommendations, and AI explanation.
    """
    prediction_service = get_prediction_service()
    
    try:
        prediction = prediction_service.get_comprehensive_prediction(
            vessel_id=vessel_id,
            include_berth_suggestions=include_berth_suggestions,
            include_ukc=include_ukc,
            include_anomaly_check=include_anomaly_check
        )
        
        return {
            "vessel_id": prediction.vessel_id,
            "vessel_name": prediction.vessel_name,
            "eta_prediction": prediction.eta_prediction,
            "dwell_prediction": prediction.dwell_prediction,
            "ukc_analysis": prediction.ukc_analysis,
            "anomaly_status": prediction.anomaly_status,
            "berth_recommendations": prediction.berth_recommendations,
            "resource_requirements": prediction.resource_requirements,
            "ai_explanation": prediction.ai_explanation,
            "overall_confidence": prediction.overall_confidence,
            "processing_time_ms": prediction.processing_time_ms,
            "models_used": prediction.models_used
        }
    except Exception as e:
        logger.error(f"Comprehensive prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml/optimize-schedule", tags=["ML Optimization"])
async def ml_optimize_schedule(
    vessel_ids: Optional[str] = Query(None, description="Comma-separated vessel IDs (optional)"),
    time_horizon_hours: int = Query(48, ge=6, le=168),
    objective: str = Query("balanced", description="Objective: balanced, waiting_time, utilization, conflicts"),
    use_genetic_algorithm: bool = Query(False, description="Use genetic algorithm (slower but better)")
):
    """
    Optimize berth schedule using ML and heuristics.
    
    Algorithms available:
    - Priority-Based (fast, greedy)
    - Genetic Algorithm (slower, global optimization)
    
    Objectives:
    - balanced: Weighted combination of all factors
    - waiting_time: Minimize total vessel waiting time
    - utilization: Maximize berth utilization
    - conflicts: Minimize scheduling conflicts
    """
    optimization_service = get_optimization_service()
    
    vessel_id_list = None
    if vessel_ids:
        vessel_id_list = [int(x.strip()) for x in vessel_ids.split(",")]
    
    try:
        result = optimization_service.optimize_schedule(
            vessel_ids=vessel_id_list,
            time_horizon_hours=time_horizon_hours,
            objective=objective,
            use_genetic_algorithm=use_genetic_algorithm
        )
        
        return {
            "success": result.success,
            "solution": result.solution,
            "conflicts": result.conflicts,
            "cascading_effects": result.cascading_effects,
            "optimization_score": result.optimization_score,
            "execution_time_ms": result.execution_time_ms,
            "algorithm_used": result.algorithm_used,
            "ai_explanation": result.ai_explanation
        }
    except Exception as e:
        logger.error(f"Schedule optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml/handle-delay", tags=["ML Optimization"])
async def ml_handle_vessel_delay(
    vessel_id: int = Query(..., description="Delayed vessel ID"),
    new_eta: str = Query(..., description="New ETA in ISO format")
):
    """
    Re-optimize schedule after a vessel delay.
    
    Analyzes cascading effects and generates a new optimized schedule
    with minimal disruption to other vessels.
    """
    optimization_service = get_optimization_service()
    
    try:
        eta_datetime = datetime.fromisoformat(new_eta.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format for new_eta")
    
    try:
        result = optimization_service.handle_vessel_delay(vessel_id, eta_datetime)
        
        return {
            "success": result.success,
            "solution": result.solution,
            "conflicts": result.conflicts,
            "cascading_effects": result.cascading_effects,
            "optimization_score": result.optimization_score,
            "execution_time_ms": result.execution_time_ms,
            "algorithm_used": result.algorithm_used,
            "ai_explanation": result.ai_explanation
        }
    except Exception as e:
        logger.error(f"Delay handling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/assign-resources/{vessel_id}", tags=["ML Optimization"])
async def ml_assign_resources(
    vessel_id: int,
    eta: str = Query(..., description="Expected arrival time in ISO format")
):
    """
    Optimal resource (pilot/tug) assignment using Hungarian algorithm.
    
    Returns the optimal assignment of pilots and tugboats for the vessel
    based on requirements, availability, and constraints.
    """
    optimization_service = get_optimization_service()
    
    try:
        eta_datetime = datetime.fromisoformat(eta.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format for eta")
    
    try:
        result = optimization_service.assign_resources(vessel_id, eta_datetime)
        return result
    except Exception as e:
        logger.error(f"Resource assignment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/traffic-forecast", tags=["ML Analytics"])
async def ml_traffic_forecast(
    hours_ahead: int = Query(24, ge=1, le=72, description="Hours to forecast")
):
    """
    Get ML-based traffic forecast for the port.
    
    Returns hourly predictions of vessel counts, berth utilization,
    and traffic trends.
    """
    traffic_service = get_traffic_service()
    
    try:
        forecast = traffic_service.get_traffic_forecast(hours_ahead)
        return forecast
    except Exception as e:
        logger.error(f"Traffic forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml/port-status", tags=["ML Analytics"])
async def ml_port_status():
    """
    Get current port status with AI insights.
    
    Returns real-time status including vessel counts, resource availability,
    weather conditions, and berth utilization.
    """
    traffic_service = get_traffic_service()
    
    try:
        status = traffic_service.get_current_port_status()
        return status
    except Exception as e:
        logger.error(f"Port status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SMARTBERTH CORE (CLAUDE-POWERED) ====================

@app.get("/core/status", tags=["SmartBerth Core"])
async def core_status():
    """
    Get SmartBerth Core status - Claude Opus 4 powered engine.
    """
    core = get_smartberth_core()
    return {
        "initialized": core._initialized,
        "model": settings.claude_model,
        "vessels_loaded": len(core._vessels_df) if core._vessels_df is not None else 0,
        "ais_records": len(core._ais_df) if core._ais_df is not None else 0,
        "berths_loaded": len(core._berths_df) if core._berths_df is not None else 0,
        "training_datasets": len(core._training_data),
    }


@app.post("/core/initialize", tags=["SmartBerth Core"])
async def initialize_core():
    """
    Initialize SmartBerth Core engine with Claude model and data.
    """
    core = get_smartberth_core()
    
    if core._initialized:
        return {"status": "already_initialized", "message": "SmartBerth Core is already initialized"}
    
    success = core.initialize()
    
    if success:
        return {
            "status": "initialized",
            "message": "SmartBerth Core initialized successfully",
            "model": settings.claude_model,
            "datasets_loaded": len(core._training_data)
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to initialize SmartBerth Core")


@app.get("/core/eta/{vessel_id}", tags=["SmartBerth Core"])
async def core_predict_eta(vessel_id: int):
    """
    Predict ETA using Claude-powered SmartBerth Core.
    Includes AI explanation and confidence scoring.
    """
    core = get_smartberth_core()
    
    if not core._initialized:
        if not core.initialize():
            raise HTTPException(status_code=503, detail="SmartBerth Core not initialized")
    
    try:
        from dataclasses import asdict
        from datetime import datetime
        
        prediction = core.predict_eta(vessel_id)
        result = asdict(prediction)
        # Convert datetime for JSON serialization
        if isinstance(result.get('predicted_eta'), datetime):
            result['predicted_eta'] = result['predicted_eta'].isoformat()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Core ETA prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/core/berth/{vessel_id}", tags=["SmartBerth Core"])
async def core_recommend_berth(vessel_id: int):
    """
    Get berth recommendation using Claude-powered SmartBerth Core.
    Includes constraint validation and AI reasoning.
    """
    core = get_smartberth_core()
    
    if not core._initialized:
        if not core.initialize():
            raise HTTPException(status_code=503, detail="SmartBerth Core not initialized")
    
    try:
        from dataclasses import asdict
        recommendation = core.recommend_berth(vessel_id)
        return asdict(recommendation)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Core berth recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/core/pipeline", tags=["SmartBerth Core"])
async def run_core_pipeline(vessel_ids: Optional[List[int]] = None):
    """
    Run full SmartBerth pipeline with Claude AI.
    
    Processes all vessels (or specified list) through:
    1. ETA prediction
    2. Berth recommendation
    3. Conflict detection
    4. AI-powered summary
    """
    core = get_smartberth_core()
    
    if not core._initialized:
        if not core.initialize():
            raise HTTPException(status_code=503, detail="SmartBerth Core not initialized")
    
    try:
        from datetime import datetime
        
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
        
        results = core.run_full_pipeline(vessel_ids)
        
        # Convert datetime objects
        for pred in results.get('eta_predictions', []):
            if isinstance(pred.get('predicted_eta'), datetime):
                pred['predicted_eta'] = pred['predicted_eta'].isoformat()
        
        return results
    except Exception as e:
        logger.error(f"Core pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/core/training-analysis", tags=["SmartBerth Core"])
async def analyze_training_data():
    """
    Analyze training data patterns.
    Returns statistics on vessel calls, ETA variance, dwell times, etc.
    """
    core = get_smartberth_core()
    
    if not core._initialized:
        if not core.initialize():
            raise HTTPException(status_code=503, detail="SmartBerth Core not initialized")
    
    return core.analyze_training_data()


@app.get("/core/insights", tags=["SmartBerth Core"])
async def get_training_insights():
    """
    Get AI-generated insights from training data analysis.
    Uses Claude to interpret patterns and provide recommendations.
    """
    core = get_smartberth_core()
    
    if not core._initialized:
        if not core.initialize():
            raise HTTPException(status_code=503, detail="SmartBerth Core not initialized")
    
    return {"insights": core.get_training_insights()}


# ==================== GRAPH REASONING ENDPOINTS ====================

class GraphQueryRequest(BaseModel):
    vessel_id: Optional[int] = None
    berth_id: Optional[int] = None
    port_id: Optional[int] = None
    schedule_id: Optional[int] = None
    time_start: Optional[str] = None  # ISO format
    time_end: Optional[str] = None    # ISO format
    limit: int = Field(default=5, ge=1, le=20)


class RouterQueryRequest(BaseModel):
    query: str
    use_ai_routing: bool = Field(default=True, description="Use Claude for query routing")


@app.get("/graph/status", tags=["Graph Reasoning"])
async def get_graph_status():
    """Get status of Neo4j graph database and reasoner"""
    try:
        from graph import get_graph_reasoner
        reasoner = get_graph_reasoner()
        return reasoner.get_status()
    except ImportError:
        return {"error": "Graph module not available"}
    except Exception as e:
        logger.error(f"Graph status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/stats", tags=["Graph Reasoning"])
async def get_graph_statistics():
    """Get statistics about nodes and relationships in the graph"""
    try:
        from graph import get_neo4j_loader
        loader = get_neo4j_loader()
        return loader.get_graph_stats()
    except ImportError:
        return {"error": "Graph module not available"}
    except Exception as e:
        logger.error(f"Graph stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/load-data", tags=["Graph Reasoning"])
async def load_data_to_graph(clear_first: bool = True):
    """Load data from SQL Server into Neo4j graph database"""
    try:
        from graph import get_neo4j_loader
        loader = get_neo4j_loader()
        
        if not loader.driver:
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        if not loader.sql_connection:
            raise HTTPException(status_code=503, detail="SQL Server not connected")
        
        results = loader.load_all(clear_first=clear_first)
        return {
            "success": True,
            "loaded": results,
            "total": sum(results.values())
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Graph module not available")
    except Exception as e:
        logger.error(f"Graph data load failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/suitable-berths", tags=["Graph Reasoning"])
async def find_suitable_berths(request: GraphQueryRequest):
    """
    Find suitable berths for a vessel using graph traversal.
    Returns berths with compatibility scores and AI explanation.
    """
    try:
        from graph import get_graph_reasoner
        reasoner = get_graph_reasoner()
        
        if not reasoner.driver:
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        if not request.vessel_id:
            raise HTTPException(status_code=400, detail="vessel_id is required")
        
        from datetime import datetime, timedelta
        time_start = request.time_start or datetime.now().isoformat()
        time_end = request.time_end or (datetime.now() + timedelta(days=1)).isoformat()
        
        result = reasoner.find_suitable_berths(
            vessel_id=request.vessel_id,
            check_time_start=time_start,
            check_time_end=time_end
        )
        
        return {
            "query_type": result.query_type,
            "results": result.raw_results,
            "explanation": result.explanation,
            "confidence": result.confidence,
            "recommendations": result.recommendations,
            "warnings": result.warnings,
            "time_ms": result.reasoning_time_ms
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Graph module not available")
    except Exception as e:
        logger.error(f"Suitable berths query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/explain-berth", tags=["Graph Reasoning"])
async def explain_berth_recommendation(request: GraphQueryRequest):
    """
    Explain why a berth is recommended for a vessel.
    Multi-hop graph traversal with Claude explanation.
    """
    try:
        from graph import get_graph_reasoner
        reasoner = get_graph_reasoner()
        
        if not reasoner.driver:
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        if not request.vessel_id or not request.berth_id:
            raise HTTPException(status_code=400, detail="vessel_id and berth_id are required")
        
        result = reasoner.explain_berth_recommendation(
            vessel_id=request.vessel_id,
            berth_id=request.berth_id
        )
        
        return {
            "query_type": result.query_type,
            "results": result.raw_results,
            "explanation": result.explanation,
            "confidence": result.confidence,
            "recommendations": result.recommendations,
            "warnings": result.warnings,
            "time_ms": result.reasoning_time_ms
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Graph module not available")
    except Exception as e:
        logger.error(f"Berth explanation query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/conflict-cascade", tags=["Graph Reasoning"])
async def analyze_conflict_cascade(request: GraphQueryRequest):
    """
    Analyze cascading effects of a scheduling conflict.
    Finds affected vessels and alternative options.
    """
    try:
        from graph import get_graph_reasoner
        reasoner = get_graph_reasoner()
        
        if not reasoner.driver:
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        if not request.schedule_id:
            raise HTTPException(status_code=400, detail="schedule_id is required")
        
        result = reasoner.analyze_conflict_cascade(schedule_id=request.schedule_id)
        
        return {
            "query_type": result.query_type,
            "results": result.raw_results,
            "explanation": result.explanation,
            "confidence": result.confidence,
            "recommendations": result.recommendations,
            "warnings": result.warnings,
            "time_ms": result.reasoning_time_ms
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Graph module not available")
    except Exception as e:
        logger.error(f"Conflict cascade query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/resource-contention", tags=["Graph Reasoning"])
async def detect_resource_contention(request: GraphQueryRequest):
    """
    Detect resource contention (pilots, tugs, berths) at a port.
    Identifies shortages and peak demand periods.
    """
    try:
        from graph import get_graph_reasoner
        reasoner = get_graph_reasoner()
        
        if not reasoner.driver:
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        if not request.port_id:
            raise HTTPException(status_code=400, detail="port_id is required")
        
        from datetime import datetime, timedelta
        time_start = request.time_start or datetime.now().isoformat()
        time_end = request.time_end or (datetime.now() + timedelta(hours=24)).isoformat()
        
        result = reasoner.detect_resource_contention(
            port_id=request.port_id,
            time_start=time_start,
            time_end=time_end
        )
        
        return {
            "query_type": result.query_type,
            "results": result.raw_results,
            "explanation": result.explanation,
            "confidence": result.confidence,
            "recommendations": result.recommendations,
            "warnings": result.warnings,
            "time_ms": result.reasoning_time_ms
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Graph module not available")
    except Exception as e:
        logger.error(f"Resource contention query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/alternative-berths", tags=["Graph Reasoning"])
async def find_alternative_berths(request: GraphQueryRequest):
    """
    Find alternative berths for a vessel with historical preference.
    Ranks alternatives by compatibility and past usage.
    """
    try:
        from graph import get_graph_reasoner
        reasoner = get_graph_reasoner()
        
        if not reasoner.driver:
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        if not request.vessel_id:
            raise HTTPException(status_code=400, detail="vessel_id is required")
        
        result = reasoner.find_alternative_berths(
            vessel_id=request.vessel_id,
            exclude_berth_id=request.berth_id,
            time_start=request.time_start,
            time_end=request.time_end,
            limit=request.limit
        )
        
        return {
            "query_type": result.query_type,
            "results": result.raw_results,
            "explanation": result.explanation,
            "confidence": result.confidence,
            "recommendations": result.recommendations,
            "warnings": result.warnings,
            "time_ms": result.reasoning_time_ms
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Graph module not available")
    except Exception as e:
        logger.error(f"Alternative berths query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== QUERY ROUTER ENDPOINTS ====================

@app.post("/router/route", tags=["Query Router"])
async def route_query(request: RouterQueryRequest):
    """
    Route a natural language query to the appropriate engine.
    Determines if query should go to ChromaDB (semantic) or Neo4j (graph).
    """
    try:
        from rag.router import get_query_router
        router = get_query_router()
        router.use_ai_routing = request.use_ai_routing
        
        decision = router.route(request.query)
        
        return {
            "query": request.query,
            "primary_engine": decision.primary_engine.value,
            "secondary_engine": decision.secondary_engine.value if decision.secondary_engine else None,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "intent": decision.query_intent,
            "detected_entities": decision.detected_entities
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Router module not available")
    except Exception as e:
        logger.error(f"Query routing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/router/execute", tags=["Query Router"])
async def execute_routed_query(request: RouterQueryRequest):
    """
    Route and execute a query across ChromaDB and/or Neo4j.
    Combines results from both engines if hybrid routing is selected.
    """
    try:
        from rag.router import get_query_orchestrator
        orchestrator = get_query_orchestrator()
        orchestrator.router.use_ai_routing = request.use_ai_routing
        
        result = orchestrator.execute(request.query)
        
        return {
            "query": result.query,
            "routing": {
                "primary_engine": result.routing.primary_engine.value,
                "secondary_engine": result.routing.secondary_engine.value if result.routing.secondary_engine else None,
                "confidence": result.routing.confidence,
                "intent": result.routing.query_intent
            },
            "chromadb_results": result.chromadb_results,
            "neo4j_results": result.neo4j_results,
            "combined_explanation": result.combined_explanation,
            "sources": result.sources
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Router module not available")
    except Exception as e:
        logger.error(f"Routed query execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BROWSER AGENT ENDPOINTS ====================

# Global state for browser agent
_browser_agent: Optional[AgenticBrowserController] = None
_agent_websockets: List[WebSocket] = []
_current_task_id: Optional[str] = None


class AgentTaskRequest(BaseModel):
    """Request to start a browser agent task"""
    task: str = Field(..., description="Natural language task description")
    start_url: Optional[str] = Field(None, description="Optional starting URL")
    max_steps: int = Field(50, description="Maximum steps before stopping")
    connect_to_chrome: bool = Field(False, description="Connect to existing Chrome via CDP (port 9222)")
    cdp_endpoint: Optional[str] = Field(None, description="Custom CDP endpoint (default: http://localhost:9222)")


class AgentStatusResponse(BaseModel):
    """Response for agent status"""
    available: bool
    running: bool
    current_task: Optional[str]
    state: Optional[str]
    steps_completed: int
    errors: int
    connected_mode: bool = False  # True if connected to user's Chrome


async def broadcast_to_websockets(message: dict):
    """Broadcast a message to all connected WebSocket clients"""
    if not _agent_websockets:
        return
    
    message_json = json.dumps(message, default=str)
    disconnected = []
    
    for ws in _agent_websockets:
        try:
            await ws.send_text(message_json)
        except Exception:
            disconnected.append(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        _agent_websockets.remove(ws)


@app.get("/agent/status", tags=["Browser Agent"])
async def get_agent_status() -> AgentStatusResponse:
    """Get the current status of the browser agent"""
    if not BROWSER_AGENT_AVAILABLE:
        return AgentStatusResponse(
            available=False,
            running=False,
            current_task=None,
            state=None,
            steps_completed=0,
            errors=0
        )
    
    global _browser_agent
    
    if _browser_agent is None:
        return AgentStatusResponse(
            available=True,
            running=False,
            current_task=None,
            state="idle",
            steps_completed=0,
            errors=0
        )
    
    # Check if memory is initialized
    if not _browser_agent.memory:
        return AgentStatusResponse(
            available=True,
            running=True,  # If agent exists but no memory, it's still initializing
            current_task="Initializing...",
            state="initializing",
            steps_completed=0,
            errors=0
        )
    
    summary = _browser_agent.memory.get_task_summary()
    return AgentStatusResponse(
        available=True,
        running=_browser_agent.state not in [AgentState.IDLE, AgentState.COMPLETED, AgentState.FAILED],
        current_task=_browser_agent.memory.current_task.task_description if _browser_agent.memory.current_task else None,
        state=_browser_agent.state.value,
        steps_completed=summary["total_steps"],
        errors=summary.get("errors_encountered", 0)
    )


@app.post("/agent/start", tags=["Browser Agent"])
async def start_agent_task(request: AgentTaskRequest, background_tasks: BackgroundTasks):
    """Start a new browser agent task"""
    if not BROWSER_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Browser Agent not available. Install playwright and beautifulsoup4.")
    
    global _browser_agent, _current_task_id
    
    # Check if already running
    if _browser_agent is not None and _browser_agent.state not in [AgentState.IDLE, AgentState.COMPLETED, AgentState.FAILED]:
        raise HTTPException(status_code=409, detail="Agent is already running a task")
    
    # Generate task ID
    import uuid
    _current_task_id = str(uuid.uuid4())[:8]
    
    async def on_step(step: AgentStep):
        """Callback when agent completes a step"""
        await broadcast_to_websockets({
            "type": "step",
            "task_id": _current_task_id,
            "step_number": step.step_number,
            "action": step.action.action_type.value if step.action else None,
            "action_details": {
                "target": step.action.target,  # CSS selector or URL
                "value": step.action.value,
                "reasoning": step.action.reasoning
            } if step.action else None,
            "thinking": step.thinking,  # Agent's reasoning
            "success": step.result.success if step.result else None,
            "error": step.result.error_message if step.result else None,
            "timestamp": step.timestamp.isoformat()
        })
    
    async def on_state_change(state: AgentState):
        """Callback when agent state changes"""
        await broadcast_to_websockets({
            "type": "state",
            "task_id": _current_task_id,
            "state": state.value,
            "timestamp": datetime.now().isoformat()
        })
    
    async def on_screenshot(screenshot_b64: str):
        """Callback when agent takes a screenshot"""
        await broadcast_to_websockets({
            "type": "screenshot",
            "task_id": _current_task_id,
            "data": screenshot_b64,
            "timestamp": datetime.now().isoformat()
        })
    
    async def on_tool_call(tool_name: str, parameters: dict, result: Any):
        """Callback when agent calls an internal tool"""
        # Determine status based on result type
        status = "success"
        result_data = result
        if isinstance(result, dict) and "error" in result:
            status = "error"
        elif result is None:
            status = "error"
            result_data = {"error": "No result returned"}
        
        await broadcast_to_websockets({
            "type": "tool_call",
            "task_id": _current_task_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result_data,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    
    # Determine if connecting to existing Chrome or launching new browser
    cdp_endpoint = None
    if request.connect_to_chrome:
        cdp_endpoint = request.cdp_endpoint or "http://localhost:9222"
        logger.info(f"Agent will connect to existing Chrome at {cdp_endpoint}")
    
    # In CDP mode, try to reuse existing agent if it's still connected
    # This allows consecutive tasks to work in the same browser session
    reuse_existing_agent = False
    if cdp_endpoint and _browser_agent is not None:
        # Check if agent is initialized and browser is ready
        if hasattr(_browser_agent, 'browser') and _browser_agent.browser and _browser_agent.browser.is_ready:
            reuse_existing_agent = True
            logger.info("Reusing existing CDP connection for consecutive task")
    
    if not reuse_existing_agent:
        # Create new agent controller
        _browser_agent = AgenticBrowserController(
            headless=False,  # Run visible so user can watch the agent navigate
            on_step=on_step,
            on_state_change=on_state_change,
            on_tool_call=on_tool_call,
            on_screenshot=on_screenshot
        )
    else:
        # Update callbacks on existing agent
        _browser_agent._on_step = on_step
        _browser_agent._on_state_change = on_state_change
        _browser_agent._on_tool_call = on_tool_call
        _browser_agent._on_screenshot = on_screenshot
    
    # Create task
    # If connecting to existing Chrome, don't specify URL - use current page
    target_url = request.start_url or "http://localhost:5174"
    if request.connect_to_chrome and not request.start_url:
        target_url = None  # Let agent use current page in connected browser
    
    task = AgentTask(
        task_id=_current_task_id,
        description=request.task,
        target_url=target_url or "",
        max_steps=request.max_steps
    )
    
    async def run_task():
        """Run the agent task in background"""
        global _browser_agent
        try:
            # Skip initialization if reusing existing agent with active CDP connection
            if reuse_existing_agent:
                logger.info("Using existing browser connection for consecutive task")
            else:
                # Initialize the browser agent (with CDP endpoint if connecting to existing Chrome)
                if not await _browser_agent.initialize(cdp_endpoint=cdp_endpoint):
                    if cdp_endpoint:
                        raise Exception(f"Failed to connect to Chrome at {cdp_endpoint}. Make sure Chrome is started with: --remote-debugging-port=9222")
                    else:
                        raise Exception("Failed to initialize browser agent")
            
            # Execute task and capture result
            result = await _browser_agent.execute_task(task)
            
            # Broadcast completion with summary and final screenshot
            completed_message = {
                "type": "completed",
                "task_id": _current_task_id,
                "success": result.get("success", False),
                "summary": result.get("summary", ""),
                "final_summary": result.get("final_summary", result.get("summary", "")),  # User-friendly summary
                "steps": result.get("steps", 0),
                "model_used": result.get("model_used", "unknown"),
                "pages_visited": result.get("pages_visited", []),
                "tool_calls_count": len(result.get("tool_calls", [])),
                "timestamp": datetime.now().isoformat()
            }
            
            # Include full-screen screenshot if available
            if result.get("final_screenshot"):
                completed_message["final_screenshot"] = result.get("final_screenshot")
            
            await broadcast_to_websockets(completed_message)
            
        except Exception as e:
            logger.error(f"Agent task failed: {e}")
            await broadcast_to_websockets({
                "type": "error",
                "task_id": _current_task_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        finally:
            # In CDP/connected mode, DON'T close the connection - keep it alive for consecutive tasks
            # Only cleanup if NOT using CDP (i.e., launched a new browser)
            if _browser_agent and not cdp_endpoint:
                await _browser_agent.close()
            # Note: In CDP mode, the connection stays alive so consecutive tasks can use the same browser
    
    # Start task in background
    background_tasks.add_task(run_task)
    
    return {
        "task_id": _current_task_id,
        "task": request.task,
        "status": "started",
        "message": "Agent task started. Connect to /agent/ws for real-time updates."
    }


@app.post("/agent/stop", tags=["Browser Agent"])
async def stop_agent_task():
    """Stop the currently running agent task"""
    if not BROWSER_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Browser Agent not available")
    
    global _browser_agent
    
    if _browser_agent is None:
        raise HTTPException(status_code=404, detail="No agent task is running")
    
    try:
        await _browser_agent.close()
        _browser_agent = None
        
        await broadcast_to_websockets({
            "type": "stopped",
            "task_id": _current_task_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return {"status": "stopped", "message": "Agent task stopped"}
    except Exception as e:
        logger.error(f"Failed to stop agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/history", tags=["Browser Agent"])
async def get_agent_history():
    """Get the action history of the current/last agent task"""
    if not BROWSER_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Browser Agent not available") 
    
    global _browser_agent
    
    if _browser_agent is None:
        return {"steps": [], "summary": None}
    
    steps = []
    try:
        # Use get_all_steps() method instead of steps property
        all_steps = _browser_agent.memory.get_all_steps()
        for step in all_steps:
            try:
                # Handle action_type safely - it might be an enum, string, or object
                action_type = None
                action_reason = None
                if step.action:
                    if hasattr(step.action, 'action_type'):
                        action_type = step.action.action_type.value if hasattr(step.action.action_type, 'value') else str(step.action.action_type)
                    elif isinstance(step.action, dict):
                        action_type = step.action.get('action_type')
                    # Get reasoning from the BrowserAction (not AgentStep)
                    if hasattr(step.action, 'reasoning'):
                        action_reason = step.action.reasoning
                
                # AgentStep has 'thinking', not 'reasoning'
                thinking = getattr(step, 'thinking', None) or action_reason
                
                steps.append({
                    "step_number": step.step_number,
                    "action": action_type,
                    "reasoning": thinking,
                    "success": step.result.success if step.result and hasattr(step.result, 'success') else None,
                    "url": getattr(step, 'url', ''),
                    "observation": getattr(step, 'observation', '')[:500] if getattr(step, 'observation', None) else None,
                    "timestamp": step.timestamp.isoformat() if hasattr(step.timestamp, 'isoformat') else str(step.timestamp)
                })
            except Exception as step_error:
                logger.warning(f"Error processing step {getattr(step, 'step_number', '?')}: {step_error}")
                steps.append({
                    "step_number": getattr(step, 'step_number', 0),
                    "action": "unknown",
                    "reasoning": str(step_error),
                    "success": None,
                    "url": '',
                    "timestamp": datetime.now().isoformat()
                })
    except Exception as e:
        logger.error(f"Error getting agent history: {e}")
        return {"steps": [], "summary": None, "error": str(e)}
    
    # Get summary safely
    summary = None
    try:
        summary = _browser_agent.memory.get_task_summary()
    except Exception as e:
        logger.warning(f"Error getting task summary: {e}")
    
    return {
        "steps": steps,
        "summary": summary
    }


# ==================== AGENT TOOLS API ====================

@app.get("/agent/tools", tags=["Browser Agent Tools"])
async def list_agent_tools():
    """Get list of all internal tools available to the agent"""
    if not BROWSER_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Browser Agent not available")
    
    global _browser_agent
    
    # Initialize agent if needed
    if _browser_agent is None:
        try:
            _browser_agent = create_browser_agent(headless=True)
        except Exception as e:
            logger.warning(f"Could not create browser agent: {e}")
            return {"tools": [], "error": str(e)}
    
    tools = _browser_agent.get_available_tools()
    return {
        "tools": tools,
        "count": len(tools),
        "categories": list(set(t["category"] for t in tools))
    }


class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: dict = {}


@app.post("/agent/tools/execute", tags=["Browser Agent Tools"])
async def execute_agent_tool(request: ToolExecutionRequest):
    """
    Execute an internal tool directly without using the browser.
    This allows API consumers to call database queries, ML predictions,
    and other backend functions that the agent can use.
    """
    if not BROWSER_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Browser Agent not available")
    
    global _browser_agent
    
    # Initialize agent if needed
    if _browser_agent is None:
        try:
            _browser_agent = create_browser_agent(headless=True)
            await _browser_agent.initialize()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {e}")
    
    try:
        result = await _browser_agent.execute_tool_direct(
            request.tool_name,
            request.parameters
        )
        return {
            "tool": request.tool_name,
            "parameters": request.parameters,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/tools/history", tags=["Browser Agent Tools"])
async def get_tool_call_history():
    """Get history of internal tool calls from this session"""
    if not BROWSER_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Browser Agent not available")
    
    global _browser_agent
    
    if _browser_agent is None:
        return {"tool_calls": [], "count": 0}
    
    history = _browser_agent.get_tool_call_history()
    return {
        "tool_calls": history,
        "count": len(history)
    }


@app.post("/agent/tools/query", tags=["Browser Agent Tools"])
async def agent_smart_query(query: str):
    """
    Execute a natural language query using the agent's tool system.
    The Qwen3 manager agent will classify and route the query to the appropriate tool.
    """
    if not BROWSER_AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Browser Agent not available")
    
    global _browser_agent
    
    # Initialize agent if needed
    if _browser_agent is None:
        try:
            _browser_agent = create_browser_agent(headless=True)
            await _browser_agent.initialize()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {e}")
    
    try:
        # First, use manager agent to classify the query
        classify_result = await _browser_agent.execute_tool_direct(
            "manager_classify",
            {"query": query}
        )
        
        # Based on classification, decide which tool to use
        if classify_result.get("success"):
            task_type = classify_result.get("data", {}).get("task_type", "unknown")
            
            # Map task type to tool
            tool_mapping = {
                "eta_prediction": ("ml_predict_eta", {"vessel_id": 1}),
                "berth_recommendation": ("ml_recommend_berth", {"vessel_id": 1}),
                "conflict_detection": ("ml_detect_conflicts", {}),
                "vessel_query": ("db_get_vessels", {}),
                "berth_query": ("db_get_berths", {}),
                "schedule_query": ("db_get_schedules", {}),
                "knowledge_query": ("rag_search", {"query": query}),
                "system_status": ("system_health", {}),
            }
            
            tool_name, default_params = tool_mapping.get(
                task_type, 
                ("rag_search", {"query": query})
            )
            
            # Execute the appropriate tool
            tool_result = await _browser_agent.execute_tool_direct(tool_name, default_params)
            
            return {
                "query": query,
                "classification": classify_result.get("data"),
                "tool_used": tool_name,
                "result": tool_result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Fallback to RAG search
            rag_result = await _browser_agent.execute_tool_direct(
                "rag_search",
                {"query": query, "top_k": 5}
            )
            return {
                "query": query,
                "classification": None,
                "tool_used": "rag_search",
                "result": rag_result,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Smart query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/agent/ws")
async def agent_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    _agent_websockets.append(websocket)
    
    logger.info(f"Browser agent WebSocket connected. Total clients: {len(_agent_websockets)}")
    
    # Send current status
    status = await get_agent_status()
    await websocket.send_text(json.dumps({
        "type": "connected",
        "status": status.model_dump(),
        "timestamp": datetime.now().isoformat()
    }))
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle ping/pong
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
                # Handle status request
                elif message.get("type") == "status":
                    status = await get_agent_status()
                    await websocket.send_text(json.dumps({
                        "type": "status",
                        "status": status.model_dump(),
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        _agent_websockets.remove(websocket)
        logger.info(f"Browser agent WebSocket disconnected. Total clients: {len(_agent_websockets)}")


# ==================== MAIN ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Hardcoded to avoid port conflicts
        reload=False,  # Disable for production
        log_level="info"
    )
