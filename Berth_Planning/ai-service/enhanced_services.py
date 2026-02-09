"""
SmartBerth AI Service - Enhanced Services Integration Layer
Integrates Feature Engineering, Heuristics, and ML Models into unified services

This module bridges the AI layers with the REST API endpoints:
1. Feature Engineering → Extracts features from vessel/berth/weather data
2. Heuristics → Constraint solving, optimization algorithms
3. ML Models → ETA prediction, dwell time, anomaly detection
4. LLM Integration → Natural language explanations via Claude API
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

from database import get_db_service
from model import get_model

# Import new AI layers
from feature_engineering import (
    FeatureExtractor, 
    get_feature_extractor,
    TemporalFeatures,
    SpatialFeatures,
    VesselFeatures,
    WeatherFeatures,
    UKCFeatures,
    BerthMatchFeatures
)

from heuristics import (
    SmartBerthHeuristics,
    get_heuristics_engine,
    AllocationSolution,
    VesselRequest,
    ConflictDetection,
    OptimizationObjective
)

from ml_models import (
    SmartBerthMLService,
    get_ml_service,
    ETAPrediction,
    DwellTimePrediction,
    AnomalyResult,
    BerthScore as MLBerthScore,
    TrafficForecast
)

logger = logging.getLogger(__name__)


# ============================================================================
# ENHANCED DATA CLASSES
# ============================================================================

@dataclass
class SmartBerthPrediction:
    """Comprehensive prediction result combining all AI layers"""
    vessel_id: int
    vessel_name: str
    
    # ETA Prediction
    eta_prediction: Optional[Dict[str, Any]] = None
    
    # Dwell Time
    dwell_prediction: Optional[Dict[str, Any]] = None
    
    # UKC Safety
    ukc_analysis: Optional[Dict[str, Any]] = None
    
    # Anomaly Detection
    anomaly_status: Optional[Dict[str, Any]] = None
    
    # Recommended Berths
    berth_recommendations: List[Dict[str, Any]] = None
    
    # Resource Requirements
    resource_requirements: Optional[Dict[str, Any]] = None
    
    # AI Explanation
    ai_explanation: str = ""
    
    # Confidence & Metadata
    overall_confidence: float = 0.0
    processing_time_ms: float = 0.0
    models_used: List[str] = None


@dataclass
class ScheduleOptimizationResult:
    """Result of schedule optimization"""
    success: bool
    solution: Optional[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    cascading_effects: List[Dict[str, Any]]
    optimization_score: float
    execution_time_ms: float
    algorithm_used: str
    ai_explanation: str


# ============================================================================
# ENHANCED PREDICTION SERVICE
# ============================================================================

class EnhancedPredictionService:
    """
    Unified prediction service combining all AI layers.
    """
    
    def __init__(self):
        self.db = get_db_service()
        self.feature_extractor = get_feature_extractor(self.db)
        self.ml_service = get_ml_service()
        self._heuristics: Optional[SmartBerthHeuristics] = None
    
    @property
    def heuristics(self) -> SmartBerthHeuristics:
        """Lazy initialization of heuristics engine with berth data"""
        if self._heuristics is None:
            berths = self.db.get_all_berths()
            self._heuristics = SmartBerthHeuristics(berths)
        return self._heuristics
    
    def get_comprehensive_prediction(
        self,
        vessel_id: int,
        include_berth_suggestions: bool = True,
        include_ukc: bool = True,
        include_anomaly_check: bool = True
    ) -> SmartBerthPrediction:
        """
        Generate comprehensive AI-powered predictions for a vessel.
        Combines feature engineering, ML predictions, and heuristics.
        """
        start_time = datetime.now()
        models_used = []
        
        # Get vessel data
        vessel = self.db.get_vessel_by_id(vessel_id)
        if not vessel:
            return SmartBerthPrediction(
                vessel_id=vessel_id,
                vessel_name="Unknown",
                ai_explanation="Vessel not found in database"
            )
        
        vessel_name = vessel.get('VesselName', 'Unknown')
        
        # Extract vessel features
        vessel_features = self.feature_extractor.extract_vessel_features(vessel)
        models_used.append("feature_engineering")
        
        # Get AIS data for spatial features
        ais_data = self.db.get_latest_ais_for_vessel(vessel_id, limit=1)
        spatial_features = None
        if ais_data:
            latest_ais = ais_data[0]
            spatial_features = self.feature_extractor.extract_spatial_features(
                latitude=float(latest_ais.get('Latitude', 0)),
                longitude=float(latest_ais.get('Longitude', 0)),
                speed=float(latest_ais.get('Speed', 0) or 0),
                heading=float(latest_ais.get('Heading', 0) or 0)
            )
        
        # Get weather features
        weather_data = self.db.get_current_weather()
        weather_features = None
        if weather_data:
            weather_features = self.feature_extractor.extract_weather_features(weather_data)
        
        # Get temporal features
        temporal_features = self.feature_extractor.extract_temporal_features(
            datetime.now()
        )
        
        # ======= ETA PREDICTION =======
        eta_result = None
        if spatial_features:
            eta_prediction = self.ml_service.predict_eta(
                vessel_id=vessel_id,
                vessel_name=vessel_name,
                distance_nm=spatial_features.distance_to_port,
                speed_knots=spatial_features.speed_over_ground,
                weather_factor=weather_features.combined_weather_score if weather_features else 1.0
            )
            eta_result = {
                "predicted_eta": eta_prediction.predicted_eta.isoformat() if eta_prediction.predicted_eta else None,
                "deviation_minutes": eta_prediction.deviation_minutes,
                "confidence": eta_prediction.confidence,
                "method": eta_prediction.method,
                "factors": eta_prediction.factors
            }
            models_used.append("eta_ml_model")
        
        # ======= DWELL TIME PREDICTION =======
        dwell_result = self.ml_service.predict_dwell_time(
            vessel_id=vessel_id,
            vessel_type=vessel_features.vessel_type,
            cargo_quantity=vessel_features.cargo_quantity,
            cargo_unit=vessel_features.cargo_unit
        )
        dwell_prediction = {
            "predicted_dwell_minutes": dwell_result.predicted_dwell_minutes,
            "confidence": dwell_result.confidence,
            "interval": dwell_result.prediction_interval,
            "method": dwell_result.method
        }
        models_used.append("dwell_ml_model")
        
        # ======= UKC ANALYSIS =======
        ukc_result = None
        if include_ukc and spatial_features:
            # Determine channel based on berth type
            channel_depth = 13.1  # Default inner harbour
            if vessel_features.is_deep_draft_vessel:
                channel_depth = 16.5  # BMCT deep water
            
            tide_height = temporal_features.tide_height or 3.0
            
            ukc_features = self.feature_extractor.calculate_ukc_features(
                vessel_draft=vessel_features.draft,
                vessel_beam=vessel_features.beam,
                vessel_speed=spatial_features.speed_over_ground if spatial_features else 8.0,
                channel_depth=channel_depth,
                tide_height=tide_height,
                vessel_type=vessel_features.vessel_type,
                wave_height=weather_features.wave_height if weather_features else 0.5
            )
            ukc_result = {
                "is_safe": ukc_features.is_safe,
                "net_ukc": ukc_features.net_ukc,
                "ukc_percentage": ukc_features.ukc_percentage,
                "risk_level": ukc_features.risk_level,
                "recommendation": ukc_features.transit_recommendation
            }
            models_used.append("ukc_calculator")
        
        # ======= ANOMALY DETECTION =======
        anomaly_result = None
        if include_anomaly_check and spatial_features:
            # Generate feature vector for anomaly detection
            feature_vector = [
                spatial_features.distance_to_port,
                spatial_features.speed_over_ground,
                spatial_features.course_deviation,
                weather_features.wind_speed if weather_features else 10.0
            ]
            
            deviation = eta_result.get('deviation_minutes', 0) if eta_result else 0
            anomaly = self.ml_service.detect_anomaly(feature_vector, deviation)
            anomaly_result = {
                "is_anomaly": anomaly.is_anomaly,
                "anomaly_score": anomaly.anomaly_score,
                "anomaly_type": anomaly.anomaly_type,
                "explanation": anomaly.explanation
            }
            models_used.append("anomaly_detector")
        
        # ======= BERTH RECOMMENDATIONS =======
        berth_recommendations = []
        if include_berth_suggestions:
            berths = self.db.get_all_berths()
            if berths:
                scores = self.ml_service.score_berths(vessel, berths)
                berth_recommendations = [
                    {
                        "berth_id": s.berth_id,
                        "berth_code": s.berth_code,
                        "score": s.score,
                        "components": s.components,
                        "waiting_time_estimate": s.waiting_time_estimate,
                        "recommendation": s.recommendation
                    }
                    for s in scores[:5]  # Top 5
                ]
                models_used.append("berth_scoring_model")
        
        # ======= RESOURCE REQUIREMENTS =======
        resource_requirements = {
            "tugs_required": vessel_features.tugs_required,
            "pilot_class": vessel_features.pilot_class_required,
            "estimated_cranes": min(4, int(vessel_features.cargo_quantity / 2000) + 1) if vessel_features.cargo_quantity > 0 else 2
        }
        
        # ======= GENERATE AI EXPLANATION =======
        ai_explanation = self._generate_comprehensive_explanation(
            vessel_name=vessel_name,
            vessel_features=vessel_features,
            spatial_features=spatial_features,
            eta_result=eta_result,
            dwell_prediction=dwell_prediction,
            ukc_result=ukc_result,
            anomaly_result=anomaly_result,
            berth_recommendations=berth_recommendations
        )
        
        # Calculate overall confidence
        confidences = [
            eta_result.get('confidence', 0) if eta_result else 0,
            dwell_prediction.get('confidence', 0),
        ]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 50.0
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SmartBerthPrediction(
            vessel_id=vessel_id,
            vessel_name=vessel_name,
            eta_prediction=eta_result,
            dwell_prediction=dwell_prediction,
            ukc_analysis=ukc_result,
            anomaly_status=anomaly_result,
            berth_recommendations=berth_recommendations,
            resource_requirements=resource_requirements,
            ai_explanation=ai_explanation,
            overall_confidence=overall_confidence,
            processing_time_ms=processing_time,
            models_used=models_used
        )
    
    def _generate_comprehensive_explanation(
        self,
        vessel_name: str,
        vessel_features: VesselFeatures,
        spatial_features: Optional[SpatialFeatures],
        eta_result: Optional[Dict],
        dwell_prediction: Dict,
        ukc_result: Optional[Dict],
        anomaly_result: Optional[Dict],
        berth_recommendations: List[Dict]
    ) -> str:
        """Generate comprehensive AI explanation using LLM"""
        
        # Build context summary
        context_parts = [f"Analysis for {vessel_name} ({vessel_features.vessel_type}, {vessel_features.loa}m LOA):"]
        
        if spatial_features:
            context_parts.append(
                f"Currently {spatial_features.distance_to_port:.1f} NM from port, "
                f"speed {spatial_features.speed_over_ground:.1f} knots, "
                f"zone: {spatial_features.zone_category}"
            )
        
        if eta_result:
            confidence = eta_result.get('confidence', 0)
            deviation = eta_result.get('deviation_minutes', 0)
            status = "on time" if abs(deviation) < 30 else f"{'delayed' if deviation > 0 else 'early'} by {abs(deviation):.0f} minutes"
            context_parts.append(f"ETA prediction: {status} ({confidence:.0f}% confidence)")
        
        context_parts.append(
            f"Expected dwell time: {dwell_prediction.get('predicted_dwell_minutes', 0) / 60:.1f} hours"
        )
        
        if ukc_result:
            safety = "SAFE" if ukc_result.get('is_safe') else "UNSAFE"
            context_parts.append(f"UKC status: {safety} ({ukc_result.get('risk_level', 'Unknown')} risk)")
        
        if anomaly_result and anomaly_result.get('is_anomaly'):
            context_parts.append(f"⚠️ Anomaly detected: {anomaly_result.get('anomaly_type', 'unknown')}")
        
        if berth_recommendations:
            top_berth = berth_recommendations[0]
            context_parts.append(
                f"Top berth recommendation: {top_berth.get('berth_code', 'N/A')} "
                f"(score: {top_berth.get('score', 0):.1f})"
            )
        
        # Try to enhance with LLM
        try:
            model = get_model()
            if model.model is not None:
                prompt = f"""Summarize this vessel analysis in 2-3 sentences for a port operator:
{chr(10).join(context_parts)}

Focus on: arrival status, safety, and recommended actions."""
                
                result = model.generate_text(
                    prompt=prompt,
                    system_prompt="You are a maritime operations AI. Be concise and actionable.",
                    max_tokens=150,
                    temperature=0.5
                )
                if result.get("success"):
                    return result.get("text", " ".join(context_parts))
        except Exception as e:
            logger.warning(f"LLM explanation failed: {e}")
        
        return " ".join(context_parts)


# ============================================================================
# ENHANCED OPTIMIZATION SERVICE
# ============================================================================

class EnhancedOptimizationService:
    """
    Schedule optimization service using heuristics and ML.
    """
    
    def __init__(self):
        self.db = get_db_service()
        self._heuristics: Optional[SmartBerthHeuristics] = None
        self.ml_service = get_ml_service()
    
    @property
    def heuristics(self) -> SmartBerthHeuristics:
        """Lazy initialization of heuristics engine"""
        if self._heuristics is None:
            berths = self.db.get_all_berths()
            self._heuristics = SmartBerthHeuristics(berths)
        return self._heuristics
    
    def optimize_schedule(
        self,
        vessel_ids: Optional[List[int]] = None,
        time_horizon_hours: int = 48,
        objective: str = "balanced",
        use_genetic_algorithm: bool = False
    ) -> ScheduleOptimizationResult:
        """
        Optimize berth schedule for given vessels or all pending vessels.
        """
        start_time = datetime.now()
        
        # Get vessels to optimize
        if vessel_ids:
            vessels = [self.db.get_vessel_by_id(vid) for vid in vessel_ids]
            vessels = [v for v in vessels if v]
        else:
            # Get all vessels expected within time horizon
            vessels = self.db.get_pending_vessels(
                from_time=datetime.now().isoformat(),
                until_time=(datetime.now() + timedelta(hours=time_horizon_hours)).isoformat()
            )
        
        if not vessels:
            return ScheduleOptimizationResult(
                success=False,
                solution=None,
                conflicts=[],
                cascading_effects=[],
                optimization_score=0,
                execution_time_ms=0,
                algorithm_used="none",
                ai_explanation="No vessels found for optimization"
            )
        
        # Convert to vessel dicts for heuristics
        vessel_dicts = []
        for v in vessels:
            # Get schedule info for ETA
            schedules = self.db.get_schedules_by_vessel(v['VesselId'])
            eta = None
            dwell = 720
            if schedules:
                eta = schedules[0].get('ETA')
                dwell = schedules[0].get('EstimatedDwellTime', 720)
            
            vessel_dicts.append({
                **v,
                'ETA': eta or datetime.now() + timedelta(hours=24),
                'EstimatedDwellTime': dwell
            })
        
        # Map objective
        obj_map = {
            'balanced': OptimizationObjective.BALANCED,
            'waiting_time': OptimizationObjective.MINIMIZE_WAITING_TIME,
            'utilization': OptimizationObjective.MAXIMIZE_BERTH_UTILIZATION,
            'conflicts': OptimizationObjective.MINIMIZE_CONFLICTS
        }
        optimization_objective = obj_map.get(objective, OptimizationObjective.BALANCED)
        
        # Run optimization
        if use_genetic_algorithm:
            solution = self.heuristics.optimize_schedule(vessel_dicts, optimization_objective)
            algorithm = "genetic_algorithm"
        else:
            solution = self.heuristics.priority_allocate(vessel_dicts)
            algorithm = "priority_based"
        
        # Detect conflicts
        conflicts = self.heuristics.detect_conflicts(solution, vessel_dicts)
        conflict_dicts = [
            {
                "type": c.conflict_type.value,
                "vessels": c.vessel_ids,
                "berth": c.berth_id,
                "severity": c.severity,
                "description": c.description,
                "resolution_options": c.resolution_options
            }
            for c in conflicts
        ]
        
        # Convert solution
        solution_dict = {
            "assignments": solution.assignments,
            "start_times": {k: v.isoformat() for k, v in solution.start_times.items()},
            "end_times": {k: v.isoformat() for k, v in solution.end_times.items()},
            "total_waiting_time_minutes": solution.total_waiting_time,
            "is_feasible": solution.is_feasible,
            "fitness_score": solution.fitness_score
        }
        
        # Generate explanation
        ai_explanation = self._generate_optimization_explanation(
            len(vessel_dicts), solution, conflicts, algorithm
        )
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ScheduleOptimizationResult(
            success=solution.is_feasible,
            solution=solution_dict,
            conflicts=conflict_dicts,
            cascading_effects=[],
            optimization_score=solution.fitness_score,
            execution_time_ms=execution_time,
            algorithm_used=algorithm,
            ai_explanation=ai_explanation
        )
    
    def handle_vessel_delay(
        self,
        vessel_id: int,
        new_eta: datetime
    ) -> ScheduleOptimizationResult:
        """
        Re-optimize schedule when a vessel is delayed.
        """
        start_time = datetime.now()
        
        # Get current schedule solution (would need to reconstruct from DB)
        # For now, get all scheduled vessels
        vessels = self.db.get_pending_vessels(
            from_time=datetime.now().isoformat(),
            until_time=(datetime.now() + timedelta(hours=72)).isoformat()
        )
        
        if not vessels:
            return ScheduleOptimizationResult(
                success=False,
                solution=None,
                conflicts=[],
                cascading_effects=[],
                optimization_score=0,
                execution_time_ms=0,
                algorithm_used="none",
                ai_explanation="No scheduled vessels found"
            )
        
        # Re-run optimization with updated ETA
        vessel_dicts = []
        for v in vessels:
            schedules = self.db.get_schedules_by_vessel(v['VesselId'])
            eta = new_eta if v['VesselId'] == vessel_id else None
            if schedules and not eta:
                eta = schedules[0].get('ETA')
            
            vessel_dicts.append({
                **v,
                'ETA': eta or datetime.now() + timedelta(hours=24),
                'EstimatedDwellTime': schedules[0].get('EstimatedDwellTime', 720) if schedules else 720
            })
        
        # Optimize
        solution = self.heuristics.priority_allocate(vessel_dicts)
        
        # Identify cascading effects
        cascading_effects = []
        for vid, start in solution.start_times.items():
            vessel = next((v for v in vessel_dicts if v['VesselId'] == vid), None)
            if vessel and vessel.get('ETA'):
                original_eta = vessel['ETA']
                if isinstance(original_eta, str):
                    original_eta = datetime.fromisoformat(original_eta.replace('Z', '+00:00'))
                
                delay = (start - original_eta).total_seconds() / 60
                if delay > 30:  # More than 30 min delay
                    cascading_effects.append({
                        "vessel_id": vid,
                        "vessel_name": vessel.get('VesselName', 'Unknown'),
                        "delay_minutes": delay,
                        "reason": f"Cascaded from vessel {vessel_id} delay"
                    })
        
        conflicts = self.heuristics.detect_conflicts(solution, vessel_dicts)
        conflict_dicts = [
            {
                "type": c.conflict_type.value,
                "vessels": c.vessel_ids,
                "severity": c.severity,
                "description": c.description
            }
            for c in conflicts
        ]
        
        solution_dict = {
            "assignments": solution.assignments,
            "start_times": {k: v.isoformat() for k, v in solution.start_times.items()},
            "end_times": {k: v.isoformat() for k, v in solution.end_times.items()},
            "total_waiting_time_minutes": solution.total_waiting_time,
            "is_feasible": solution.is_feasible
        }
        
        ai_explanation = f"Delay of vessel {vessel_id} to {new_eta.isoformat()} "
        if cascading_effects:
            ai_explanation += f"caused {len(cascading_effects)} cascading delays. "
        else:
            ai_explanation += "was absorbed without cascading impact. "
        ai_explanation += f"Schedule re-optimized with {len(conflicts)} conflicts detected."
        
        execution_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ScheduleOptimizationResult(
            success=solution.is_feasible,
            solution=solution_dict,
            conflicts=conflict_dicts,
            cascading_effects=cascading_effects,
            optimization_score=solution.fitness_score,
            execution_time_ms=execution_time,
            algorithm_used="re-optimization",
            ai_explanation=ai_explanation
        )
    
    def assign_resources(
        self,
        vessel_id: int,
        eta: datetime
    ) -> Dict[str, Any]:
        """
        Optimal resource (pilot/tug) assignment for a vessel.
        """
        vessel = self.db.get_vessel_by_id(vessel_id)
        if not vessel:
            return {"error": "Vessel not found"}
        
        # Get available resources
        pilots = self.db.get_available_resources('Pilot', eta.isoformat())
        tugs = self.db.get_available_resources('Tugboat', eta.isoformat())
        
        if not pilots and not tugs:
            return {
                "vessel_id": vessel_id,
                "assignments": [],
                "message": "No resources available at requested time"
            }
        
        # Create vessel dict for heuristics
        vessel_dict = {
            **vessel,
            'ETA': eta,
            'EstimatedDwellTime': 720
        }
        
        # Assign using Hungarian algorithm
        resources = []
        if pilots:
            resources.extend([
                {
                    "resource_id": p.get('PilotId', i),
                    "resource_type": "Pilot",
                    "resource_name": p.get('PilotName', f'Pilot-{i}'),
                    "pilot_class": p.get('PilotClass', 'III'),
                    "max_gt": p.get('MaxGT', 50000),
                    "is_available": True
                }
                for i, p in enumerate(pilots)
            ])
        
        if tugs:
            resources.extend([
                {
                    "resource_id": t.get('TugId', i + 100),
                    "resource_type": "Tugboat",
                    "resource_name": t.get('TugName', f'Tug-{i}'),
                    "bollard_pull": t.get('BollardPull', 50),
                    "is_available": True
                }
                for i, t in enumerate(tugs)
            ])
        
        assignments = self.heuristics.assign_resources([vessel_dict], resources)
        
        return {
            "vessel_id": vessel_id,
            "vessel_name": vessel.get('VesselName', 'Unknown'),
            "eta": eta.isoformat(),
            "assignments": [
                {
                    "resource_type": a.resource_type,
                    "resource_name": a.resource_name,
                    "start_time": a.start_time.isoformat(),
                    "end_time": a.end_time.isoformat(),
                    "status": a.status
                }
                for a in assignments
            ],
            "message": f"Assigned {len(assignments)} resources using Hungarian algorithm"
        }
    
    def _generate_optimization_explanation(
        self,
        vessel_count: int,
        solution: AllocationSolution,
        conflicts: List[ConflictDetection],
        algorithm: str
    ) -> str:
        """Generate natural language explanation for optimization result"""
        parts = [f"Optimized schedule for {vessel_count} vessels using {algorithm}."]
        
        if solution.is_feasible:
            parts.append(f"All vessels assigned successfully.")
            parts.append(f"Total waiting time: {solution.total_waiting_time:.0f} minutes.")
        else:
            parts.append(f"⚠️ Some vessels could not be assigned.")
        
        if conflicts:
            parts.append(f"Detected {len(conflicts)} conflict(s) requiring attention.")
        else:
            parts.append("No conflicts detected.")
        
        return " ".join(parts)


# ============================================================================
# ENHANCED TRAFFIC ANALYSIS SERVICE
# ============================================================================

class EnhancedTrafficService:
    """
    Traffic analysis and forecasting service.
    """
    
    def __init__(self):
        self.db = get_db_service()
        self.ml_service = get_ml_service()
    
    def get_traffic_forecast(
        self,
        hours_ahead: int = 24
    ) -> Dict[str, Any]:
        """
        Get traffic forecast for the port.
        """
        # Update forecaster with current data
        # In production, this would use historical DB data
        
        forecasts = self.ml_service.forecast_traffic(hours_ahead)
        
        return {
            "forecasts": [
                {
                    "timestamp": f.timestamp.isoformat(),
                    "vessel_count": f.vessel_count,
                    "berth_utilization": f.berth_utilization,
                    "confidence": f.confidence,
                    "trend": f.trend
                }
                for f in forecasts
            ],
            "summary": {
                "peak_hour": max(forecasts, key=lambda f: f.vessel_count).timestamp.isoformat() if forecasts else None,
                "average_utilization": sum(f.berth_utilization for f in forecasts) / len(forecasts) if forecasts else 0,
                "trend": forecasts[0].trend if forecasts else "stable"
            }
        }
    
    def get_current_port_status(self) -> Dict[str, Any]:
        """
        Get current port status with AI insights.
        """
        # Get vessel counts
        berthed = self.db.get_berthed_vessels()
        approaching = self.db.get_approaching_vessels()
        
        # Get resource availability
        now = datetime.now().isoformat()
        pilots = self.db.get_available_resources('Pilot', now)
        tugs = self.db.get_available_resources('Tugboat', now)
        
        # Get weather
        weather = self.db.get_current_weather()
        
        # Build status
        status = {
            "timestamp": datetime.now().isoformat(),
            "vessels": {
                "berthed": len(berthed) if berthed else 0,
                "approaching": len(approaching) if approaching else 0
            },
            "resources": {
                "pilots_available": len(pilots) if pilots else 0,
                "tugs_available": len(tugs) if tugs else 0
            },
            "weather": {
                "condition": weather.get('WeatherCondition', 'Unknown') if weather else 'Unknown',
                "wind_speed": weather.get('WindSpeed', 0) if weather else 0,
                "visibility": weather.get('Visibility', 0) if weather else 0,
                "is_operations_restricted": False
            },
            "berth_utilization": self._calculate_utilization(berthed)
        }
        
        # Check for weather restrictions
        if weather:
            if weather.get('WindSpeed', 0) > 25 or weather.get('Visibility', 10) < 0.5:
                status['weather']['is_operations_restricted'] = True
        
        return status
    
    def _calculate_utilization(self, berthed_vessels) -> float:
        """Calculate berth utilization percentage"""
        total_berths = 20  # JNPT has approximately 20 berths
        if not berthed_vessels:
            return 0.0
        return (len(berthed_vessels) / total_berths) * 100


# ============================================================================
# SERVICE INSTANCES
# ============================================================================

_prediction_service: Optional[EnhancedPredictionService] = None
_optimization_service: Optional[EnhancedOptimizationService] = None
_traffic_service: Optional[EnhancedTrafficService] = None


def get_prediction_service() -> EnhancedPredictionService:
    """Get enhanced prediction service singleton"""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = EnhancedPredictionService()
    return _prediction_service


def get_optimization_service() -> EnhancedOptimizationService:
    """Get enhanced optimization service singleton"""
    global _optimization_service
    if _optimization_service is None:
        _optimization_service = EnhancedOptimizationService()
    return _optimization_service


def get_traffic_service() -> EnhancedTrafficService:
    """Get enhanced traffic service singleton"""
    global _traffic_service
    if _traffic_service is None:
        _traffic_service = EnhancedTrafficService()
    return _traffic_service
