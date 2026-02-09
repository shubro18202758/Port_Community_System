"""
SmartBerth AI Service - Feature Engineering Layer
Advanced feature extraction for ML-powered berth planning and ETA prediction

Research-backed features based on:
1. High-accuracy ETA prediction (KFUPM 2025) - Hybrid tree-based stacking
2. Multi-data fusion for vessel arrival (ITSC 2023) - TCN with AIS/Weather fusion
3. Port optimization heuristics - Constraint satisfaction and scoring

Feature Categories:
- Temporal Features (time patterns, seasonality)
- Spatial Features (distance, position, bearing)
- Vessel Features (physical, operational characteristics)
- Historical Features (past performance, delays)
- Weather Features (wind, visibility, wave impacts)
- Resource Features (pilot, tug, crane availability)
- Traffic Features (congestion, queue dynamics)
- UKC Features (Under Keel Clearance calculations)
"""

import math
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# JNPT Port coordinates (from seed data)
JNPT_PORT_LAT = 18.9388
JNPT_PORT_LON = 72.8354
PILOT_BOARDING_LAT = 18.8500
PILOT_BOARDING_LON = 72.7500

# Channel depths from seed data (meters)
CHANNEL_DEPTHS = {
    "JNPT_MAIN_APPROACH": 15.0,
    "BMCT_DEEP_WATER": 16.5,
    "INNER_HARBOUR": 13.1,
    "SHALLOW_WATER": 10.0
}

# Vessel type coefficients (block coefficient for squat calculation)
BLOCK_COEFFICIENTS = {
    "Container": 0.68,
    "Bulk": 0.82,
    "Tanker": 0.80,
    "General": 0.75,
    "RoRo": 0.65
}

# Weather impact thresholds
WEATHER_THRESHOLDS = {
    "wind_speed_critical": 35,      # knots
    "wind_speed_warning": 25,       # knots
    "visibility_min": 0.5,          # nautical miles
    "wave_height_warning": 1.5,     # meters
    "wave_height_critical": 2.5     # meters
}


# ============================================================================
# DATA CLASSES FOR FEATURE CONTAINERS
# ============================================================================

@dataclass
class TemporalFeatures:
    """Time-based features for pattern recognition"""
    hour_of_day: int
    day_of_week: int
    day_of_month: int
    month: int
    quarter: int
    is_weekend: bool
    is_night_hours: bool  # 22:00-06:00
    is_peak_hours: bool   # 08:00-18:00
    tide_phase: str       # "rising", "falling", "high", "low"
    tide_height: float
    hours_to_high_tide: float
    is_monsoon_season: bool
    season: str           # "winter", "pre_monsoon", "monsoon", "post_monsoon"
    
    # Cyclical encodings (for ML models)
    hour_sin: float = 0.0
    hour_cos: float = 0.0
    day_sin: float = 0.0
    day_cos: float = 0.0
    month_sin: float = 0.0
    month_cos: float = 0.0
    
    def __post_init__(self):
        # Compute cyclical encodings
        self.hour_sin = math.sin(2 * math.pi * self.hour_of_day / 24)
        self.hour_cos = math.cos(2 * math.pi * self.hour_of_day / 24)
        self.day_sin = math.sin(2 * math.pi * self.day_of_week / 7)
        self.day_cos = math.cos(2 * math.pi * self.day_of_week / 7)
        self.month_sin = math.sin(2 * math.pi * self.month / 12)
        self.month_cos = math.cos(2 * math.pi * self.month / 12)


@dataclass
class SpatialFeatures:
    """Location and distance-based features"""
    current_latitude: float
    current_longitude: float
    distance_to_port: float         # nautical miles
    distance_to_pilot_boarding: float
    bearing_to_port: float          # degrees
    course_deviation: float         # degrees from direct route
    speed_over_ground: float        # knots
    rate_of_turn: float             # degrees per minute
    heading: float
    
    # Derived features
    estimated_hours_to_port: float
    speed_efficiency: float         # actual vs optimal speed
    is_in_approach_zone: bool       # within 50nm of port
    is_in_pilotage_area: bool       # within 10nm of pilot boarding
    zone_category: str              # "open_sea", "approach", "pilotage", "harbour"


@dataclass
class VesselFeatures:
    """Vessel physical and operational characteristics"""
    vessel_id: int
    vessel_name: str
    vessel_type: str
    loa: float                      # meters
    beam: float                     # meters
    draft: float                    # meters
    air_draft: float                # meters (if applicable)
    dwt: float                      # deadweight tonnage
    gross_tonnage: float
    teu_capacity: Optional[int]     # for containers
    
    # Derived features
    vessel_size_category: str       # "feeder", "panamax", "post_panamax", "mega"
    displacement_ratio: float       # draft / design_draft
    block_coefficient: float
    tugs_required: int
    pilot_class_required: str
    is_deep_draft_vessel: bool      # draft > 14m
    is_mega_vessel: bool            # LOA > 350m
    
    # Cargo features
    cargo_type: str
    cargo_quantity: float
    cargo_unit: str
    is_hazardous: bool
    is_reefer_cargo: bool
    priority_level: int             # 1=high, 2=normal, 3=low


@dataclass
class HistoricalFeatures:
    """Features derived from historical vessel performance"""
    vessel_visit_count: int
    average_dwell_time: float           # minutes
    average_waiting_time: float         # minutes
    average_eta_deviation: float        # minutes
    eta_accuracy_rate: float            # percentage
    on_time_arrival_rate: float         # percentage
    terminal_familiarity_score: float   # 0-1 (based on past visits)
    
    # Route-specific history
    route_frequency: int                # visits on this route
    route_avg_speed: float              # knots
    route_delay_pattern: str            # "consistent", "variable", "improving"
    
    # Seasonal patterns
    season_avg_delay: float             # for current season
    weather_sensitivity_score: float    # how much weather affects this vessel


@dataclass  
class WeatherFeatures:
    """Weather and environmental features"""
    wind_speed: float               # knots
    wind_direction: float           # degrees
    wind_direction_text: str        # "N", "NE", etc.
    visibility: float               # nautical miles
    wave_height: float              # meters
    temperature: float              # celsius
    precipitation: float            # mm/h
    weather_condition: str          # "Clear", "Cloudy", "Rain"
    
    # Derived features
    wind_impact_factor: float       # 0-1 (1=no impact)
    wave_impact_factor: float
    visibility_impact_factor: float
    combined_weather_score: float   # 0-1
    is_weather_alert: bool
    operations_restricted: bool     # crane/pilot ops affected
    
    # Forecast features
    forecast_6h_wind: float
    forecast_6h_wave: float
    weather_trend: str              # "improving", "stable", "deteriorating"


@dataclass
class UKCFeatures:
    """Under Keel Clearance calculation features"""
    channel_depth: float
    tide_height: float
    available_depth: float          # channel + tide
    vessel_draft: float
    static_ukc: float
    
    # Dynamic UKC components
    squat: float
    wave_allowance: float
    heel_allowance: float
    dynamic_ukc: float
    net_ukc: float
    
    # Safety metrics
    ukc_percentage: float
    required_ukc_percentage: float
    safety_margin: float
    is_safe: bool
    risk_level: str                 # "Low", "Medium", "High", "Critical"
    transit_recommendation: str


@dataclass
class TrafficFeatures:
    """Port traffic and congestion features"""
    vessels_in_queue: int
    vessels_at_berth: int
    vessels_approaching: int
    average_queue_time: float       # minutes
    berth_utilization: float        # 0-1
    terminal_utilization: Dict[str, float]
    
    # Resource availability
    available_pilots: int
    available_tugs: int
    available_cranes: int
    resource_constraint_score: float  # 0-1 (1=all available)
    
    # Time window features
    optimal_arrival_window: Tuple[datetime, datetime]
    congestion_forecast_1h: float
    congestion_forecast_6h: float
    congestion_forecast_24h: float


@dataclass
class BerthMatchFeatures:
    """Features for berth-vessel compatibility scoring"""
    berth_id: int
    berth_code: str
    terminal_code: str
    
    # Physical compatibility scores
    loa_margin: float               # berth_max_loa - vessel_loa
    beam_margin: float
    draft_margin: float
    physical_fit_score: float       # 0-1
    
    # Operational compatibility
    cargo_type_match: bool
    crane_availability: int
    equipment_match_score: float
    
    # Time-based scoring
    waiting_time_estimate: float    # minutes
    dwell_time_estimate: float
    slot_efficiency_score: float
    
    # Historical performance at berth
    avg_turnaround_time: float
    avg_productivity: float
    
    # Combined scores
    total_match_score: float


