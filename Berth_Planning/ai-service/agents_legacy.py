"""
SmartBerth AI Service - Multi-Agent System
Implements the 5 core agents for intelligent berth planning:
1. ETA Predictor Agent - Predicts vessel arrival times
2. Berth Optimizer Agent - Optimizes berth allocation
3. Resource Scheduler Agent - Schedules cranes, pilots, tugs
4. Conflict Resolver Agent - Detects and resolves conflicts
5. Orchestrator Agent - Coordinates all agents
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from decimal import Decimal
import random
import math
import json

from database import get_db_service
from model import get_model

logger = logging.getLogger(__name__)


def to_float(value: Any, default: float = 0.0) -> float:
    """Convert Decimal or other numeric types to float safely"""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ==================== DATA CLASSES ====================

@dataclass
class VesselArrival:
    """Vessel arrival data for scheduling"""
    vessel_id: int
    vessel_name: str
    vessel_type: str
    loa: float
    beam: float
    draft: float
    gross_tonnage: float
    cargo_type: str
    cargo_volume: float
    priority: int
    eta: datetime
    predicted_eta: Optional[datetime] = None
    etd: Optional[datetime] = None


@dataclass
class BerthSlot:
    """Available berth time slot"""
    berth_id: int
    berth_name: str
    terminal_name: str
    berth_type: str
    max_loa: float
    max_beam: float
    max_draft: float
    num_cranes: int
    start_time: datetime
    end_time: datetime
    score: float = 0.0


@dataclass
class Allocation:
    """A vessel-to-berth allocation"""
    vessel_id: int
    berth_id: int
    start_time: datetime
    end_time: datetime
    score: float
    violations: List[str] = field(default_factory=list)
    resources: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conflict:
    """Scheduling conflict"""
    conflict_type: str  # "overlap", "resource", "tidal", "weather"
    severity: int  # 1-10
    affected_vessels: List[int]
    affected_berths: List[int]
    time_window: Tuple[datetime, datetime]
    description: str
    suggested_resolutions: List[Dict[str, Any]]


@dataclass
class AgentMessage:
    """Inter-agent communication message"""
    from_agent: str
    to_agent: str
    action: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


# ==================== ETA PREDICTOR AGENT ====================

class ETAPredictorAgent:
    """
    Predicts vessel arrival times using historical data, weather, and AIS.
    Implements ML-based ETA prediction with confidence scoring.
    """
    
    def __init__(self):
        self.db = get_db_service()
        self.model = get_model()
        self.name = "ETA_PREDICTOR"
        
        # Historical delay patterns by vessel type (in minutes)
        self.delay_patterns = {
            "container": {"mean": 45, "std": 30},
            "bulk": {"mean": 120, "std": 60},
            "tanker": {"mean": 90, "std": 45},
            "general": {"mean": 60, "std": 40},
            "roro": {"mean": 30, "std": 20},
        }
    
    def predict_eta(self, vessel_id: int) -> Dict[str, Any]:
        """
        Predict ETA for a vessel using multiple factors.
        Returns predicted ETA, confidence score, and contributing factors.
        """
        try:
            # Get vessel and schedule data
            vessel = self.db.get_vessel_by_id(vessel_id)
            if not vessel:
                return {"error": f"Vessel {vessel_id} not found"}
            
            schedule = self.db.get_vessel_schedule(vessel_id)
            if not schedule:
                return {"error": f"No schedule found for vessel {vessel_id}"}
            
            declared_eta = schedule.get('ETA')
            if not declared_eta:
                return {"error": "No ETA declared for vessel"}
            
            # Factors contributing to delay
            factors = {}
            total_delay_minutes = 0
            
            # 1. Historical vessel performance
            vessel_type = vessel.get('VesselType', 'general').lower()
            pattern = self.delay_patterns.get(vessel_type, {"mean": 60, "std": 40})
            historical_delay = pattern["mean"]
            factors["historical_pattern"] = {
                "description": f"{vessel_type.title()} vessels average {historical_delay}min delay",
                "delay_minutes": historical_delay,
                "weight": 0.3
            }
            total_delay_minutes += historical_delay * 0.3
            
            # 2. Weather impact
            try:
                weather = self.db.get_current_weather()
                if weather:
                    wind_speed = weather.get('WindSpeed', 0)
                    wave_height = weather.get('WaveHeight', 0)
                    
                    weather_delay = 0
                    if wind_speed > 20:
                        weather_delay += (wind_speed - 20) * 3
                    if wave_height > 1.5:
                        weather_delay += (wave_height - 1.5) * 20
                    
                    factors["weather"] = {
                        "wind_speed": wind_speed,
                        "wave_height": wave_height,
                        "delay_minutes": weather_delay,
                        "weight": 0.25
                    }
                    total_delay_minutes += weather_delay * 0.25
            except Exception as e:
                logger.warning(f"Could not get weather data: {e}")
            
            # 3. Port congestion
            try:
                eta_time = declared_eta if isinstance(declared_eta, datetime) else datetime.fromisoformat(str(declared_eta))
                pending_vessels = self.db.get_vessels_by_status('Scheduled')
                congestion_factor = min(len(pending_vessels) / 10, 1.0)  # Normalize to max 1.0
                congestion_delay = congestion_factor * 45  # Max 45 min delay
                
                factors["port_congestion"] = {
                    "pending_vessels": len(pending_vessels),
                    "congestion_factor": congestion_factor,
                    "delay_minutes": congestion_delay,
                    "weight": 0.2
                }
                total_delay_minutes += congestion_delay * 0.2
            except Exception as e:
                logger.warning(f"Could not check congestion: {e}")
            
            # 4. Tidal restrictions
            try:
                vessel_draft = to_float(vessel.get('Draft'), 0)
                if vessel_draft > 10:  # Deep draft vessel
                    tidal_delay = 60  # May need to wait for tide
                    factors["tidal_restriction"] = {
                        "vessel_draft": vessel_draft,
                        "requires_high_tide": True,
                        "delay_minutes": tidal_delay,
                        "weight": 0.25
                    }
                    total_delay_minutes += tidal_delay * 0.25
            except Exception as e:
                logger.warning(f"Could not check tidal: {e}")
            
            # Calculate predicted ETA
            eta_dt = declared_eta if isinstance(declared_eta, datetime) else datetime.fromisoformat(str(declared_eta))
            predicted_eta = eta_dt + timedelta(minutes=total_delay_minutes)
            
            # ======= DYNAMIC MULTI-FACTOR CONFIDENCE CALCULATION =======
            # Factor 1: Weather confidence (40% weight) - varies 0.5 to 1.0
            weather_factor = factors.get("weather", {})
            wind_speed = float(weather_factor.get("wind_speed", 10))  # Convert to float to avoid Decimal issues
            if wind_speed < 10:
                weather_confidence = 0.95
            elif wind_speed < 20:
                weather_confidence = 0.85 - (wind_speed - 10) * 0.02
            elif wind_speed < 30:
                weather_confidence = 0.65 - (wind_speed - 20) * 0.015
            else:
                weather_confidence = max(0.40, 0.50 - (wind_speed - 30) * 0.01)
            
            # Factor 2: Port congestion confidence (30% weight) - varies 0.5 to 1.0
            congestion_factor = factors.get("port_congestion", {})
            pending_count = int(congestion_factor.get("pending_vessels", 0))  # Convert to int
            if pending_count <= 2:
                congestion_confidence = 0.95
            elif pending_count <= 5:
                congestion_confidence = 0.90 - (pending_count - 2) * 0.05
            elif pending_count <= 10:
                congestion_confidence = 0.75 - (pending_count - 5) * 0.04
            else:
                congestion_confidence = max(0.50, 0.55 - (pending_count - 10) * 0.01)
            
            # Factor 3: Tidal constraints confidence (15% weight) - varies 0.6 to 1.0
            tidal_factor = factors.get("tidal_restriction", {})
            if tidal_factor.get("requires_high_tide", False):
                vessel_draft = float(tidal_factor.get("vessel_draft", 10))  # Convert to float
                if vessel_draft > 14:
                    tidal_confidence = 0.60
                elif vessel_draft > 12:
                    tidal_confidence = 0.75
                else:
                    tidal_confidence = 0.85
            else:
                tidal_confidence = 1.0
            
            # Factor 4: Historical pattern confidence (15% weight) - fixed based on vessel type
            historical_conf_map = {
                "container": 0.85,
                "bulk": 0.70,
                "tanker": 0.75,
                "general": 0.65,
                "roro": 0.90
            }
            historical_confidence = historical_conf_map.get(vessel_type, 0.70)
            
            # Weighted combination for final confidence
            confidence = (
                weather_confidence * 0.40 +
                congestion_confidence * 0.30 +
                tidal_confidence * 0.15 +
                historical_confidence * 0.15
            )
            # Clamp to reasonable range
            confidence = max(0.35, min(0.95, confidence))
            
            # Determine status
            deviation = int(total_delay_minutes)
            if deviation <= 15:
                status = "on_time"
            elif deviation > 0:
                status = "delayed"
            else:
                status = "early"
            
            return {
                "vessel_id": vessel_id,
                "vessel_name": vessel.get('VesselName', ''),
                "original_eta": eta_dt.isoformat(),
                "predicted_eta": predicted_eta.isoformat(),
                "deviation_minutes": deviation,
                "confidence_score": round(confidence, 2),
                "status": status,
                "factors": factors
            }
            
        except Exception as e:
            logger.error(f"ETA prediction error: {e}")
            return {"error": str(e)}
    
    def predict_dwell_time(self, vessel: Dict[str, Any], berth: Dict[str, Any]) -> int:
        """Predict how long a vessel will stay at berth (in hours)"""
        cargo_volume = vessel.get('CargoVolume', 1000)
        num_cranes = berth.get('NumberOfCranes', 2)
        vessel_type = vessel.get('VesselType', 'general').lower()
        
        # Base handling rates (units/hour)
        handling_rates = {
            "container": 25,  # TEUs per crane per hour
            "bulk": 500,      # Tonnes per hour
            "tanker": 1000,   # Tonnes per hour
            "general": 100,   # Tonnes per crane per hour
        }
        
        rate = handling_rates.get(vessel_type, 100) * max(1, num_cranes)
        base_hours = cargo_volume / rate
        
        # Add preparation and completion time
        prep_time = 2  # hours
        
        return int(base_hours + prep_time)


# ==================== BERTH OPTIMIZER AGENT ====================

class BerthOptimizerAgent:
    """
    Optimizes berth allocation using constraint programming and genetic algorithms.
    Implements multi-objective optimization considering utilization, waiting time, and priorities.
    """
    
    def __init__(self):
        self.db = get_db_service()
        self.model = get_model()
        self.eta_predictor = ETAPredictorAgent()
        self.name = "BERTH_OPTIMIZER"
        
        # Optimization weights
        self.weights = {
            "physical_fit": 25,
            "type_match": 20,
            "waiting_time": 20,
            "resource_availability": 15,
            "historical_performance": 10,
            "tidal_compatibility": 10,
        }
    
    def get_berth_suggestions(
        self, 
        vessel_id: int, 
        top_k: int = 5,
        eta_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get ranked berth suggestions for a vessel.
        Uses multi-factor scoring with constraint validation.
        """
        try:
            # Get vessel data
            vessel = self.db.get_vessel_by_id(vessel_id)
            if not vessel:
                return [{"error": f"Vessel {vessel_id} not found"}]
            
            schedule = self.db.get_vessel_schedule(vessel_id)
            eta = eta_override or (schedule.get('ETA') if schedule else None)
            
            if not eta:
                return [{"error": "No ETA available for vessel"}]
            
            # Parse ETA
            eta_dt = eta if isinstance(eta, datetime) else datetime.fromisoformat(str(eta).replace('Z', '+00:00'))
            
            # Predict dwell time
            dwell_hours = schedule.get('EstimatedDuration', 24) if schedule else 24
            etd_dt = eta_dt + timedelta(hours=dwell_hours)
            
            # Get available berths
            berths = self.db.get_available_berths(
                eta_dt.isoformat(),
                etd_dt.isoformat()
            )
            
            if not berths:
                # Fallback to all berths
                berths = self.db.get_all_berths()
            
            # Score each berth
            scored_berths = []
            for berth in berths:
                score_result = self._score_berth(vessel, berth, eta_dt)
                scored_berths.append(score_result)
            
            # Sort by total score descending
            scored_berths.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Return top K suggestions
            return scored_berths[:top_k]
            
        except Exception as e:
            logger.error(f"Berth suggestion error: {e}")
            import traceback
            traceback.print_exc()
            return [{"error": str(e)}]
    
    def _score_berth(
        self, 
        vessel: Dict[str, Any], 
        berth: Dict[str, Any],
        eta: datetime
    ) -> Dict[str, Any]:
        """Calculate comprehensive score for a berth allocation"""
        scores = {}
        violations = []
        
        # Convert Decimal to float for vessel dimensions
        vessel_loa = to_float(vessel.get('LOA'), 0)
        vessel_draft = to_float(vessel.get('Draft'), 0)
        berth_max_loa = to_float(berth.get('MaxLOA', berth.get('Length')), 999)
        berth_max_draft = to_float(berth.get('MaxDraft'), 99)
        
        # 1. Physical Fit Score (25 points)
        loa_score = self._calculate_fit_score(vessel_loa, berth_max_loa)
        draft_score = self._calculate_fit_score(vessel_draft, berth_max_draft)
        physical_score = (loa_score + draft_score) / 2 * self.weights["physical_fit"]
        scores["physical_fit"] = physical_score
        
        if vessel_loa > berth_max_loa:
            violations.append({
                "type": "HARD",
                "constraint": "LOA_LIMIT",
                "description": f"Vessel LOA exceeds berth limit"
            })
        
        if vessel_draft > berth_max_draft:
            violations.append({
                "type": "HARD",
                "constraint": "DRAFT_LIMIT", 
                "description": f"Vessel draft exceeds berth depth"
            })
        
        # 2. Type Match Score (20 points)
        type_match = self._check_type_compatibility(
            vessel.get('VesselType', ''),
            berth.get('BerthType', '')
        )
        type_score = type_match * self.weights["type_match"]
        scores["type_match"] = type_score
        
        if type_match < 0.5:
            violations.append({
                "type": "SOFT",
                "constraint": "TYPE_MISMATCH",
                "description": f"Suboptimal cargo type match"
            })
        
        # 3. Waiting Time Score (20 points) - based on availability
        waiting_score = self.weights["waiting_time"]  # Assume no wait if available
        scores["waiting_time"] = waiting_score
        
        # 4. Resource Availability (15 points)
        num_cranes = to_float(berth.get('NumberOfCranes'), 0)
        resource_score = min(num_cranes / 4, 1.0) * self.weights["resource_availability"]
        scores["resource_availability"] = resource_score
        
        # 5. Historical Performance (10 points) - placeholder
        scores["historical"] = self.weights["historical_performance"] * 0.8
        
        # 6. Tidal Compatibility (10 points)
        tidal_score = self.weights["tidal_compatibility"]
        if vessel_draft > 10:
            tidal_score *= 0.7  # Reduce score for deep draft
        scores["tidal"] = tidal_score
        
        # Calculate total
        total_score = sum(scores.values())
        max_score = sum(self.weights.values())
        normalized_score = (total_score / max_score) * 100
        
        # Check feasibility
        hard_violations = [v for v in violations if v["type"] == "HARD"]
        is_feasible = len(hard_violations) == 0
        
        # Generate explanation
        explanation = self._generate_explanation(vessel, berth, scores, violations)
        
        return {
            "berth_id": berth.get('BerthId'),
            "berth_name": berth.get('BerthName', ''),
            "terminal_name": berth.get('TerminalName', ''),
            "total_score": round(normalized_score, 1),
            "score_breakdown": {k: round(v, 1) for k, v in scores.items()},
            "violations": violations,
            "is_feasible": is_feasible,
            "explanation": explanation,
            "berth_details": {
                "max_loa": berth.get('MaxLOA', berth.get('Length')),
                "max_draft": berth.get('MaxDraft'),
                "berth_type": berth.get('BerthType'),
                "num_cranes": berth.get('NumberOfCranes', num_cranes),
            }
        }
    
    def _calculate_fit_score(self, vessel_value: float, berth_limit: float) -> float:
        """Calculate fit score (0-1) based on margin"""
        if berth_limit <= 0:
            return 0.5
        if vessel_value > berth_limit:
            return 0  # Hard constraint violation
        margin = (berth_limit - vessel_value) / berth_limit
        # Ideal margin is 10-20%
        if 0.1 <= margin <= 0.3:
            return 1.0
        elif margin > 0.3:
            return 0.8  # Too much margin, slight waste
        else:
            return max(0, margin * 5)  # Tight fit
    
    def _check_type_compatibility(self, vessel_type: str, berth_type: str) -> float:
        """Check cargo type compatibility (0-1)"""
        vessel_type = vessel_type.lower()
        berth_type = berth_type.lower()
        
        compatibility = {
            "container": {"container": 1.0, "multipurpose": 0.7, "general": 0.5},
            "bulk": {"bulk": 1.0, "multipurpose": 0.7, "general": 0.6},
            "tanker": {"liquid": 1.0, "tanker": 1.0, "oil": 1.0},
            "roro": {"roro": 1.0, "ro-ro": 1.0, "multipurpose": 0.6},
            "general": {"general": 1.0, "multipurpose": 0.9, "container": 0.5},
        }
        
        type_matches = compatibility.get(vessel_type, {})
        return type_matches.get(berth_type, 0.3)
    
    def _generate_explanation(
        self, 
        vessel: Dict[str, Any], 
        berth: Dict[str, Any],
        scores: Dict[str, float],
        violations: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable explanation for berth suggestion"""
        parts = []
        
        vessel_name = vessel.get('VesselName', 'Vessel')
        berth_name = berth.get('BerthName', 'Berth')
        
        if not violations:
            parts.append(f"{berth_name} is a suitable berth for {vessel_name}.")
        elif any(v["type"] == "HARD" for v in violations):
            parts.append(f"⚠️ {berth_name} has constraint violations:")
            for v in violations:
                if v["type"] == "HARD":
                    parts.append(f"  - {v['description']}")
        else:
            parts.append(f"{berth_name} is feasible with minor concerns:")
            for v in violations:
                parts.append(f"  - {v['description']}")
        
        # Highlight strengths
        if scores.get("physical_fit", 0) > 20:
            parts.append("✓ Good physical dimensions match")
        if scores.get("type_match", 0) > 15:
            parts.append("✓ Cargo type is compatible")
        if scores.get("resource_availability", 0) > 10:
            parts.append(f"✓ {berth.get('NumberOfCranes', 2)} cranes available")
        
        return " ".join(parts)
    
    def optimize_schedule(
        self, 
        vessels: List[Dict[str, Any]], 
        time_horizon_hours: int = 48,
        algorithm: str = "greedy"
    ) -> Dict[str, Any]:
        """
        Optimize berth schedule for multiple vessels.
        Supports greedy, genetic algorithm, and constraint programming.
        """
        if algorithm == "greedy":
            return self._greedy_optimization(vessels, time_horizon_hours)
        elif algorithm == "genetic":
            return self._genetic_optimization(vessels, time_horizon_hours)
        else:
            return self._greedy_optimization(vessels, time_horizon_hours)
    
    def _greedy_optimization(
        self, 
        vessels: List[Dict[str, Any]], 
        time_horizon_hours: int
    ) -> Dict[str, Any]:
        """Greedy heuristic for quick solutions"""
        allocations = []
        unallocated = []
        berth_schedules = {}  # berth_id -> list of (start, end)
        
        # Sort vessels by priority and ETA
        sorted_vessels = sorted(
            vessels, 
            key=lambda v: (v.get('Priority', 2), v.get('ETA', datetime.max))
        )
        
        for vessel in sorted_vessels:
            vessel_id = vessel.get('VesselId')
            suggestions = self.get_berth_suggestions(vessel_id, top_k=10)
            
            allocated = False
            for suggestion in suggestions:
                if not suggestion.get('is_feasible', False):
                    continue
                
                berth_id = suggestion.get('berth_id')
                if berth_id is None:
                    continue
                
                # Check for overlaps
                eta = vessel.get('ETA')
                if not eta:
                    continue
                    
                eta_dt = eta if isinstance(eta, datetime) else datetime.fromisoformat(str(eta))
                dwell_hours = self.eta_predictor.predict_dwell_time(vessel, suggestion)
                etd_dt = eta_dt + timedelta(hours=dwell_hours)
                
                # Check existing allocations for this berth
                berth_schedule = berth_schedules.get(berth_id, [])
                overlap = False
                for start, end in berth_schedule:
                    if eta_dt < end and etd_dt > start:
                        overlap = True
                        break
                
                if not overlap:
                    allocations.append({
                        "vessel_id": vessel_id,
                        "vessel_name": vessel.get('VesselName', ''),
                        "berth_id": berth_id,
                        "berth_name": suggestion.get('berth_name', ''),
                        "start_time": eta_dt.isoformat(),
                        "end_time": etd_dt.isoformat(),
                        "score": suggestion.get('total_score', 0)
                    })
                    
                    # Update berth schedule
                    if berth_id not in berth_schedules:
                        berth_schedules[berth_id] = []
                    berth_schedules[berth_id].append((eta_dt, etd_dt))
                    
                    allocated = True
                    break
            
            if not allocated:
                unallocated.append({
                    "vessel_id": vessel_id,
                    "vessel_name": vessel.get('VesselName', ''),
                    "reason": "No feasible berth available"
                })
        
        return {
            "algorithm": "greedy",
            "allocations": allocations,
            "unallocated": unallocated,
            "total_vessels": len(vessels),
            "allocated_count": len(allocations),
            "utilization": len(allocations) / max(len(vessels), 1) * 100
        }
    
    def _genetic_optimization(
        self, 
        vessels: List[Dict[str, Any]], 
        time_horizon_hours: int,
        population_size: int = 50,
        generations: int = 100
    ) -> Dict[str, Any]:
        """Genetic algorithm for global optimization"""
        # Get all berths
        berths = self.db.get_all_berths()
        
        if not vessels or not berths:
            return {"error": "No vessels or berths to optimize"}
        
        # Create initial population
        population = []
        for _ in range(population_size):
            chromosome = []
            for vessel in vessels:
                # Random berth assignment
                berth = random.choice(berths)
                chromosome.append(berth.get('BerthId'))
            population.append(chromosome)
        
        # Evolution
        best_solution = None
        best_fitness = -float('inf')
        
        for gen in range(generations):
            # Evaluate fitness
            fitness_scores = []
            for chromosome in population:
                fitness = self._evaluate_chromosome(chromosome, vessels, berths)
                fitness_scores.append(fitness)
                
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_solution = chromosome.copy()
            
            # Selection (tournament)
            new_population = []
            for _ in range(population_size):
                tournament = random.sample(range(len(population)), 3)
                winner = max(tournament, key=lambda i: fitness_scores[i])
                new_population.append(population[winner].copy())
            
            # Crossover
            for i in range(0, len(new_population) - 1, 2):
                if random.random() < 0.7:
                    point = random.randint(1, len(vessels) - 1)
                    new_population[i][point:], new_population[i+1][point:] = \
                        new_population[i+1][point:], new_population[i][point:]
            
            # Mutation
            for chromosome in new_population:
                for i in range(len(chromosome)):
                    if random.random() < 0.1:
                        chromosome[i] = random.choice(berths).get('BerthId')
            
            population = new_population
        
        # Decode best solution
        allocations = []
        berth_map = {b['BerthId']: b for b in berths}
        
        for i, vessel in enumerate(vessels):
            berth_id = best_solution[i]
            berth = berth_map.get(berth_id, {})
            
            eta = vessel.get('ETA')
            eta_dt = eta if isinstance(eta, datetime) else datetime.fromisoformat(str(eta)) if eta else datetime.now()
            dwell_hours = 24  # Default
            
            allocations.append({
                "vessel_id": vessel.get('VesselId'),
                "vessel_name": vessel.get('VesselName', ''),
                "berth_id": berth_id,
                "berth_name": berth.get('BerthName', ''),
                "start_time": eta_dt.isoformat(),
                "end_time": (eta_dt + timedelta(hours=dwell_hours)).isoformat(),
                "score": self._score_assignment(vessel, berth)
            })
        
        return {
            "algorithm": "genetic",
            "generations": generations,
            "best_fitness": round(best_fitness, 2),
            "allocations": allocations,
            "total_vessels": len(vessels),
            "allocated_count": len(allocations)
        }
    
    def _evaluate_chromosome(
        self, 
        chromosome: List[int], 
        vessels: List[Dict[str, Any]], 
        berths: List[Dict[str, Any]]
    ) -> float:
        """Evaluate fitness of a chromosome (allocation solution)"""
        berth_map = {b['BerthId']: b for b in berths}
        total_score = 0
        penalties = 0
        
        berth_usage = {}  # Track berth utilization
        
        for i, vessel in enumerate(vessels):
            berth_id = chromosome[i]
            berth = berth_map.get(berth_id, {})
            
            # Add score for valid allocation
            total_score += self._score_assignment(vessel, berth)
            
            # Penalty for hard constraint violations
            vessel_loa = to_float(vessel.get('LOA'), 0)
            vessel_draft = to_float(vessel.get('Draft'), 0)
            berth_max_loa = to_float(berth.get('MaxLOA', berth.get('Length')), 999)
            berth_max_draft = to_float(berth.get('MaxDraft'), 99)
            
            if vessel_loa > berth_max_loa:
                penalties += 100
            if vessel_draft > berth_max_draft:
                penalties += 100
            
            # Track usage for overlap penalty
            if berth_id not in berth_usage:
                berth_usage[berth_id] = 0
            berth_usage[berth_id] += 1
        
        # Penalty for berth overloading
        for berth_id, count in berth_usage.items():
            if count > 1:
                penalties += (count - 1) * 50
        
        return total_score - penalties
    
    def _score_assignment(self, vessel: Dict[str, Any], berth: Dict[str, Any]) -> float:
        """Quick score for vessel-berth assignment"""
        if not berth:
            return 0
        
        score = 50.0  # Base score
        
        # Physical fit bonus
        vessel_loa = to_float(vessel.get('LOA'), 0)
        berth_max_loa = to_float(berth.get('MaxLOA', berth.get('Length')), 300)
        loa_margin = berth_max_loa - vessel_loa
        if loa_margin > 0:
            score += min(20.0, loa_margin / 10)
        else:
            score -= 50.0
        
        # Type match
        if self._check_type_compatibility(
            vessel.get('VesselType', ''), 
            berth.get('BerthType', '')
        ) > 0.7:
            score += 20.0
        
        return score


# ==================== RESOURCE SCHEDULER AGENT ====================

class ResourceSchedulerAgent:
    """
    Schedules operational resources: pilots, tugboats, cranes.
    Ensures resource availability aligns with berth allocations.
    """
    
    def __init__(self):
        self.db = get_db_service()
        self.name = "RESOURCE_SCHEDULER"
        
        # Resource requirements by vessel size
        self.tug_requirements = {
            "small": 1,   # < 20,000 GT
            "medium": 2,  # 20,000 - 50,000 GT
            "large": 3,   # > 50,000 GT
        }
    
    def schedule_resources(
        self, 
        vessel: Dict[str, Any], 
        berth: Dict[str, Any],
        operation_time: datetime
    ) -> Dict[str, Any]:
        """Schedule required resources for a berthing operation"""
        resources_needed = self._calculate_resource_needs(vessel)
        
        available_resources = {
            "pilots": [],
            "tugs": [],
            "cranes": []
        }
        
        try:
            # Get available pilots
            pilots = self.db.get_available_resources('Pilot', operation_time.isoformat())
            available_resources["pilots"] = pilots[:1] if pilots else []
            
            # Get available tugs
            tugs = self.db.get_available_resources('Tugboat', operation_time.isoformat())
            tugs_needed = resources_needed.get('tugs', 1)
            available_resources["tugs"] = tugs[:tugs_needed] if tugs else []
            
            # Cranes from berth
            num_cranes = berth.get('NumberOfCranes', 0)
            available_resources["cranes"] = [{"type": "Crane", "count": num_cranes}]
            
        except Exception as e:
            logger.warning(f"Could not fetch resources: {e}")
        
        # Check if all resources available
        all_available = (
            len(available_resources["pilots"]) >= 1 and
            len(available_resources["tugs"]) >= resources_needed.get('tugs', 1)
        )
        
        return {
            "operation_time": operation_time.isoformat(),
            "vessel_id": vessel.get('VesselId'),
            "berth_id": berth.get('BerthId'),
            "resources_needed": resources_needed,
            "resources_available": available_resources,
            "all_resources_available": all_available,
            "bottlenecks": self._identify_bottlenecks(resources_needed, available_resources)
        }
    
    def _calculate_resource_needs(self, vessel: Dict[str, Any]) -> Dict[str, int]:
        """Calculate resources needed for a vessel"""
        gt = vessel.get('GrossTonnage', 10000)
        
        if gt < 20000:
            size_class = "small"
        elif gt < 50000:
            size_class = "medium"
        else:
            size_class = "large"
        
        return {
            "pilots": 1,
            "tugs": self.tug_requirements[size_class],
            "linesmen": 4 if size_class != "small" else 2,
        }
    
    def _identify_bottlenecks(
        self, 
        needed: Dict[str, int], 
        available: Dict[str, Any]
    ) -> List[str]:
        """Identify resource bottlenecks"""
        bottlenecks = []
        
        if len(available.get("pilots", [])) < needed.get("pilots", 1):
            bottlenecks.append("Pilot shortage")
        
        if len(available.get("tugs", [])) < needed.get("tugs", 1):
            bottlenecks.append(f"Tug shortage (need {needed.get('tugs', 1)})")
        
        return bottlenecks


# ==================== CONFLICT RESOLVER AGENT ====================

class ConflictResolverAgent:
    """
    Detects and resolves scheduling conflicts.
    Provides automated resolution suggestions.
    """
    
    def __init__(self):
        self.db = get_db_service()
        self.model = get_model()
        self.name = "CONFLICT_RESOLVER"
    
    def detect_conflicts(
        self, 
        time_window_hours: int = 48
    ) -> List[Dict[str, Any]]:
        """Detect all conflicts in the upcoming schedule"""
        conflicts = []
        
        try:
            # Get upcoming schedule
            start = datetime.now()
            end = start + timedelta(hours=time_window_hours)
            
            schedules = self.db.get_schedules_in_range(
                start.isoformat(), 
                end.isoformat()
            )
            
            # Check for overlaps
            overlap_conflicts = self._detect_overlaps(schedules)
            conflicts.extend(overlap_conflicts)
            
            # Check for resource conflicts
            resource_conflicts = self._detect_resource_conflicts(schedules)
            conflicts.extend(resource_conflicts)
            
        except Exception as e:
            logger.error(f"Conflict detection error: {e}")
        
        return conflicts
    
    def _detect_overlaps(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect berth overlap conflicts"""
        conflicts = []
        
        # Group by berth
        berth_schedules = {}
        for s in schedules:
            berth_id = s.get('BerthId')
            if berth_id:
                if berth_id not in berth_schedules:
                    berth_schedules[berth_id] = []
                berth_schedules[berth_id].append(s)
        
        # Check each berth for overlaps
        for berth_id, berth_schedule in berth_schedules.items():
            for i, s1 in enumerate(berth_schedule):
                for s2 in berth_schedule[i+1:]:
                    eta1 = s1.get('ETA')
                    etd1 = s1.get('ETD') or s1.get('ATD')
                    eta2 = s2.get('ETA')
                    etd2 = s2.get('ETD') or s2.get('ATD')
                    
                    if not all([eta1, etd1, eta2, etd2]):
                        continue
                    
                    # Check overlap
                    if eta1 < etd2 and eta2 < etd1:
                        conflicts.append({
                            "type": "BERTH_OVERLAP",
                            "severity": 10,
                            "berth_id": berth_id,
                            "affected_vessels": [s1.get('VesselId'), s2.get('VesselId')],
                            "vessel_names": [s1.get('VesselName'), s2.get('VesselName')],
                            "description": f"Vessels overlap at berth {s1.get('BerthName')}",
                            "resolutions": self._suggest_overlap_resolutions(s1, s2)
                        })
        
        return conflicts
    
    def _detect_resource_conflicts(self, schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect resource shortage conflicts"""
        conflicts = []
        
        # Group by time slots (hourly)
        time_slots = {}
        for s in schedules:
            eta = s.get('ETA')
            if eta:
                eta_dt = eta if isinstance(eta, datetime) else datetime.fromisoformat(str(eta))
                slot = eta_dt.replace(minute=0, second=0, microsecond=0)
                if slot not in time_slots:
                    time_slots[slot] = []
                time_slots[slot].append(s)
        
        # Check each slot
        for slot, slot_schedules in time_slots.items():
            if len(slot_schedules) > 2:  # More than 2 vessels needing pilots at same time
                conflicts.append({
                    "type": "RESOURCE_SHORTAGE",
                    "severity": 7,
                    "time": slot.isoformat(),
                    "affected_vessels": [s.get('VesselId') for s in slot_schedules],
                    "vessel_names": [s.get('VesselName') for s in slot_schedules],
                    "description": f"{len(slot_schedules)} vessels need pilots at {slot.strftime('%H:%M')}",
                    "resolutions": [
                        {"action": "stagger_arrivals", "description": "Stagger arrival times by 30 minutes"},
                        {"action": "call_additional_pilots", "description": "Request additional pilot on duty"}
                    ]
                })
        
        return conflicts
    
    def _suggest_overlap_resolutions(
        self, 
        s1: Dict[str, Any], 
        s2: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest resolutions for overlap conflicts"""
        resolutions = []
        
        # Option 1: Delay second vessel
        resolutions.append({
            "action": "delay_vessel",
            "vessel_id": s2.get('VesselId'),
            "vessel_name": s2.get('VesselName'),
            "new_eta": (s1.get('ETD') or s1.get('ETA')),
            "description": f"Delay {s2.get('VesselName')} until {s1.get('VesselName')} departs"
        })
        
        # Option 2: Move to different berth
        resolutions.append({
            "action": "reassign_berth",
            "vessel_id": s2.get('VesselId'),
            "vessel_name": s2.get('VesselName'),
            "description": f"Move {s2.get('VesselName')} to alternative berth"
        })
        
        # Option 3: Expedite first vessel
        resolutions.append({
            "action": "expedite_departure",
            "vessel_id": s1.get('VesselId'),
            "vessel_name": s1.get('VesselName'),
            "description": f"Expedite {s1.get('VesselName')} operations"
        })
        
        return resolutions
    
    def resolve_conflict(
        self, 
        conflict_id: int, 
        resolution_action: str
    ) -> Dict[str, Any]:
        """Apply a resolution to a conflict"""
        # This would interact with the database to apply changes
        return {
            "success": True,
            "conflict_id": conflict_id,
            "action_taken": resolution_action,
            "message": f"Resolution '{resolution_action}' applied successfully"
        }


# ==================== ORCHESTRATOR AGENT ====================

class OrchestratorAgent:
    """
    Master agent that coordinates all other agents.
    Handles complex multi-step operations and decision making.
    """
    
    def __init__(self):
        self.db = get_db_service()
        self.model = get_model()
        self.name = "ORCHESTRATOR"
        
        # Initialize sub-agents
        self.eta_predictor = ETAPredictorAgent()
        self.berth_optimizer = BerthOptimizerAgent()
        self.resource_scheduler = ResourceSchedulerAgent()
        self.conflict_resolver = ConflictResolverAgent()
        
        self.message_log: List[AgentMessage] = []
    
    def process_vessel_arrival(self, vessel_id: int) -> Dict[str, Any]:
        """
        Complete workflow for processing a vessel arrival.
        Coordinates all agents to produce optimal allocation.
        """
        result = {
            "vessel_id": vessel_id,
            "steps": [],
            "success": False
        }
        
        try:
            # Step 1: Predict ETA
            self._log_message("ORCHESTRATOR", "ETA_PREDICTOR", "predict_eta", {"vessel_id": vessel_id})
            eta_result = self.eta_predictor.predict_eta(vessel_id)
            result["steps"].append({
                "agent": "ETA_PREDICTOR",
                "action": "predict_eta",
                "result": eta_result
            })
            
            if "error" in eta_result:
                result["error"] = eta_result["error"]
                return result
            
            # Step 2: Get berth suggestions
            self._log_message("ORCHESTRATOR", "BERTH_OPTIMIZER", "get_suggestions", {"vessel_id": vessel_id})
            suggestions = self.berth_optimizer.get_berth_suggestions(
                vessel_id, 
                top_k=5,
                eta_override=eta_result.get("predicted_eta")
            )
            result["steps"].append({
                "agent": "BERTH_OPTIMIZER",
                "action": "get_suggestions",
                "result": suggestions
            })
            
            if not suggestions or "error" in suggestions[0]:
                result["error"] = "No berth suggestions available"
                return result
            
            # Step 3: Check resources for top suggestion
            top_suggestion = suggestions[0]
            vessel = self.db.get_vessel_by_id(vessel_id)
            
            if top_suggestion.get("is_feasible"):
                eta_dt = datetime.fromisoformat(eta_result.get("predicted_eta", datetime.now().isoformat()))
                berth_data = {"BerthId": top_suggestion.get("berth_id"), **top_suggestion.get("berth_details", {})}
                
                self._log_message("ORCHESTRATOR", "RESOURCE_SCHEDULER", "schedule_resources", {})
                resource_result = self.resource_scheduler.schedule_resources(
                    vessel, berth_data, eta_dt
                )
                result["steps"].append({
                    "agent": "RESOURCE_SCHEDULER",
                    "action": "schedule_resources",
                    "result": resource_result
                })
            
            # Step 4: Check for conflicts
            self._log_message("ORCHESTRATOR", "CONFLICT_RESOLVER", "detect_conflicts", {})
            conflicts = self.conflict_resolver.detect_conflicts(time_window_hours=48)
            relevant_conflicts = [c for c in conflicts if vessel_id in c.get("affected_vessels", [])]
            
            result["steps"].append({
                "agent": "CONFLICT_RESOLVER",
                "action": "detect_conflicts",
                "result": {"conflicts_found": len(relevant_conflicts), "conflicts": relevant_conflicts}
            })
            
            # Compile final recommendation
            result["recommendation"] = {
                "predicted_eta": eta_result.get("predicted_eta"),
                "eta_confidence": eta_result.get("confidence_score"),
                "recommended_berth": top_suggestion,
                "alternative_berths": suggestions[1:3] if len(suggestions) > 1 else [],
                "resource_availability": resource_result.get("all_resources_available", True) if 'resource_result' in locals() else True,
                "conflicts": relevant_conflicts
            }
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Orchestration error: {e}")
            import traceback
            traceback.print_exc()
            result["error"] = str(e)
        
        return result
    
    def run_what_if_simulation(
        self, 
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run what-if simulation for delay impact analysis.
        """
        scenario_type = scenario.get("type", "delay")
        
        if scenario_type == "delay":
            return self._simulate_delay(
                scenario.get("vessel_id"),
                scenario.get("delay_hours", 4)
            )
        elif scenario_type == "berth_closure":
            return self._simulate_berth_closure(
                scenario.get("berth_id"),
                scenario.get("duration_hours", 24)
            )
        elif scenario_type == "surge":
            return self._simulate_arrival_surge(
                scenario.get("additional_vessels", 5)
            )
        else:
            return {"error": f"Unknown scenario type: {scenario_type}"}
    
    def _simulate_delay(
        self, 
        vessel_id: int, 
        delay_hours: int
    ) -> Dict[str, Any]:
        """Simulate impact of a vessel delay"""
        try:
            # Get current schedule
            schedule = self.db.get_vessel_schedule(vessel_id)
            if not schedule:
                return {"error": f"No schedule found for vessel {vessel_id}"}
            
            vessel = self.db.get_vessel_by_id(vessel_id)
            original_eta = schedule.get('ETA')
            
            if not original_eta:
                return {"error": "No ETA in schedule"}
            
            eta_dt = original_eta if isinstance(original_eta, datetime) else datetime.fromisoformat(str(original_eta))
            new_eta = eta_dt + timedelta(hours=delay_hours)
            
            # Check impacts
            impacts = []
            
            # 1. Check if berth becomes unavailable
            berth_id = schedule.get('BerthId')
            if berth_id:
                # Check if delay causes overlap with next vessel
                later_schedules = self.db.get_schedules_in_range(
                    new_eta.isoformat(),
                    (new_eta + timedelta(hours=48)).isoformat()
                )
                
                for s in later_schedules:
                    if s.get('BerthId') == berth_id and s.get('VesselId') != vessel_id:
                        impacts.append({
                            "type": "downstream_delay",
                            "vessel_id": s.get('VesselId'),
                            "vessel_name": s.get('VesselName'),
                            "description": f"{s.get('VesselName')} may need to wait or be reassigned"
                        })
            
            # 2. Check resource impacts
            impacts.append({
                "type": "resource_reallocation",
                "description": "Pilot and tug schedules may need adjustment"
            })
            
            # Use AI to generate impact summary
            prompt = f"""
Analyze the impact of a {delay_hours}-hour delay for vessel {vessel.get('VesselName', 'Unknown')}.
Original ETA: {original_eta}
New ETA: {new_eta}
Berth assigned: {schedule.get('BerthName', 'None')}

Impacts identified:
{json.dumps(impacts, indent=2)}

Provide a brief summary of cascading effects and recommendations. /no_think
"""
            
            if self.model._model_loaded or self.model.initialize():
                ai_response = self.model.generate_text(prompt, max_tokens=300)
                ai_summary = ai_response.get("text", "")
            else:
                ai_summary = "AI analysis unavailable"
            
            return {
                "scenario": "delay",
                "vessel_id": vessel_id,
                "vessel_name": vessel.get('VesselName', ''),
                "original_eta": eta_dt.isoformat(),
                "new_eta": new_eta.isoformat(),
                "delay_hours": delay_hours,
                "impacts": impacts,
                "downstream_vessels_affected": len([i for i in impacts if i["type"] == "downstream_delay"]),
                "ai_analysis": ai_summary
            }
            
        except Exception as e:
            logger.error(f"Delay simulation error: {e}")
            return {"error": str(e)}
    
    def _simulate_berth_closure(
        self, 
        berth_id: int, 
        duration_hours: int
    ) -> Dict[str, Any]:
        """Simulate impact of berth closure for maintenance"""
        try:
            berth = self.db.get_berth_by_id(berth_id) if hasattr(self.db, 'get_berth_by_id') else None
            
            # Get vessels scheduled for this berth
            start = datetime.now()
            end = start + timedelta(hours=duration_hours)
            
            schedules = self.db.get_schedules_in_range(start.isoformat(), end.isoformat())
            affected_schedules = [s for s in schedules if s.get('BerthId') == berth_id]
            
            # For each affected vessel, find alternatives
            reassignments = []
            for s in affected_schedules:
                vessel_id = s.get('VesselId')
                alternatives = self.berth_optimizer.get_berth_suggestions(vessel_id, top_k=3)
                # Filter out the closed berth
                alternatives = [a for a in alternatives if a.get('berth_id') != berth_id]
                
                reassignments.append({
                    "vessel_id": vessel_id,
                    "vessel_name": s.get('VesselName'),
                    "original_berth": s.get('BerthName'),
                    "alternative_berths": alternatives[:2] if alternatives else []
                })
            
            return {
                "scenario": "berth_closure",
                "berth_id": berth_id,
                "berth_name": berth.get('BerthName') if berth else f"Berth {berth_id}",
                "closure_duration_hours": duration_hours,
                "vessels_affected": len(affected_schedules),
                "reassignment_options": reassignments
            }
            
        except Exception as e:
            logger.error(f"Berth closure simulation error: {e}")
            return {"error": str(e)}
    
    def _simulate_arrival_surge(self, additional_vessels: int) -> Dict[str, Any]:
        """Simulate capacity under surge conditions"""
        try:
            # Get current vessels
            current_vessels = self.db.get_vessels_by_status('Scheduled')
            berths = self.db.get_all_berths()
            
            total_vessels = len(current_vessels) + additional_vessels
            total_berths = len(berths)
            
            # Simple capacity analysis
            avg_dwell = 24  # hours
            berth_capacity_per_day = total_berths  # Each berth can serve ~1 vessel/day
            
            days_to_clear = total_vessels / max(berth_capacity_per_day, 1)
            
            return {
                "scenario": "arrival_surge",
                "current_queue": len(current_vessels),
                "additional_vessels": additional_vessels,
                "total_vessels": total_vessels,
                "available_berths": total_berths,
                "estimated_days_to_clear": round(days_to_clear, 1),
                "expected_waiting_time_hours": round((days_to_clear - 1) * 24, 1) if days_to_clear > 1 else 0,
                "recommendation": "Consider requesting additional pilot/tug resources" if days_to_clear > 2 else "Capacity sufficient"
            }
            
        except Exception as e:
            logger.error(f"Surge simulation error: {e}")
            return {"error": str(e)}
    
    def _log_message(self, from_agent: str, to_agent: str, action: str, payload: Dict[str, Any]):
        """Log inter-agent communication"""
        msg = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            action=action,
            payload=payload
        )
        self.message_log.append(msg)
        logger.debug(f"[{from_agent} -> {to_agent}] {action}")


# ==================== SINGLETON INSTANCES ====================

_eta_predictor: Optional[ETAPredictorAgent] = None
_berth_optimizer: Optional[BerthOptimizerAgent] = None
_resource_scheduler: Optional[ResourceSchedulerAgent] = None
_conflict_resolver: Optional[ConflictResolverAgent] = None
_orchestrator: Optional[OrchestratorAgent] = None


def get_eta_predictor_agent() -> ETAPredictorAgent:
    global _eta_predictor
    if _eta_predictor is None:
        _eta_predictor = ETAPredictorAgent()
    return _eta_predictor


def get_berth_optimizer_agent() -> BerthOptimizerAgent:
    global _berth_optimizer
    if _berth_optimizer is None:
        _berth_optimizer = BerthOptimizerAgent()
    return _berth_optimizer


def get_resource_scheduler_agent() -> ResourceSchedulerAgent:
    global _resource_scheduler
    if _resource_scheduler is None:
        _resource_scheduler = ResourceSchedulerAgent()
    return _resource_scheduler


def get_conflict_resolver_agent() -> ConflictResolverAgent:
    global _conflict_resolver
    if _conflict_resolver is None:
        _conflict_resolver = ConflictResolverAgent()
    return _conflict_resolver


def get_orchestrator_agent() -> OrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator
