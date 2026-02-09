"""
SmartBerth AI Service - Berth Planning Intelligence
Core AI services for ETA prediction, constraint validation, and berth allocation
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math

from database import get_db_service
from model import get_model

logger = logging.getLogger(__name__)


class ConstraintType(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class ConstraintCategory(str, Enum):
    PHYSICAL = "physical"
    CARGO = "cargo"
    READINESS = "readiness"
    TIDAL = "tidal"
    WEATHER = "weather"
    PRIORITY = "priority"
    COMMERCIAL = "commercial"


@dataclass
class ConstraintViolation:
    """Represents a constraint violation"""
    constraint_name: str
    category: ConstraintCategory
    constraint_type: ConstraintType
    description: str
    severity: int  # 1-10
    vessel_value: Any
    berth_limit: Any


@dataclass
class BerthScore:
    """Score for a berth allocation option"""
    berth_id: int
    berth_name: str
    terminal_name: str
    total_score: float
    constraint_score: float
    utilization_score: float
    waiting_time_score: float
    priority_score: float
    violations: List[ConstraintViolation]
    is_feasible: bool
    explanation: str


@dataclass
class ETAPredictionResult:
    """Result of ETA prediction"""
    vessel_id: int
    vessel_name: str
    original_eta: Optional[datetime]
    predicted_eta: Optional[datetime]
    deviation_minutes: int
    confidence_score: float
    status: str  # "on_time", "early", "delayed"
    factors: Dict[str, Any]
    ai_explanation: str


# ============================================================================
# AI SCORING FORMULA DOCUMENTATION
# ============================================================================
# 
# TOTAL SCORE FORMULA:
# --------------------
# total_score = (
#     constraint_score * 0.4 +
#     utilization_score * 0.2 +
#     waiting_time_score * 0.3 +
#     priority_score * 0.1
# ) * 100
#
# INDIVIDUAL COMPONENT FORMULAS:
# ------------------------------
#
# 1. CONSTRAINT SCORE (Weight: 40%)
#    - Hard violations (LOA, Draft, Cargo incompatibility) → 0.0
#    - Soft violations → 1.0 - (violation_count * 0.1)
#    - No violations → 1.0
#
# 2. UTILIZATION SCORE (Weight: 20%)
#    Based on 48-hour window utilization analysis:
#    - Very underutilized (<30%): 0.72 + (util/0.30) * 0.08
#    - Low utilization (30-50%): 0.80 + ((util-0.30)/0.20) * 0.08
#    - Moderate (50-70%): 0.88 + ((util-0.50)/0.20) * 0.07 [OPTIMAL]
#    - High (70-85%): 0.85 - ((util-0.70)/0.15) * 0.10
#    - Very high (>85%): 0.75 - ((util-0.85)/0.15) * 0.20
#    
#    DETERMINISTIC VARIANCE:
#    variance = (berth_hash % 100 / 1250) - 0.04 + (minute_of_day / 2880)
#    Range: approximately -0.04 to +0.08
#
# 3. WAITING TIME SCORE (Weight: 30%)
#    Based on queue position and vessel type ahead:
#    - Container vessels: +6 hours
#    - Tankers: +8 hours
#    - Bulk carriers: +10 hours
#    - General cargo: +5 hours
#    
#    Wait time → Score mapping:
#    - 0-1 hours: 0.95 - (hours * 0.05)
#    - 1-4 hours: 0.90 - ((hours-1)/3) * 0.08
#    - 4-8 hours: 0.82 - ((hours-4)/4) * 0.12
#    - 8-16 hours: 0.70 - ((hours-8)/8) * 0.15
#    - 16-24 hours: 0.55 - ((hours-16)/8) * 0.12
#    - 24+ hours: 0.43 - ((hours-24)/24) * 0.08 [min: 0.35]
#    
#    DETERMINISTIC VARIANCE:
#    variance = (vessel_hash % 100 / 1667) - 0.03 + (berth_hash % 50 / 1667)
#    Range: approximately -0.03 to +0.06
#    
#    ADJUSTMENTS:
#    - Night arrival (00:00-06:00): -0.05
#    - Early morning (06:00-08:00): -0.02
#    - Weekend: -0.03
#    - Automated terminal: +0.05
#
# 4. PRIORITY SCORE (Weight: 10%)
#    - Critical: 1.0
#    - High: 0.8
#    - Normal: 0.6
#    - Low: 0.4
#
# ============================================================================


def get_scoring_formula_explanation() -> Dict[str, Any]:
    """
    Returns a comprehensive explanation of AI scoring formulas.
    This can be used by chatbot/agents to explain how scores are calculated.
    """
    return {
        "total_score": {
            "formula": "total = (constraint * 0.4 + utilization * 0.2 + waiting * 0.3 + priority * 0.1) * 100",
            "description": "Weighted combination of four components, scaled to 0-100"
        },
        "constraint_score": {
            "weight": 0.4,
            "description": "Physical and operational compatibility",
            "rules": [
                "Hard violations (LOA, Draft, Cargo mismatch) → 0.0",
                "Soft violations → 1.0 - (count * 0.1)",
                "No violations → 1.0"
            ]
        },
        "utilization_score": {
            "weight": 0.2,
            "description": "Berth capacity utilization in 48-hour window",
            "optimal_range": "50-70% utilization",
            "variance_formula": "berth_hash_variance + time_based_factor",
            "is_deterministic": True
        },
        "waiting_time_score": {
            "weight": 0.3,
            "description": "Estimated queue wait time impact",
            "factors": [
                "Queue position",
                "Vessel types ahead",
                "Priority multiplier",
                "Time of day",
                "Day of week"
            ],
            "variance_formula": "vessel_hash + berth_hash",
            "is_deterministic": True
        },
        "priority_score": {
            "weight": 0.1,
            "description": "Vessel priority level",
            "values": {
                "Critical": 1.0,
                "High": 0.8,
                "Normal": 0.6,
                "Low": 0.4
            }
        }
    }


class ConstraintValidator:
    """
    Validates berth allocation against all constraint layers:
    1. Vessel-Level (Physical, Cargo, Readiness)
    2. Berth/Terminal-Level
    3. Operational Resources
    4. Temporal & Environmental
    5. Policy & Commercial
    """
    
    def __init__(self):
        self.db = get_db_service()
    
    def validate_physical_constraints(
        self, 
        vessel: Dict[str, Any], 
        berth: Dict[str, Any]
    ) -> List[ConstraintViolation]:
        """Validate physical dimension constraints (HARD)"""
        violations = []
        
        # LOA Check
        vessel_loa = vessel.get('LOA', 0)
        berth_max_loa = berth.get('MaxLOA', 0)
        if vessel_loa > berth_max_loa:
            violations.append(ConstraintViolation(
                constraint_name="LOA_LIMIT",
                category=ConstraintCategory.PHYSICAL,
                constraint_type=ConstraintType.HARD,
                description=f"Vessel LOA ({vessel_loa}m) exceeds berth limit ({berth_max_loa}m)",
                severity=10,
                vessel_value=vessel_loa,
                berth_limit=berth_max_loa
            ))
        
        # Beam Check
        vessel_beam = vessel.get('Beam', 0)
        berth_max_beam = berth.get('MaxBeam', 0)
        if vessel_beam > berth_max_beam:
            violations.append(ConstraintViolation(
                constraint_name="BEAM_LIMIT",
                category=ConstraintCategory.PHYSICAL,
                constraint_type=ConstraintType.HARD,
                description=f"Vessel beam ({vessel_beam}m) exceeds berth limit ({berth_max_beam}m)",
                severity=10,
                vessel_value=vessel_beam,
                berth_limit=berth_max_beam
            ))
        
        # Draft Check
        vessel_draft = vessel.get('Draft', 0)
        berth_max_draft = berth.get('MaxDraft', 0)
        if vessel_draft > berth_max_draft:
            violations.append(ConstraintViolation(
                constraint_name="DRAFT_LIMIT",
                category=ConstraintCategory.PHYSICAL,
                constraint_type=ConstraintType.HARD,
                description=f"Vessel draft ({vessel_draft}m) exceeds berth depth ({berth_max_draft}m)",
                severity=10,
                vessel_value=vessel_draft,
                berth_limit=berth_max_draft
            ))
        
        return violations
    
    def validate_cargo_constraints(
        self, 
        vessel: Dict[str, Any], 
        berth: Dict[str, Any]
    ) -> List[ConstraintViolation]:
        """Validate cargo type compatibility constraints (HARD)"""
        violations = []
        
        vessel_type = vessel.get('VesselType', '').lower()
        berth_type = berth.get('BerthType', '').lower()
        
        # Type compatibility mapping
        compatibility = {
            'container': ['container', 'multipurpose', 'general'],
            'bulk': ['bulk', 'multipurpose', 'general'],
            'tanker': ['liquid', 'tanker', 'oil'],
            'roro': ['roro', 'ro-ro', 'multipurpose'],
            'general': ['general', 'multipurpose'],
        }
        
        compatible_berths = compatibility.get(vessel_type, ['multipurpose', 'general'])
        
        if berth_type and berth_type not in compatible_berths:
            violations.append(ConstraintViolation(
                constraint_name="CARGO_COMPATIBILITY",
                category=ConstraintCategory.CARGO,
                constraint_type=ConstraintType.HARD,
                description=f"Vessel type '{vessel_type}' not compatible with berth type '{berth_type}'",
                severity=10,
                vessel_value=vessel_type,
                berth_limit=berth_type
            ))
        
        return violations
    
    def validate_tidal_constraints(
        self,
        vessel: Dict[str, Any],
        eta: datetime
    ) -> List[ConstraintViolation]:
        """Validate tidal window constraints (HARD)"""
        violations = []
        
        vessel_draft = vessel.get('Draft', 0)
        
        # Get tidal data around ETA
        from_time = eta - timedelta(hours=2)
        until_time = eta + timedelta(hours=2)
        
        try:
            tidal_data = self.db.get_tidal_windows(
                from_time.isoformat(), 
                until_time.isoformat()
            )
            
            if tidal_data:
                # Find the closest tidal reading
                # Use tide height as a proxy for draft restriction
                # During low tide, available water depth is reduced
                for tide in tidal_data:
                    tide_height = tide.get('TideHeight', 0)
                    # During low tide, check if vessel draft exceeds available water depth
                    if tide.get('TideType') == 'LowTide' and tide_height and vessel_draft > tide_height:
                        violations.append(ConstraintViolation(
                            constraint_name="TIDAL_DRAFT_RESTRICTION",
                            category=ConstraintCategory.TIDAL,
                            constraint_type=ConstraintType.HARD,
                            description=f"Vessel draft ({vessel_draft}m) exceeds low tide water level ({tide_height}m) at {tide.get('TideTime')}",
                            severity=9,
                            vessel_value=vessel_draft,
                            berth_limit=tide_height
                        ))
                        break
        except Exception as e:
            logger.warning(f"Could not check tidal constraints: {e}")
        
        return violations
    
    def validate_weather_constraints(
        self,
        vessel: Dict[str, Any],
        operation_time: datetime
    ) -> List[ConstraintViolation]:
        """Validate weather constraints (HARD/SOFT)"""
        violations = []
        
        try:
            weather = self.db.get_current_weather()
            
            if weather:
                wind_speed = weather.get('WindSpeed', 0)
                visibility = weather.get('Visibility', 999)
                wave_height = weather.get('WaveHeight', 0)
                
                vessel_gt = vessel.get('GrossTonnage', 0)
                
                # Wind speed limits based on vessel size
                wind_limit = 25 if vessel_gt > 50000 else 30 if vessel_gt > 20000 else 35
                if wind_speed > wind_limit:
                    violations.append(ConstraintViolation(
                        constraint_name="WIND_SPEED_LIMIT",
                        category=ConstraintCategory.WEATHER,
                        constraint_type=ConstraintType.HARD,
                        description=f"Wind speed ({wind_speed} knots) exceeds safe limit ({wind_limit} knots) for vessel size",
                        severity=9,
                        vessel_value=vessel_gt,
                        berth_limit=wind_limit
                    ))
                
                # Visibility for pilot boarding
                if visibility < 0.5:  # Less than 500m
                    violations.append(ConstraintViolation(
                        constraint_name="VISIBILITY_LIMIT",
                        category=ConstraintCategory.WEATHER,
                        constraint_type=ConstraintType.HARD,
                        description=f"Visibility ({visibility} NM) too low for safe pilot boarding",
                        severity=8,
                        vessel_value=visibility,
                        berth_limit=0.5
                    ))
                
                # Wave height warning (soft)
                if wave_height > 1.5:
                    violations.append(ConstraintViolation(
                        constraint_name="WAVE_HEIGHT_WARNING",
                        category=ConstraintCategory.WEATHER,
                        constraint_type=ConstraintType.SOFT,
                        description=f"Wave height ({wave_height}m) may affect berthing operations",
                        severity=5,
                        vessel_value=wave_height,
                        berth_limit=1.5
                    ))
        except Exception as e:
            logger.warning(f"Could not check weather constraints: {e}")
        
        return violations
    
    def validate_resource_constraints(
        self,
        vessel: Dict[str, Any],
        eta: datetime
    ) -> List[ConstraintViolation]:
        """Validate resource availability constraints (HARD)"""
        violations = []
        
        try:
            # Check pilot availability
            pilots = self.db.get_available_resources('Pilot', eta.isoformat())
            if not pilots:
                violations.append(ConstraintViolation(
                    constraint_name="PILOT_UNAVAILABLE",
                    category=ConstraintCategory.READINESS,
                    constraint_type=ConstraintType.HARD,
                    description="No pilot available at requested time",
                    severity=9,
                    vessel_value="Required",
                    berth_limit="0 available"
                ))
            
            # Check tug availability based on vessel size
            vessel_gt = vessel.get('GrossTonnage', 0)
            tugs_required = 1 if vessel_gt < 20000 else 2 if vessel_gt < 50000 else 3
            
            tugs = self.db.get_available_resources('Tugboat', eta.isoformat())
            if len(tugs) < tugs_required:
                violations.append(ConstraintViolation(
                    constraint_name="TUG_SHORTAGE",
                    category=ConstraintCategory.READINESS,
                    constraint_type=ConstraintType.HARD,
                    description=f"Insufficient tugs: {len(tugs)} available, {tugs_required} required",
                    severity=8,
                    vessel_value=tugs_required,
                    berth_limit=len(tugs)
                ))
        except Exception as e:
            logger.warning(f"Could not check resource constraints: {e}")
        
        return violations
    
    def validate_priority_constraints(
        self,
        vessel: Dict[str, Any],
        schedule: Dict[str, Any]
    ) -> Tuple[float, List[ConstraintViolation]]:
        """
        Validate priority/commercial constraints (SOFT with weights)
        Returns (priority_score, violations)
        """
        violations = []
        priority_score = 1.0
        
        vessel_priority = vessel.get('Priority', 2)
        schedule_priority = schedule.get('Priority', 2)
        
        # Priority scoring
        if vessel_priority == 1 or schedule_priority == 1:
            priority_score = 1.5  # High priority bonus
        elif vessel_priority == 3 and schedule_priority == 3:
            priority_score = 0.8  # Low priority penalty
        
        # Check for perishable cargo
        cargo_type = vessel.get('CargoType', '').lower()
        if 'perishable' in cargo_type or 'reefer' in cargo_type:
            priority_score *= 1.3
            violations.append(ConstraintViolation(
                constraint_name="PERISHABLE_CARGO",
                category=ConstraintCategory.PRIORITY,
                constraint_type=ConstraintType.SOFT,
                description="Vessel carrying perishable cargo - prioritize allocation",
                severity=3,
                vessel_value=cargo_type,
                berth_limit="Priority boost applied"
            ))
        
        return priority_score, violations
    
    def validate_all_constraints(
        self,
        vessel: Dict[str, Any],
        berth: Dict[str, Any],
        schedule: Dict[str, Any],
        eta: Optional[datetime] = None
    ) -> Tuple[bool, List[ConstraintViolation], float]:
        """
        Validate all constraint layers.
        Returns (is_feasible, all_violations, priority_score)
        """
        all_violations = []
        
        # Layer 1: Physical constraints
        all_violations.extend(self.validate_physical_constraints(vessel, berth))
        
        # Layer 2: Cargo compatibility
        all_violations.extend(self.validate_cargo_constraints(vessel, berth))
        
        if eta:
            # Layer 3: Tidal constraints
            all_violations.extend(self.validate_tidal_constraints(vessel, eta))
            
            # Layer 4: Weather constraints
            all_violations.extend(self.validate_weather_constraints(vessel, eta))
            
            # Layer 5: Resource constraints
            all_violations.extend(self.validate_resource_constraints(vessel, eta))
        
        # Layer 6: Priority/Commercial (soft constraints)
        priority_score, priority_violations = self.validate_priority_constraints(vessel, schedule)
        all_violations.extend(priority_violations)
        
        # Check if any hard constraints are violated
        hard_violations = [v for v in all_violations if v.constraint_type == ConstraintType.HARD]
        is_feasible = len(hard_violations) == 0
        
        return is_feasible, all_violations, priority_score


class ETAPredictor:
    """
    AI-powered ETA prediction using Janus Pro 7B and historical data
    """
    
    # Mumbai Port coordinates
    PORT_LAT = 18.9388
    PORT_LON = 72.8354
    
    def __init__(self):
        self.db = get_db_service()
        self.model = get_model()
    
    def _haversine_distance(
        self, 
        lat1: float, lon1: float, 
        lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two coordinates in nautical miles"""
        R = 3440.065  # Earth's radius in nautical miles
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _get_weather_factor(self) -> float:
        """Get weather impact factor (0.5-1.0)"""
        try:
            weather = self.db.get_current_weather()
            if weather:
                wind = weather.get('WindSpeed', 0)
                wave = weather.get('WaveHeight', 0)
                
                # Calculate impact
                wind_impact = max(0.7, 1.0 - (wind / 100))
                wave_impact = max(0.8, 1.0 - (wave / 5))
                
                return min(wind_impact, wave_impact)
        except:
            pass
        return 1.0
    
    def predict_eta(self, vessel_id: int, schedule_id: Optional[int] = None) -> ETAPredictionResult:
        """
        Predict ETA for a vessel using AI analysis
        """
        vessel = self.db.get_vessel_by_id(vessel_id)
        if not vessel:
            return ETAPredictionResult(
                vessel_id=vessel_id,
                vessel_name="Unknown",
                original_eta=None,
                predicted_eta=None,
                deviation_minutes=0,
                confidence_score=0,
                status="unknown",
                factors={},
                ai_explanation="Vessel not found in database"
            )
        
        # Get schedule if available
        schedule = None
        original_eta = None
        if schedule_id:
            schedule = self.db.get_schedule_by_id(schedule_id)
            if schedule:
                original_eta = schedule.get('ETA')
        
        # Get latest AIS data
        ais_data = self.db.get_latest_ais_for_vessel(vessel_id, limit=5)
        
        # Get weather data for comprehensive analysis
        weather_data = self.db.get_current_weather()
        weather_impact = self._get_weather_factor()
        
        factors = {
            "distance_to_port": None,
            "current_speed": None,
            "average_speed": None,
            "weather_impact": weather_impact,
            "data_freshness": None,
            "prediction_method": "Fallback",
            "weather_condition": weather_data.get('Conditions', 'Unknown') if weather_data else 'Unknown',
            "wind_speed": weather_data.get('WindSpeed', 0) if weather_data else 0,
            "visibility": weather_data.get('Visibility', 10) if weather_data else 10,
            "confidence_factors": {}
        }
        
        predicted_eta = original_eta
        confidence = 35.0  # Base confidence for fallback
        status = "unknown"
        
        if ais_data:
            latest = ais_data[0]
            lat = float(latest.get('Latitude', 0))
            lon = float(latest.get('Longitude', 0))
            speed = float(latest.get('Speed', 0) or 0)
            recorded_at = latest.get('RecordedAt')
            
            # Calculate distance
            distance = self._haversine_distance(lat, lon, self.PORT_LAT, self.PORT_LON)
            factors["distance_to_port"] = round(distance, 2)
            factors["current_speed"] = speed
            
            # Calculate average speed from history
            if len(ais_data) > 1:
                speeds = [float(a.get('Speed', 0) or 0) for a in ais_data if a.get('Speed')]
                factors["average_speed"] = round(sum(speeds) / len(speeds), 2) if speeds else speed
            else:
                factors["average_speed"] = speed
            
            # Data freshness (minutes since last AIS)
            freshness_minutes = 999
            if recorded_at:
                freshness_minutes = (datetime.utcnow() - recorded_at).total_seconds() / 60
                factors["data_freshness"] = round(freshness_minutes, 1)
            
            # Calculate ETA
            if speed > 0.5:
                adjusted_speed = speed * factors["weather_impact"]
                hours_to_arrival = distance / adjusted_speed
                predicted_eta = datetime.utcnow() + timedelta(hours=hours_to_arrival)
                
                # ========== COMPREHENSIVE MULTI-FACTOR CONFIDENCE CALCULATION ==========
                # Based on Knowledge Base: ETA_Prediction_Knowledge.md Section 6
                
                confidence_scores = []
                confidence_breakdown = {}
                
                # Factor 1: Distance to port (closer = higher confidence)
                # < 50nm: 95%, < 100nm: 88%, < 200nm: 75%, < 500nm: 62%, > 500nm: 48%
                if distance < 50:
                    dist_conf = 95 - (distance / 50) * 7  # 95-88
                elif distance < 100:
                    dist_conf = 88 - ((distance - 50) / 50) * 13  # 88-75
                elif distance < 200:
                    dist_conf = 75 - ((distance - 100) / 100) * 13  # 75-62
                elif distance < 500:
                    dist_conf = 62 - ((distance - 200) / 300) * 14  # 62-48
                else:
                    dist_conf = max(35, 48 - ((distance - 500) / 500) * 13)  # 48-35
                confidence_scores.append(dist_conf)
                confidence_breakdown["distance"] = round(dist_conf, 1)
                
                # Factor 2: AIS data freshness (newer = higher confidence)
                # < 15min: 96%, < 30min: 89%, < 60min: 78%, < 360min: 58%, > 360min: 42%
                if freshness_minutes < 15:
                    fresh_conf = 96 - (freshness_minutes / 15) * 7  # 96-89
                elif freshness_minutes < 30:
                    fresh_conf = 89 - ((freshness_minutes - 15) / 15) * 11  # 89-78
                elif freshness_minutes < 60:
                    fresh_conf = 78 - ((freshness_minutes - 30) / 30) * 20  # 78-58
                elif freshness_minutes < 360:
                    fresh_conf = 58 - ((freshness_minutes - 60) / 300) * 16  # 58-42
                else:
                    fresh_conf = max(30, 42 - ((freshness_minutes - 360) / 360) * 12)  # 42-30
                confidence_scores.append(fresh_conf)
                confidence_breakdown["data_freshness"] = round(fresh_conf, 1)
                
                # Factor 3: Weather stability (clear = higher confidence)
                wind_speed = factors.get("wind_speed", 0)
                visibility = factors.get("visibility", 10)
                weather_condition = factors.get("weather_condition", "Unknown").lower()
                
                # Wind impact: 0-15: 92%, 15-25: 82%, 25-35: 68%, > 35: 52%
                if wind_speed < 15:
                    wind_conf = 92 - (wind_speed / 15) * 10
                elif wind_speed < 25:
                    wind_conf = 82 - ((wind_speed - 15) / 10) * 14
                elif wind_speed < 35:
                    wind_conf = 68 - ((wind_speed - 25) / 10) * 16
                else:
                    wind_conf = max(40, 52 - ((wind_speed - 35) / 20) * 12)
                
                # Visibility impact: > 5km: 90%, 3-5: 78%, 1-3: 62%, < 1: 45%
                if visibility > 5:
                    vis_conf = 90
                elif visibility > 3:
                    vis_conf = 78 + ((visibility - 3) / 2) * 12
                elif visibility > 1:
                    vis_conf = 62 + ((visibility - 1) / 2) * 16
                else:
                    vis_conf = max(35, 45 + (visibility * 17))
                
                # Weather condition modifier
                weather_modifier = 1.0
                if 'clear' in weather_condition or 'sunny' in weather_condition:
                    weather_modifier = 1.05
                elif 'storm' in weather_condition or 'heavy' in weather_condition:
                    weather_modifier = 0.85
                elif 'rain' in weather_condition or 'fog' in weather_condition:
                    weather_modifier = 0.92
                
                weather_conf = ((wind_conf + vis_conf) / 2) * weather_modifier
                weather_conf = max(35, min(95, weather_conf))
                confidence_scores.append(weather_conf)
                confidence_breakdown["weather"] = round(weather_conf, 1)
                
                # Factor 4: Speed consistency (stable = higher confidence)
                avg_speed = factors.get("average_speed", speed)
                speed_variance = abs(speed - avg_speed) / max(avg_speed, 1) if avg_speed > 0 else 0
                
                # Variance < 5%: 94%, < 10%: 85%, < 20%: 72%, < 30%: 58%, > 30%: 45%
                if speed_variance < 0.05:
                    speed_conf = 94 - (speed_variance / 0.05) * 9  # 94-85
                elif speed_variance < 0.10:
                    speed_conf = 85 - ((speed_variance - 0.05) / 0.05) * 13  # 85-72
                elif speed_variance < 0.20:
                    speed_conf = 72 - ((speed_variance - 0.10) / 0.10) * 14  # 72-58
                elif speed_variance < 0.30:
                    speed_conf = 58 - ((speed_variance - 0.20) / 0.10) * 13  # 58-45
                else:
                    speed_conf = max(35, 45 - ((speed_variance - 0.30) / 0.20) * 10)  # 45-35
                confidence_scores.append(speed_conf)
                confidence_breakdown["speed_consistency"] = round(speed_conf, 1)
                
                # Factor 5: Vessel type reliability (based on typical patterns)
                vessel_type = vessel.get('VesselType', '').lower()
                type_conf = 75  # Default
                if 'container' in vessel_type:
                    type_conf = 85  # Container vessels are typically reliable
                elif 'tanker' in vessel_type or 'bulk' in vessel_type:
                    type_conf = 78  # Tankers are moderately predictable
                elif 'cruise' in vessel_type or 'ferry' in vessel_type:
                    type_conf = 82  # Regular schedules
                elif 'lng' in vessel_type or 'lpg' in vessel_type:
                    type_conf = 80  # Specialized operations
                
                # Add some variance based on vessel size (larger = more predictable)
                vessel_loa = vessel.get('LOA', 0)
                if vessel_loa > 300:
                    type_conf += 5
                elif vessel_loa > 200:
                    type_conf += 2
                
                type_conf = min(92, type_conf)
                confidence_scores.append(type_conf)
                confidence_breakdown["vessel_reliability"] = round(type_conf, 1)
                
                # ========== WEIGHTED FINAL CONFIDENCE ==========
                # Weights: Distance 0.25, Freshness 0.25, Weather 0.20, Speed 0.20, Type 0.10
                weights = [0.25, 0.25, 0.20, 0.20, 0.10]
                weighted_confidence = sum(c * w for c, w in zip(confidence_scores, weights))
                
                # Apply prediction horizon adjustment (farther predictions = lower confidence)
                if hours_to_arrival > 24:
                    horizon_penalty = min(15, (hours_to_arrival - 24) / 24 * 10)
                    weighted_confidence -= horizon_penalty
                elif hours_to_arrival < 2:
                    weighted_confidence += 3  # Boost for imminent arrivals
                
                confidence = max(30, min(98, weighted_confidence))
                factors["confidence_factors"] = confidence_breakdown
                factors["prediction_method"] = "AI-Multi-Factor-Analysis"
            else:
                # Vessel stationary - different confidence model
                factors["prediction_method"] = "Stationary-Fallback"
                # Stationary vessels have inherently lower confidence
                base_stationary_conf = 42
                if freshness_minutes < 30:
                    base_stationary_conf += 8
                if distance < 10:
                    base_stationary_conf += 15  # Very close, likely anchored
                elif distance < 50:
                    base_stationary_conf += 5
                confidence = min(65, base_stationary_conf)
        
        # Calculate deviation
        deviation_minutes = 0
        if original_eta and predicted_eta:
            deviation_minutes = int((predicted_eta - original_eta).total_seconds() / 60)
            
            if deviation_minutes < -30:
                status = "early"
            elif deviation_minutes > 30:
                status = "delayed"
            else:
                status = "on_time"
        
        # Generate AI explanation
        ai_explanation = self._generate_eta_explanation(
            vessel, factors, deviation_minutes, status
        )
        
        return ETAPredictionResult(
            vessel_id=vessel_id,
            vessel_name=vessel.get('VesselName', 'Unknown'),
            original_eta=original_eta,
            predicted_eta=predicted_eta,
            deviation_minutes=deviation_minutes,
            confidence_score=round(confidence, 1),
            status=status,
            factors=factors,
            ai_explanation=ai_explanation
        )
    
    def _generate_eta_explanation(
        self,
        vessel: Dict[str, Any],
        factors: Dict[str, Any],
        deviation: int,
        status: str
    ) -> str:
        """Generate natural language explanation using AI model"""
        
        # Build context for AI
        context = f"""
        Vessel: {vessel.get('VesselName')}
        Type: {vessel.get('VesselType')}
        Distance to Port: {factors.get('distance_to_port', 'N/A')} NM
        Current Speed: {factors.get('current_speed', 'N/A')} knots
        Weather Impact Factor: {factors.get('weather_impact', 1.0)}
        Prediction Method: {factors.get('prediction_method')}
        Deviation: {deviation} minutes ({status})
        """
        
        # Try to use AI model for explanation
        try:
            model = get_model()
            # Initialize model if not already loaded
            if model.client is None:
                model.initialize()
            
            if model.client is not None:
                result = model.generate_text(
                    prompt=f"Generate a brief, professional explanation for this ETA prediction:\n{context}",
                    system_prompt="You are a maritime operations assistant. Provide concise, factual explanations for vessel ETA predictions. Keep responses under 100 words.",
                    max_tokens=150,
                    temperature=0.5
                )
                if result.get("success"):
                    return result.get("text", "")
        except Exception as e:
            logger.warning(f"AI explanation failed: {e}")
        
        # Fallback to rule-based explanation
        if status == "on_time":
            return f"Vessel is proceeding as scheduled. Current speed of {factors.get('current_speed', 'N/A')} knots maintains expected arrival time."
        elif status == "early":
            return f"Vessel may arrive {abs(deviation)} minutes early due to favorable conditions and current speed of {factors.get('current_speed', 'N/A')} knots."
        else:
            reasons = []
            if factors.get('weather_impact', 1.0) < 0.9:
                reasons.append("adverse weather conditions")
            if factors.get('current_speed', 0) < factors.get('average_speed', 0):
                reasons.append("reduced vessel speed")
            reason_text = " and ".join(reasons) if reasons else "operational factors"
            return f"Vessel may be delayed by {deviation} minutes due to {reason_text}."


class BerthAllocator:
    """
    AI-powered berth allocation with optimization
    """
    
    def __init__(self):
        self.db = get_db_service()
        self.validator = ConstraintValidator()
        self.predictor = ETAPredictor()
    
    def get_berth_suggestions(
        self,
        vessel_id: int,
        preferred_eta: Optional[datetime] = None,
        top_n: int = 5
    ) -> List[BerthScore]:
        """
        Get ranked berth suggestions for a vessel
        """
        vessel = self.db.get_vessel_by_id(vessel_id)
        if not vessel:
            return []
        
        # Get ETA
        eta = preferred_eta or datetime.utcnow() + timedelta(hours=24)
        
        # Get all active berths
        all_berths = self.db.get_all_berths()
        
        # Score each berth
        scored_berths = []
        
        for berth in all_berths:
            if not berth.get('IsActive', True):
                continue
            
            # Create mock schedule for validation
            mock_schedule = {'Priority': vessel.get('Priority', 2)}
            
            # Validate constraints
            is_feasible, violations, priority_score = self.validator.validate_all_constraints(
                vessel, berth, mock_schedule, eta
            )
            
            # Calculate scores
            constraint_score = self._calculate_constraint_score(violations)
            utilization_score = self._calculate_utilization_score(berth, eta)
            waiting_score = self._calculate_waiting_time_score(berth, vessel, eta)
            
            # Total score (weighted)
            total_score = (
                constraint_score * 0.4 +
                utilization_score * 0.2 +
                waiting_score * 0.3 +
                priority_score * 0.1
            ) * 100
            
            # Generate fast rule-based explanation for now (AI explanation generated after sorting)
            explanation = self._generate_fast_explanation(vessel, berth, is_feasible, violations, total_score)
            
            scored_berths.append(BerthScore(
                berth_id=berth['BerthId'],
                berth_name=berth['BerthName'],
                terminal_name=berth['TerminalName'],
                total_score=round(total_score, 1),
                constraint_score=round(constraint_score * 100, 1),
                utilization_score=round(utilization_score * 100, 1),
                waiting_time_score=round(waiting_score * 100, 1),
                priority_score=round(priority_score * 100, 1),
                violations=[asdict(v) for v in violations],
                is_feasible=is_feasible,
                explanation=explanation
            ))
        
        # Sort by feasibility first, then score
        scored_berths.sort(key=lambda x: (x.is_feasible, x.total_score), reverse=True)
        
        return scored_berths[:top_n]
    
    def _calculate_constraint_score(self, violations: List[ConstraintViolation]) -> float:
        """Calculate score based on constraint violations (1.0 = perfect)"""
        if not violations:
            return 1.0
        
        hard_violations = sum(1 for v in violations if v.constraint_type == ConstraintType.HARD)
        soft_violations = sum(1 for v in violations if v.constraint_type == ConstraintType.SOFT)
        
        if hard_violations > 0:
            return 0.0
        
        # Soft violations reduce score but don't make infeasible
        return max(0.5, 1.0 - (soft_violations * 0.1))
    
    def _calculate_utilization_score(self, berth: Dict[str, Any], eta: datetime) -> float:
        """Calculate berth utilization efficiency score based on actual schedule data"""
        try:
            berth_id = berth.get('BerthID') or berth.get('BerthId')
            berth_name = berth.get('BerthName', '')
            
            # Time window analysis: 24 hours before and after ETA
            window_start = eta - timedelta(hours=24)
            window_end = eta + timedelta(hours=24)
            
            # Get schedules for this berth in the time window (convert to ISO strings)
            all_schedules = self.db.get_schedules_in_range(
                window_start.isoformat(), 
                window_end.isoformat()
            )
            berth_schedules = [s for s in all_schedules 
                              if (s.get('BerthID') == berth_id or s.get('BerthId') == berth_id)]
            
            if not berth_schedules:
                # No schedules = berth is underutilized, high score for new allocation
                # Time of day factor: peak hours (08:00-18:00) vs off-peak
                hour = eta.hour
                if 8 <= hour <= 18:
                    base_score = 0.85  # Peak hours, underutilized berth = great choice
                elif 6 <= hour <= 8 or 18 <= hour <= 22:
                    base_score = 0.78  # Shoulder hours
                else:
                    base_score = 0.70  # Night hours
                
                # DETERMINISTIC variance based on berth characteristics and time
                # Formula: variance = (berth_id_hash % 100 / 1250) - 0.04 + (minute_of_day / 2880)
                # This gives consistent values per berth while adding time-based micro-variation
                berth_hash = hash(str(berth_id)) % 100
                minute_of_day = eta.hour * 60 + eta.minute
                variance = (berth_hash / 1250) - 0.04 + (minute_of_day / 2880)  # Range: ~-0.04 to ~0.08
                return round(min(0.95, max(0.58, base_score + variance)), 2)
            
            # Calculate actual utilization in window
            total_window_minutes = 48 * 60  # 48-hour window
            occupied_minutes = 0
            
            for schedule in berth_schedules:
                sched_start = schedule.get('StartTime', schedule.get('ETA'))
                sched_end = schedule.get('EndTime', schedule.get('ETD'))
                
                if sched_start and sched_end:
                    # Clip to our window
                    effective_start = max(sched_start, window_start)
                    effective_end = min(sched_end, window_end)
                    if effective_end > effective_start:
                        occupied_minutes += (effective_end - effective_start).total_seconds() / 60
            
            current_utilization = occupied_minutes / total_window_minutes
            
            # Optimal utilization is 70-85%
            # Score higher for underutilized berths (room for this vessel)
            # Score lower for overutilized (congested) or very underutilized (unpopular)
            if current_utilization < 0.30:
                # Very underutilized - might indicate issues, but available
                score = 0.72 + (current_utilization / 0.30) * 0.08  # 0.72 - 0.80
            elif current_utilization < 0.50:
                # Low utilization - good availability
                score = 0.80 + ((current_utilization - 0.30) / 0.20) * 0.08  # 0.80 - 0.88
            elif current_utilization < 0.70:
                # Moderate utilization - ideal range
                score = 0.88 + ((current_utilization - 0.50) / 0.20) * 0.07  # 0.88 - 0.95
            elif current_utilization < 0.85:
                # High utilization - still manageable
                score = 0.85 - ((current_utilization - 0.70) / 0.15) * 0.10  # 0.85 - 0.75
            else:
                # Very high utilization - congestion risk
                score = 0.75 - ((current_utilization - 0.85) / 0.15) * 0.20  # 0.75 - 0.55
            
            # Terminal type bonus (specialized terminals tend to be more efficient)
            terminal_name = berth.get('TerminalName', '').lower()
            if 'container' in terminal_name:
                score += 0.03
            elif 'bulk' in terminal_name or 'liquid' in terminal_name:
                score += 0.02
            
            return round(min(0.98, max(0.52, score)), 2)
            
        except Exception as e:
            logger.warning(f"Error calculating utilization score: {e}")
            return 0.75  # Reasonable fallback
    
    def _calculate_waiting_time_score(
        self, 
        berth: Dict[str, Any], 
        vessel: Dict[str, Any],
        eta: datetime
    ) -> float:
        """Calculate score based on estimated waiting time using queue analysis"""
        try:
            berth_id = berth.get('BerthID') or berth.get('BerthId')
            vessel_priority = vessel.get('Priority', 'Normal')
            
            # Handle priority as integer (from DB) or string
            if isinstance(vessel_priority, int):
                priority_map = {1: 'Critical', 2: 'High', 3: 'Normal', 4: 'Low'}
                vessel_priority = priority_map.get(vessel_priority, 'Normal')
            
            # Get active schedules for this berth
            active_schedules = self.db.get_active_schedules()
            berth_queue = [s for s in active_schedules 
                          if (s.get('BerthID') == berth_id or s.get('BerthId') == berth_id) 
                          and s.get('ETA', datetime.max) > datetime.utcnow()]
            
            # Sort by ETA to get queue order
            berth_queue.sort(key=lambda x: x.get('ETA', datetime.max))
            
            # Find the vessel's position if it were added
            vessels_ahead = sum(1 for s in berth_queue if s.get('ETA', datetime.max) <= eta)
            
            # Priority multiplier
            priority_multiplier = {
                'Critical': 0.5,   # Effectively cuts waiting time
                'High': 0.7,
                'Normal': 1.0,
                'Low': 1.3
            }.get(vessel_priority, 1.0)
            
            # Base waiting time estimate (hours)
            # Each vessel ahead adds ~4-8 hours depending on type
            estimated_wait_hours = 0
            for schedule in berth_queue[:vessels_ahead]:
                vessel_type = schedule.get('VesselType', '').lower()
                if 'container' in vessel_type:
                    estimated_wait_hours += 6  # Container ops
                elif 'tanker' in vessel_type:
                    estimated_wait_hours += 8  # Tanker loading/unloading
                elif 'bulk' in vessel_type:
                    estimated_wait_hours += 10  # Bulk cargo
                else:
                    estimated_wait_hours += 5  # General cargo
            
            estimated_wait_hours *= priority_multiplier
            
            # Score based on waiting time
            # 0 hours = 0.95, 4 hours = 0.85, 8 hours = 0.72, 16 hours = 0.58, 24+ = 0.45
            if estimated_wait_hours < 1:
                base_score = 0.95 - (estimated_wait_hours * 0.05)  # 0.95 - 0.90
            elif estimated_wait_hours < 4:
                base_score = 0.90 - ((estimated_wait_hours - 1) / 3) * 0.08  # 0.90 - 0.82
            elif estimated_wait_hours < 8:
                base_score = 0.82 - ((estimated_wait_hours - 4) / 4) * 0.12  # 0.82 - 0.70
            elif estimated_wait_hours < 16:
                base_score = 0.70 - ((estimated_wait_hours - 8) / 8) * 0.15  # 0.70 - 0.55
            elif estimated_wait_hours < 24:
                base_score = 0.55 - ((estimated_wait_hours - 16) / 8) * 0.12  # 0.55 - 0.43
            else:
                base_score = max(0.35, 0.43 - ((estimated_wait_hours - 24) / 24) * 0.08)  # 0.43 - 0.35
            
            # DETERMINISTIC variance based on vessel and berth characteristics
            # Formula: variance = (vessel_hash % 100 / 1667) - 0.03 + (berth_hash % 50 / 1667)
            # This creates consistent per-vessel/berth variation without randomness
            vessel_id = vessel.get('VesselID') or vessel.get('VesselId') or 0
            vessel_hash = hash(str(vessel_id)) % 100
            berth_hash = hash(str(berth_id)) % 50
            variance = (vessel_hash / 1667) - 0.03 + (berth_hash / 1667)  # Range: ~-0.03 to ~0.06
            score = base_score + variance
            
            # Time of day factor (night arrivals may face longer processing)
            arrival_hour = eta.hour
            if 0 <= arrival_hour < 6:
                score -= 0.05  # Night penalty
            elif 6 <= arrival_hour < 8:
                score -= 0.02  # Early morning slight penalty
            
            # Weekend factor (if applicable)
            if eta.weekday() >= 5:  # Saturday or Sunday
                score -= 0.03  # Weekend processing may be slower
            
            # Terminal efficiency bonus
            terminal_name = berth.get('TerminalName', '').lower()
            if 'automated' in terminal_name or 'modern' in terminal_name:
                score += 0.05
            
            return round(min(0.98, max(0.38, score)), 2)
            
        except Exception as e:
            logger.warning(f"Error calculating waiting time score: {e}")
            return 0.68  # Reasonable fallback
    
    def _generate_fast_explanation(
        self,
        vessel: Dict[str, Any],
        berth: Dict[str, Any],
        is_feasible: bool,
        violations: List[ConstraintViolation],
        score: float
    ) -> str:
        """Generate fast rule-based explanation for berth allocation - no AI call"""
        vessel_name = vessel.get('VesselName', 'Unknown')
        berth_name = berth.get('BerthName', 'Unknown')
        terminal = berth.get('TerminalName', '')
        
        if not is_feasible:
            hard_issues = [v.description for v in violations if v.constraint_type == ConstraintType.HARD]
            if hard_issues:
                return f"Not recommended: {'; '.join(hard_issues[:2])}"
            return f"Constraints not satisfied for {vessel_name} at {berth_name}."
        
        # Build dynamic explanation based on score
        if score >= 85:
            quality = "Excellent"
            reason = "All constraints satisfied with optimal efficiency."
        elif score >= 70:
            quality = "Good"
            reason = "Compatible match with favorable utilization."
        elif score >= 55:
            quality = "Acceptable"
            reason = "Meets requirements with minor optimization tradeoffs."
        else:
            quality = "Marginal"
            reason = "Consider alternative berths for better fit."
        
        return f"{quality} allocation ({score:.0f}%): {berth_name} at {terminal}. {reason}"
    
    def _generate_allocation_explanation(
        self,
        vessel: Dict[str, Any],
        berth: Dict[str, Any],
        is_feasible: bool,
        violations: List[ConstraintViolation],
        score: float
    ) -> str:
        """Generate natural language explanation for berth allocation using AI model"""
        vessel_name = vessel.get('VesselName', 'Unknown')
        berth_name = berth.get('BerthName', 'Unknown')
        terminal_name = berth.get('TerminalName', 'Unknown')
        
        # Build context for AI explanation
        context = f"""
        Vessel: {vessel_name}
        Type: {vessel.get('VesselType', 'Unknown')}
        LOA: {vessel.get('LOA', 'N/A')}m
        Draft: {vessel.get('Draft', 'N/A')}m
        Berth: {berth_name} at {terminal_name}
        Berth Length: {berth.get('Length', 'N/A')}m
        Berth Max Draft: {berth.get('MaxDraft', 'N/A')}m
        Allocation Feasible: {is_feasible}
        Score: {score}/100
        Constraint Violations: {[v.description for v in violations] if violations else 'None'}
        """
        
        # Try to use AI model for explanation
        try:
            model = get_model()
            # Initialize model if not already loaded
            if model.client is None:
                model.initialize()
            
            if model.client is not None:
                if is_feasible:
                    prompt = f"""Generate a professional, concise recommendation for this berth allocation.
                    Explain why this berth is suitable and highlight key compatibility factors.
                    Context: {context}"""
                else:
                    prompt = f"""Generate a professional, concise explanation for why this berth allocation is NOT recommended.
                    Clearly state the constraint violations and safety concerns.
                    Context: {context}"""
                
                result = model.generate_text(
                    prompt=prompt,
                    system_prompt="You are a maritime port operations expert. Provide concise, factual berth allocation recommendations. Keep responses under 80 words. Be specific about vessel-berth compatibility.",
                    max_tokens=150,
                    temperature=0.5
                )
                if result.get("success") and result.get("text"):
                    return result.get("text")
        except Exception as e:
            logger.warning(f"AI berth explanation failed: {e}")
        
        # Fallback to rule-based explanation
        if not is_feasible:
            hard_issues = [v.description for v in violations if v.constraint_type == ConstraintType.HARD]
            return f"Berth {berth_name} is NOT suitable for {vessel_name}: {'; '.join(hard_issues[:2])}"
        
        if score >= 80:
            return f"Berth {berth_name} is highly recommended for {vessel_name}. All physical constraints satisfied with optimal utilization."
        elif score >= 60:
            soft_issues = [v.description for v in violations if v.constraint_type == ConstraintType.SOFT]
            if soft_issues:
                return f"Berth {berth_name} is suitable with minor considerations: {soft_issues[0]}"
            return f"Berth {berth_name} is a good option for {vessel_name}."
        else:
            return f"Berth {berth_name} is feasible but suboptimal. Consider alternatives if available."


# Service instances
constraint_validator = ConstraintValidator()
eta_predictor = ETAPredictor()
berth_allocator = BerthAllocator()


def get_constraint_validator() -> ConstraintValidator:
    return constraint_validator


def get_eta_predictor() -> ETAPredictor:
    return eta_predictor


def get_berth_allocator() -> BerthAllocator:
    return berth_allocator