# ============================================================================
# FEATURE EXTRACTION FUNCTIONS
# ============================================================================

class FeatureExtractor:
    """
    Comprehensive feature extraction engine for SmartBerth AI.
    Implements research-backed feature engineering for:
    - ETA Prediction
    - Berth Allocation Optimization
    - Resource Scheduling
    - Conflict Detection
    """
    
    def __init__(self, db_service=None):
        """Initialize with optional database service for historical lookups"""
        self.db = db_service
        
    # ========================================================================
    # TEMPORAL FEATURE EXTRACTION
    # ========================================================================
    
    def extract_temporal_features(
        self, 
        timestamp: datetime,
        tidal_data: Optional[Dict[str, Any]] = None
    ) -> TemporalFeatures:
        """
        Extract time-based features from a timestamp.
        
        Args:
            timestamp: The datetime to extract features from
            tidal_data: Optional tidal information
            
        Returns:
            TemporalFeatures dataclass
        """
        hour = timestamp.hour
        dow = timestamp.weekday()
        month = timestamp.month
        
        # Determine season (Mumbai/JNPT)
        if month in [11, 12, 1, 2]:
            season = "winter"
            is_monsoon = False
        elif month in [3, 4, 5]:
            season = "pre_monsoon"
            is_monsoon = False
        elif month in [6, 7, 8, 9]:
            season = "monsoon"
            is_monsoon = True
        else:
            season = "post_monsoon"
            is_monsoon = False
        
        # Tidal features
        tide_height = 0.0
        tide_phase = "unknown"
        hours_to_high = 6.0  # default
        
        if tidal_data:
            tide_height = tidal_data.get('height', 0.0)
            tide_type = tidal_data.get('tide_type', '')
            if 'high' in tide_type.lower():
                tide_phase = "high"
                hours_to_high = 0.0
            elif 'low' in tide_type.lower():
                tide_phase = "low"
                hours_to_high = 6.0  # approximate
            # Could calculate rising/falling based on consecutive readings
        
        return TemporalFeatures(
            hour_of_day=hour,
            day_of_week=dow,
            day_of_month=timestamp.day,
            month=month,
            quarter=(month - 1) // 3 + 1,
            is_weekend=dow >= 5,
            is_night_hours=hour < 6 or hour >= 22,
            is_peak_hours=8 <= hour <= 18,
            tide_phase=tide_phase,
            tide_height=tide_height,
            hours_to_high_tide=hours_to_high,
            is_monsoon_season=is_monsoon,
            season=season
        )
    
    # ========================================================================
    # SPATIAL FEATURE EXTRACTION
    # ========================================================================
    
    def extract_spatial_features(
        self,
        latitude: float,
        longitude: float,
        speed: float,
        heading: float,
        rate_of_turn: float = 0.0
    ) -> SpatialFeatures:
        """
        Extract location and movement features.
        
        Uses Haversine formula for accurate distance calculation
        and great circle bearing for direction.
        """
        # Distance to port
        dist_to_port = self._haversine_distance(
            latitude, longitude, JNPT_PORT_LAT, JNPT_PORT_LON
        )
        
        # Distance to pilot boarding
        dist_to_pilot = self._haversine_distance(
            latitude, longitude, PILOT_BOARDING_LAT, PILOT_BOARDING_LON
        )
        
        # Bearing to port
        bearing = self._calculate_bearing(
            latitude, longitude, JNPT_PORT_LAT, JNPT_PORT_LON
        )
        
        # Course deviation
        course_deviation = abs(self._normalize_angle(heading - bearing))
        
        # Estimated time to port
        if speed > 0.5:
            hours_to_port = dist_to_port / speed
        else:
            hours_to_port = float('inf')
        
        # Speed efficiency (compared to typical 12-14 knot approach)
        optimal_speed = 12.0
        speed_efficiency = min(speed / optimal_speed, 1.0) if speed > 0 else 0.0
        
        # Zone categorization
        if dist_to_port > 50:
            zone = "open_sea"
        elif dist_to_port > 10:
            zone = "approach"
        elif dist_to_pilot > 2:
            zone = "pilotage"
        else:
            zone = "harbour"
        
        return SpatialFeatures(
            current_latitude=latitude,
            current_longitude=longitude,
            distance_to_port=round(dist_to_port, 2),
            distance_to_pilot_boarding=round(dist_to_pilot, 2),
            bearing_to_port=round(bearing, 1),
            course_deviation=round(course_deviation, 1),
            speed_over_ground=speed,
            rate_of_turn=rate_of_turn,
            heading=heading,
            estimated_hours_to_port=round(hours_to_port, 2),
            speed_efficiency=round(speed_efficiency, 2),
            is_in_approach_zone=dist_to_port <= 50,
            is_in_pilotage_area=dist_to_pilot <= 10,
            zone_category=zone
        )
    
    # ========================================================================
    # VESSEL FEATURE EXTRACTION
    # ========================================================================
    
    def extract_vessel_features(
        self,
        vessel_data: Dict[str, Any],
        cargo_data: Optional[Dict[str, Any]] = None
    ) -> VesselFeatures:
        """
        Extract vessel physical and operational characteristics.
        """
        loa = vessel_data.get('LOA', 0) or vessel_data.get('loa', 0)
        beam = vessel_data.get('Beam', 0) or vessel_data.get('beam', 0)
        draft = vessel_data.get('Draft', 0) or vessel_data.get('draft', 0)
        gt = vessel_data.get('GrossTonnage', 0) or vessel_data.get('grossTonnage', 0)
        dwt = vessel_data.get('DWT', 0) or vessel_data.get('dwt', 0)
        vessel_type = vessel_data.get('VesselType', 'Container') or vessel_data.get('vesselType', 'Container')
        
        # Size categorization
        if loa <= 200:
            size_category = "feeder"
        elif loa <= 300:
            size_category = "panamax"
        elif loa <= 366:
            size_category = "post_panamax"
        else:
            size_category = "mega"
        
        # Block coefficient
        block_coef = BLOCK_COEFFICIENTS.get(vessel_type, 0.70)
        
        # Tug requirements based on GT
        if gt < 20000:
            tugs_required = 1
        elif gt < 50000:
            tugs_required = 2
        else:
            tugs_required = 3
        
        # Pilot class requirement
        if gt > 100000:
            pilot_class = "Master"
        elif gt > 50000:
            pilot_class = "Class I"
        elif gt > 25000:
            pilot_class = "Class II"
        else:
            pilot_class = "Class III"
        
        # Cargo features
        cargo_type = cargo_data.get('cargoType', 'General') if cargo_data else 'General'
        cargo_qty = cargo_data.get('cargoQuantity', 0) if cargo_data else 0
        cargo_unit = cargo_data.get('cargoUnit', 'MT') if cargo_data else 'MT'
        
        return VesselFeatures(
            vessel_id=vessel_data.get('VesselId', vessel_data.get('vesselId', 0)),
            vessel_name=vessel_data.get('VesselName', vessel_data.get('vesselName', 'Unknown')),
            vessel_type=vessel_type,
            loa=loa,
            beam=beam,
            draft=draft,
            air_draft=vessel_data.get('AirDraft', 0) or 0,
            dwt=dwt,
            gross_tonnage=gt,
            teu_capacity=vessel_data.get('TEUCapacity', None),
            vessel_size_category=size_category,
            displacement_ratio=draft / 14.5 if draft > 0 else 0,  # normalized
            block_coefficient=block_coef,
            tugs_required=tugs_required,
            pilot_class_required=pilot_class,
            is_deep_draft_vessel=draft > 14.0,
            is_mega_vessel=loa > 350,
            cargo_type=cargo_type,
            cargo_quantity=cargo_qty,
            cargo_unit=cargo_unit,
            is_hazardous='hazard' in cargo_type.lower() or 'chemical' in cargo_type.lower(),
            is_reefer_cargo='reefer' in cargo_type.lower() or 'frozen' in cargo_type.lower(),
            priority_level=vessel_data.get('Priority', 2)
        )
    
    # ========================================================================
    # WEATHER FEATURE EXTRACTION
    # ========================================================================
    
    def extract_weather_features(
        self,
        weather_data: Dict[str, Any],
        forecast_data: Optional[List[Dict[str, Any]]] = None
    ) -> WeatherFeatures:
        """
        Extract weather and environmental impact features.
        """
        wind_speed = weather_data.get('WindSpeed', 0) or weather_data.get('windSpeed', 0)
        wind_dir = weather_data.get('WindDirection', 0) or weather_data.get('windDirection', 0)
        visibility = weather_data.get('Visibility', 10) or weather_data.get('visibility', 10)
        wave_height = weather_data.get('WaveHeight', 0) or weather_data.get('waveHeight', 0)
        
        # Calculate impact factors (1.0 = no impact, 0.0 = severe impact)
        wind_impact = max(0.5, 1.0 - (wind_speed / WEATHER_THRESHOLDS["wind_speed_critical"]))
        wave_impact = max(0.5, 1.0 - (wave_height / WEATHER_THRESHOLDS["wave_height_critical"]))
        vis_impact = min(1.0, visibility / 2.0)  # Full impact below 2nm
        
        combined_score = (wind_impact * 0.4 + wave_impact * 0.3 + vis_impact * 0.3)
        
        # Determine if operations are restricted
        ops_restricted = (
            wind_speed > WEATHER_THRESHOLDS["wind_speed_warning"] or
            visibility < WEATHER_THRESHOLDS["visibility_min"] or
            wave_height > WEATHER_THRESHOLDS["wave_height_warning"]
        )
        
        # Alert status
        is_alert = (
            wind_speed > WEATHER_THRESHOLDS["wind_speed_critical"] or
            wave_height > WEATHER_THRESHOLDS["wave_height_critical"]
        )
        
        # Forecast features
        forecast_6h_wind = wind_speed
        forecast_6h_wave = wave_height
        weather_trend = "stable"
        
        if forecast_data and len(forecast_data) > 0:
            future = forecast_data[0]
            forecast_6h_wind = future.get('windSpeed', wind_speed)
            forecast_6h_wave = future.get('waveHeight', wave_height)
            
            if forecast_6h_wind < wind_speed - 5:
                weather_trend = "improving"
            elif forecast_6h_wind > wind_speed + 5:
                weather_trend = "deteriorating"
        
        return WeatherFeatures(
            wind_speed=wind_speed,
            wind_direction=wind_dir,
            wind_direction_text=self._direction_to_text(wind_dir),
            visibility=visibility,
            wave_height=wave_height,
            temperature=weather_data.get('Temperature', 25) or 25,
            precipitation=weather_data.get('Precipitation', 0) or 0,
            weather_condition=weather_data.get('WeatherCondition', 'Clear') or 'Clear',
            wind_impact_factor=round(wind_impact, 2),
            wave_impact_factor=round(wave_impact, 2),
            visibility_impact_factor=round(vis_impact, 2),
            combined_weather_score=round(combined_score, 2),
            is_weather_alert=is_alert,
            operations_restricted=ops_restricted,
            forecast_6h_wind=forecast_6h_wind,
            forecast_6h_wave=forecast_6h_wave,
            weather_trend=weather_trend
        )
    
    # ========================================================================
    # UKC FEATURE EXTRACTION
    # ========================================================================
    
    def calculate_ukc_features(
        self,
        vessel_draft: float,
        vessel_beam: float,
        vessel_speed: float,
        channel_depth: float,
        tide_height: float,
        vessel_type: str = "Container",
        wave_height: float = 0.5
    ) -> UKCFeatures:
        """
        Calculate Under Keel Clearance features using maritime engineering formulas.
        
        Based on PIANC guidelines and port authority requirements.
        UKC = Available Depth - Draft - Squat - Wave Allowance - Heel Allowance
        """
        # Available depth
        available_depth = channel_depth + tide_height
        
        # Static UKC
        static_ukc = available_depth - vessel_draft
        
        # Squat calculation (Barrass formula)
        # Squat = Cb * (V^2 / 100) where V is speed in knots
        block_coef = BLOCK_COEFFICIENTS.get(vessel_type, 0.70)
        squat = block_coef * (vessel_speed ** 2) / 100
        
        # Wave allowance (typically 0.5 * significant wave height)
        wave_allowance = 0.5 * wave_height
        
        # Heel allowance (beam-based, typically 0.1-0.2m for containers)
        heel_allowance = min(0.2, vessel_beam * 0.003)
        
        # Dynamic UKC
        dynamic_ukc = static_ukc - squat
        
        # Net UKC (after all deductions)
        net_ukc = dynamic_ukc - wave_allowance - heel_allowance
        
        # UKC percentage
        ukc_percentage = (net_ukc / vessel_draft) * 100 if vessel_draft > 0 else 0
        
        # Required UKC (10% for containers, 15% for tankers)
        if vessel_type == "Tanker":
            required_percentage = 15.0
        else:
            required_percentage = 10.0
        
        # Safety assessment
        safety_margin = net_ukc - (vessel_draft * required_percentage / 100)
        is_safe = ukc_percentage >= required_percentage
        
        # Risk level
        if ukc_percentage < 5:
            risk_level = "Critical"
        elif ukc_percentage < required_percentage:
            risk_level = "High"
        elif ukc_percentage < required_percentage * 1.5:
            risk_level = "Medium"
        else:
            risk_level = "Low"
        
        # Generate recommendation
        if is_safe and risk_level == "Low":
            recommendation = "Safe to transit. Adequate UKC margin."
        elif is_safe:
            recommendation = f"Safe but monitor conditions. UKC at {ukc_percentage:.1f}%."
        elif risk_level == "High":
            recommendation = f"WARNING: Insufficient UKC ({ukc_percentage:.1f}%). Wait for higher tide."
        else:
            recommendation = f"UNSAFE: Critical UKC ({ukc_percentage:.1f}%). Transit prohibited."
        
        return UKCFeatures(
            channel_depth=channel_depth,
            tide_height=tide_height,
            available_depth=round(available_depth, 2),
            vessel_draft=vessel_draft,
            static_ukc=round(static_ukc, 2),
            squat=round(squat, 2),
            wave_allowance=round(wave_allowance, 2),
            heel_allowance=round(heel_allowance, 2),
            dynamic_ukc=round(dynamic_ukc, 2),
            net_ukc=round(net_ukc, 2),
            ukc_percentage=round(ukc_percentage, 1),
            required_ukc_percentage=required_percentage,
            safety_margin=round(safety_margin, 2),
            is_safe=is_safe,
            risk_level=risk_level,
            transit_recommendation=recommendation
        )
    
    # ========================================================================
    # HISTORICAL FEATURE EXTRACTION
    # ========================================================================
    
    def extract_historical_features(
        self,
        vessel_id: int,
        vessel_history: List[Dict[str, Any]]
    ) -> HistoricalFeatures:
        """
        Extract features from vessel's historical performance.
        """
        if not vessel_history:
            return HistoricalFeatures(
                vessel_visit_count=0,
                average_dwell_time=720.0,  # default 12 hours
                average_waiting_time=60.0,
                average_eta_deviation=30.0,
                eta_accuracy_rate=85.0,
                on_time_arrival_rate=80.0,
                terminal_familiarity_score=0.0,
                route_frequency=0,
                route_avg_speed=12.0,
                route_delay_pattern="unknown",
                season_avg_delay=30.0,
                weather_sensitivity_score=0.5
            )
        
        # Calculate averages
        dwell_times = [h.get('actualDwellTime', 720) for h in vessel_history]
        waiting_times = [h.get('actualWaitingTime', 60) for h in vessel_history]
        eta_accuracies = [h.get('etaAccuracy', 85) for h in vessel_history]
        
        avg_dwell = sum(dwell_times) / len(dwell_times)
        avg_waiting = sum(waiting_times) / len(waiting_times)
        avg_eta_accuracy = sum(eta_accuracies) / len(eta_accuracies)
        
        # On-time rate (ETA accuracy > 90%)
        on_time_count = sum(1 for a in eta_accuracies if a >= 90)
        on_time_rate = (on_time_count / len(eta_accuracies)) * 100
        
        # Terminal familiarity (more visits = higher score, max 1.0)
        visit_count = len(vessel_history)
        familiarity = min(1.0, visit_count / 10)
        
        # Delay pattern analysis
        if visit_count >= 3:
            recent_accuracies = eta_accuracies[-3:]
            if all(a >= 90 for a in recent_accuracies):
                delay_pattern = "consistent"
            elif recent_accuracies[-1] > recent_accuracies[0]:
                delay_pattern = "improving"
            else:
                delay_pattern = "variable"
        else:
            delay_pattern = "unknown"
        
        return HistoricalFeatures(
            vessel_visit_count=visit_count,
            average_dwell_time=round(avg_dwell, 1),
            average_waiting_time=round(avg_waiting, 1),
            average_eta_deviation=round(100 - avg_eta_accuracy, 1),
            eta_accuracy_rate=round(avg_eta_accuracy, 1),
            on_time_arrival_rate=round(on_time_rate, 1),
            terminal_familiarity_score=round(familiarity, 2),
            route_frequency=visit_count,
            route_avg_speed=12.0,  # Would need AIS history
            route_delay_pattern=delay_pattern,
            season_avg_delay=30.0,  # Would need seasonal analysis
            weather_sensitivity_score=0.5  # Would need correlation analysis
        )
    
    # ========================================================================
    # BERTH MATCH FEATURE EXTRACTION
    # ========================================================================
    
    def calculate_berth_match_features(
        self,
        vessel_features: VesselFeatures,
        berth_data: Dict[str, Any],
        schedule_data: Optional[Dict[str, Any]] = None
    ) -> BerthMatchFeatures:
        """
        Calculate compatibility features between a vessel and berth.
        """
        berth_max_loa = berth_data.get('MaxLOA', 300) or berth_data.get('maxLoa', 300)
        berth_max_beam = berth_data.get('MaxBeam', 50) or berth_data.get('maxBeam', 50)
        berth_max_draft = berth_data.get('MaxDraft', 14) or berth_data.get('maxDraft', 14)
        berth_type = berth_data.get('BerthType', 'Container') or berth_data.get('terminalType', 'Container')
        
        # Physical margins
        loa_margin = berth_max_loa - vessel_features.loa
        beam_margin = berth_max_beam - vessel_features.beam
        draft_margin = berth_max_draft - vessel_features.draft
        
        # Physical fit score (all margins must be positive)
        if loa_margin < 0 or beam_margin < 0 or draft_margin < 0:
            physical_fit = 0.0
        else:
            # Score based on how much margin is available
            loa_score = min(1.0, loa_margin / 50)  # Ideal: 50m+ margin
            beam_score = min(1.0, beam_margin / 10)
            draft_score = min(1.0, draft_margin / 3)
            physical_fit = (loa_score * 0.4 + beam_score * 0.3 + draft_score * 0.3)
        
        # Cargo type match
        vessel_cargo_type = vessel_features.cargo_type.lower()
        berth_type_lower = berth_type.lower()
        cargo_match = (
            vessel_cargo_type in berth_type_lower or
            berth_type_lower in ['general', 'multipurpose'] or
            (vessel_features.vessel_type.lower() in berth_type_lower)
        )
        
        # Crane availability (from berth data)
        crane_count = berth_data.get('CraneCount', 2) or berth_data.get('numberOfCranes', 2)
        equipment_score = min(1.0, crane_count / 4)  # Ideal: 4+ cranes
        
        # Time estimates (defaults, would use ML model)
        waiting_estimate = 60.0 if physical_fit > 0.8 else 120.0
        dwell_estimate = vessel_features.cargo_quantity / 100 if vessel_features.cargo_quantity > 0 else 720
        
        # Total score calculation
        weights = {
            'physical': 0.4,
            'cargo': 0.25,
            'equipment': 0.2,
            'time': 0.15
        }
        
        total_score = (
            weights['physical'] * physical_fit +
            weights['cargo'] * (1.0 if cargo_match else 0.0) +
            weights['equipment'] * equipment_score +
            weights['time'] * (1.0 - min(1.0, waiting_estimate / 180))
        )
        
        return BerthMatchFeatures(
            berth_id=berth_data.get('BerthId', berth_data.get('berthId', 0)),
            berth_code=berth_data.get('BerthCode', berth_data.get('berthCode', '')),
            terminal_code=berth_data.get('TerminalCode', berth_data.get('terminalCode', '')),
            loa_margin=round(loa_margin, 1),
            beam_margin=round(beam_margin, 1),
            draft_margin=round(draft_margin, 1),
            physical_fit_score=round(physical_fit, 2),
            cargo_type_match=cargo_match,
            crane_availability=crane_count,
            equipment_match_score=round(equipment_score, 2),
            waiting_time_estimate=round(waiting_estimate, 1),
            dwell_time_estimate=round(dwell_estimate, 1),
            slot_efficiency_score=round(physical_fit * 0.7 + equipment_score * 0.3, 2),
            avg_turnaround_time=720.0,  # Would need historical data
            avg_productivity=100.0,
            total_match_score=round(total_score, 2)
        )
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
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
    
    def _calculate_bearing(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """Calculate initial bearing from point 1 to point 2 in degrees"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360
    
    def _normalize_angle(self, angle: float) -> float:
        """Normalize angle to -180 to 180 degrees"""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle
    
    def _direction_to_text(self, degrees: float) -> str:
        """Convert degrees to cardinal direction"""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    # ========================================================================
    # FEATURE VECTOR GENERATION (FOR ML MODELS)
    # ========================================================================
    
    def generate_eta_feature_vector(
        self,
        temporal: TemporalFeatures,
        spatial: SpatialFeatures,
        vessel: VesselFeatures,
        weather: WeatherFeatures,
        historical: Optional[HistoricalFeatures] = None
    ) -> np.ndarray:
        """
        Generate a numerical feature vector for ETA prediction models.
        
        Based on research: Speed, distance, course, vessel type are key features.
        """
        features = [
            # Temporal (cyclical encodings)
            temporal.hour_sin,
            temporal.hour_cos,
            temporal.day_sin,
            temporal.day_cos,
            temporal.month_sin,
            temporal.month_cos,
            float(temporal.is_weekend),
            float(temporal.is_peak_hours),
            float(temporal.is_monsoon_season),
            temporal.tide_height,
            
            # Spatial (key features per research)
            spatial.distance_to_port,
            spatial.distance_to_pilot_boarding,
            spatial.speed_over_ground,
            spatial.bearing_to_port,
            spatial.course_deviation,
            spatial.estimated_hours_to_port,
            spatial.speed_efficiency,
            
            # Vessel
            vessel.loa / 400,  # Normalized
            vessel.beam / 60,
            vessel.draft / 20,
            vessel.gross_tonnage / 250000,
            float(vessel.is_mega_vessel),
            float(vessel.is_deep_draft_vessel),
            float(vessel.tugs_required) / 3,
            
            # Weather (impact factors)
            weather.wind_impact_factor,
            weather.wave_impact_factor,
            weather.visibility_impact_factor,
            weather.combined_weather_score,
        ]
        
        # Historical (if available)
        if historical:
            features.extend([
                historical.eta_accuracy_rate / 100,
                historical.on_time_arrival_rate / 100,
                historical.terminal_familiarity_score,
                historical.average_waiting_time / 180,  # Normalized
            ])
        else:
            features.extend([0.85, 0.80, 0.0, 0.5])  # Defaults
        
        return np.array(features, dtype=np.float32)
    
    def generate_berth_allocation_features(
        self,
        vessel: VesselFeatures,
        berth_matches: List[BerthMatchFeatures],
        traffic: Optional[TrafficFeatures] = None
    ) -> Dict[str, np.ndarray]:
        """
        Generate feature matrices for berth allocation optimization.
        
        Returns dict with feature arrays for each candidate berth.
        """
        result = {}
        
        for match in berth_matches:
            features = np.array([
                match.physical_fit_score,
                float(match.cargo_type_match),
                match.equipment_match_score,
                match.loa_margin / 50,
                match.draft_margin / 5,
                match.waiting_time_estimate / 180,
                match.total_match_score,
            ], dtype=np.float32)
            
            result[match.berth_code] = features
        
        return result


# ============================================================================
# SINGLETON ACCESSOR
# ============================================================================

_feature_extractor: Optional[FeatureExtractor] = None

def get_feature_extractor(db_service=None) -> FeatureExtractor:
    """Get or create the feature extractor singleton"""
    global _feature_extractor
    if _feature_extractor is None:
        _feature_extractor = FeatureExtractor(db_service)
    return _feature_extractor
