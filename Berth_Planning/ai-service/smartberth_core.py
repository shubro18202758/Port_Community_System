"""
SmartBerth AI Core - Claude Opus 4 Integration
Main orchestration layer for berth planning intelligence

This module integrates:
1. Claude Opus 4 for reasoning and natural language understanding
2. Training data for historical patterns and ML features
3. Test data for real-time vessel/berth operations
4. RAG pipeline for domain knowledge retrieval
5. Multi-agent coordination for complex planning tasks
"""

import logging
import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json

from config import get_settings
from model import get_model, SMARTBERTH_SYSTEM_PROMPT
from database import get_db_service
from rag import get_rag_pipeline

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
TEST_DATA_DIR = BASE_DIR / "Test_Data"
TRAIN_DATA_DIR = BASE_DIR / "Train_Database"
SEED_DATA_FILE = BASE_DIR / "seed-data.json"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class VesselProfile:
    """Complete vessel profile from data"""
    vessel_id: int
    vessel_name: str
    imo: str
    mmsi: str
    vessel_type: str
    loa: float
    beam: float
    draft: float
    gross_tonnage: float
    cargo_type: str
    cargo_volume: float
    cargo_unit: str
    priority: int
    flag_state: str


@dataclass
class AISPosition:
    """AIS position data"""
    vessel_id: int
    latitude: float
    longitude: float
    speed: float
    course: float
    heading: float
    navigation_status: str
    eta: Optional[datetime]
    distance_to_port: float
    phase: str
    recorded_at: datetime


@dataclass
class BerthProfile:
    """Berth configuration"""
    berth_code: str
    berth_name: str
    terminal_code: str
    terminal_name: str
    berth_type: str
    max_loa: float
    max_beam: float
    max_draft: float
    num_cranes: int
    is_active: bool


@dataclass 
class ETAPrediction:
    """ETA prediction result with confidence"""
    vessel_id: int
    vessel_name: str
    current_position: Tuple[float, float]
    distance_nm: float
    current_speed: float
    weather_factor: float
    base_eta_hours: float
    adjusted_eta_hours: float
    predicted_eta: datetime
    confidence_score: float
    factors: Dict[str, Any]
    ai_explanation: str


@dataclass
class BerthRecommendation:
    """Berth allocation recommendation"""
    vessel_id: int
    vessel_name: str
    recommended_berth: str
    terminal_name: str
    score: float
    is_feasible: bool
    hard_constraint_violations: List[str]
    soft_constraint_scores: Dict[str, float]
    estimated_waiting_time: float
    ai_reasoning: str


@dataclass
class ScheduleOptimization:
    """Schedule optimization result"""
    success: bool
    allocations: List[Dict[str, Any]]
    conflicts_resolved: int
    total_waiting_time_reduction: float
    utilization_improvement: float
    ai_summary: str


# ============================================================================
# SMARTBERTH CORE ENGINE
# ============================================================================

class SmartBerthCore:
    """
    Core AI engine for SmartBerth using Claude Opus 4.
    Integrates all data sources and provides intelligent berth planning.
    """
    
    # JNPT Port coordinates
    PORT_LAT = 18.9453
    PORT_LON = 72.9400
    
    def __init__(self):
        self.settings = get_settings()
        self.model = get_model()
        self.db = get_db_service()
        self.rag = get_rag_pipeline()
        
        # Data caches
        self._vessels_df: Optional[pd.DataFrame] = None
        self._berths_df: Optional[pd.DataFrame] = None
        self._ais_df: Optional[pd.DataFrame] = None
        self._weather_df: Optional[pd.DataFrame] = None
        self._training_data: Dict[str, pd.DataFrame] = {}
        self._seed_data: Optional[Dict] = None
        
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the SmartBerth core engine"""
        try:
            logger.info("Initializing SmartBerth Core Engine...")
            
            # Initialize Claude model
            if not self.model.initialize():
                logger.error("Failed to initialize Claude model")
                return False
            logger.info(f"✅ Claude model initialized: {self.settings.claude_model}")
            
            # Initialize RAG pipeline
            if not self.rag.initialize():
                logger.warning("RAG pipeline initialization failed - continuing without RAG")
            else:
                logger.info("✅ RAG pipeline initialized")
            
            # Load data
            self._load_test_data()
            self._load_training_data()
            self._load_seed_data()
            
            self._initialized = True
            logger.info("✅ SmartBerth Core Engine initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SmartBerth Core: {e}")
            return False
    
    # ========================================================================
    # DATA LOADING
    # ========================================================================
    
    def _load_test_data(self):
        """Load test data from CSV files"""
        try:
            if TEST_DATA_DIR.exists():
                # Load vessels
                vessels_file = TEST_DATA_DIR / "VESSELS.csv"
                if vessels_file.exists():
                    self._vessels_df = pd.read_csv(vessels_file)
                    logger.info(f"Loaded {len(self._vessels_df)} vessels from test data")
                
                # Load AIS data
                ais_file = TEST_DATA_DIR / "AIS_DATA.csv"
                if ais_file.exists():
                    self._ais_df = pd.read_csv(ais_file)
                    logger.info(f"Loaded {len(self._ais_df)} AIS records from test data")
                
                # Load berths
                berths_file = TEST_DATA_DIR / "BERTHS.csv"
                if berths_file.exists():
                    self._berths_df = pd.read_csv(berths_file)
                    logger.info(f"Loaded {len(self._berths_df)} berths from test data")
                
                # Load weather
                weather_file = TEST_DATA_DIR / "WEATHER_DATA.csv"
                if weather_file.exists():
                    self._weather_df = pd.read_csv(weather_file)
                    logger.info(f"Loaded {len(self._weather_df)} weather records")
                    
        except Exception as e:
            logger.error(f"Error loading test data: {e}")
    
    def _load_training_data(self):
        """Load training data for ML patterns"""
        try:
            if TRAIN_DATA_DIR.exists():
                training_files = {
                    'vessel_calls': 'SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv',
                    'weather': 'SmartBerth_AI_Weather_Parameters_Training_Data.csv',
                    'berth_params': 'SmartBerth_AI_Berth_Parameters_Training_Data.csv',
                    'vessel_params': 'SmartBerth_AI_Vessel_Parameters_Training_Data.csv',
                    'ukc': 'SmartBerth_AI_UKC_Training_Data.csv',
                    'ais_params': 'SmartBerth_AI_AIS_Parameters_Training_Data.csv',
                }
                
                for key, filename in training_files.items():
                    filepath = TRAIN_DATA_DIR / filename
                    if filepath.exists():
                        self._training_data[key] = pd.read_csv(filepath)
                        logger.info(f"Loaded {len(self._training_data[key])} records for {key}")
                        
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
    
    def _load_seed_data(self):
        """Load seed data from JSON"""
        try:
            if SEED_DATA_FILE.exists():
                with open(SEED_DATA_FILE, 'r') as f:
                    self._seed_data = json.load(f)
                logger.info("Loaded seed data from JSON")
        except Exception as e:
            logger.error(f"Error loading seed data: {e}")
    
    # ========================================================================
    # CORE CALCULATIONS
    # ========================================================================
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in nautical miles"""
        R = 3440.065  # Earth's radius in nautical miles
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def calculate_weather_factor(self, wind_speed: float, wave_height: float, visibility: float = 10) -> float:
        """
        Calculate weather impact factor (0.6-1.0).
        Lower factor means worse conditions = slower vessel speed.
        """
        # Wind impact
        if wind_speed > 35:
            wind_factor = 0.70
        elif wind_speed > 25:
            wind_factor = 0.85
        elif wind_speed > 15:
            wind_factor = 0.95
        else:
            wind_factor = 1.0
        
        # Wave impact
        if wave_height > 3.0:
            wave_factor = 0.70
        elif wave_height > 2.0:
            wave_factor = 0.85
        elif wave_height > 1.5:
            wave_factor = 0.92
        else:
            wave_factor = 1.0
        
        # Visibility impact
        if visibility < 0.5:
            vis_factor = 0.60  # May need to anchor
        elif visibility < 2:
            vis_factor = 0.90
        else:
            vis_factor = 1.0
        
        return min(wind_factor, wave_factor, vis_factor)
    
    def calculate_confidence_score(
        self,
        distance_nm: float,
        speed_knots: float,
        data_freshness_minutes: float,
        weather_factor: float,
        speed_variance: float = 0.1
    ) -> float:
        """
        Calculate confidence score (0-100) for ETA prediction.
        Based on data quality, distance, speed consistency, and weather.
        """
        # Base confidence
        confidence = 85.0
        
        # Data freshness impact
        if data_freshness_minutes > 60:
            confidence -= 15
        elif data_freshness_minutes > 30:
            confidence -= 5
        
        # Distance impact (more uncertainty at longer distances)
        if distance_nm > 200:
            confidence -= 10
        elif distance_nm > 100:
            confidence -= 5
        
        # Speed impact
        if speed_knots < 3:
            confidence -= 20  # Vessel may be anchored/stationary
        elif speed_knots < 8:
            confidence -= 10
        
        # Speed variance impact
        if speed_variance > 0.3:
            confidence -= 15
        elif speed_variance > 0.2:
            confidence -= 10
        
        # Weather impact
        if weather_factor < 0.8:
            confidence -= 10
        elif weather_factor < 0.9:
            confidence -= 5
        
        return max(20, min(98, confidence))
    
    # ========================================================================
    # ETA PREDICTION
    # ========================================================================
    
    def predict_eta(self, vessel_id: int) -> ETAPrediction:
        """
        Predict ETA for a vessel using AI-powered analysis.
        Combines AIS data, weather, historical patterns, and Claude reasoning.
        """
        # Get vessel data
        vessel = self._get_vessel(vessel_id)
        if vessel is None:
            raise ValueError(f"Vessel {vessel_id} not found")
        
        # Get latest AIS position
        ais = self._get_latest_ais(vessel_id)
        if ais is None:
            raise ValueError(f"No AIS data for vessel {vessel_id}")
        
        # Get current weather
        weather = self._get_current_weather()
        
        # Calculate distance to port
        distance_nm = self.haversine_distance(
            ais['Latitude'], ais['Longitude'],
            self.PORT_LAT, self.PORT_LON
        )
        
        # Calculate weather factor
        weather_factor = self.calculate_weather_factor(
            weather.get('WindSpeed', 10),
            weather.get('WaveHeight', 1.0),
            weather.get('Visibility', 10)
        )
        
        # Calculate ETA
        speed = float(ais.get('Speed', 12))
        if speed < 0.5:
            speed = 10  # Use default if vessel stationary
        
        adjusted_speed = speed * weather_factor
        base_eta_hours = distance_nm / speed
        adjusted_eta_hours = distance_nm / adjusted_speed
        
        # Add approach/pilotage time
        approach_time = 1.5  # Hours for pilot boarding and channel transit
        total_eta_hours = adjusted_eta_hours + approach_time
        
        predicted_eta = datetime.now() + timedelta(hours=total_eta_hours)
        
        # Calculate confidence
        confidence = self.calculate_confidence_score(
            distance_nm=distance_nm,
            speed_knots=speed,
            data_freshness_minutes=10,  # Assuming fresh data
            weather_factor=weather_factor
        )
        
        # Get historical patterns from training data
        historical_delay = self._get_historical_delay_pattern(vessel['VesselType'])
        
        # Build factors dict
        factors = {
            'distance_nm': round(distance_nm, 2),
            'current_speed': speed,
            'adjusted_speed': round(adjusted_speed, 2),
            'weather_factor': round(weather_factor, 2),
            'wind_speed': weather.get('WindSpeed', 'N/A'),
            'wave_height': weather.get('WaveHeight', 'N/A'),
            'historical_delay_avg': historical_delay,
            'approach_time_hours': approach_time,
        }
        
        # Generate AI explanation using Claude
        ai_explanation = self._generate_eta_explanation(vessel, factors, confidence)
        
        return ETAPrediction(
            vessel_id=vessel_id,
            vessel_name=vessel['VesselName'],
            current_position=(ais['Latitude'], ais['Longitude']),
            distance_nm=round(distance_nm, 2),
            current_speed=speed,
            weather_factor=round(weather_factor, 2),
            base_eta_hours=round(base_eta_hours, 2),
            adjusted_eta_hours=round(adjusted_eta_hours, 2),
            predicted_eta=predicted_eta,
            confidence_score=round(confidence, 1),
            factors=factors,
            ai_explanation=ai_explanation
        )
    
    def _get_historical_delay_pattern(self, vessel_type: str) -> float:
        """Get average delay pattern from training data"""
        try:
            if 'vessel_calls' in self._training_data:
                df = self._training_data['vessel_calls']
                type_data = df[df['vesselType'].str.contains(vessel_type, case=False, na=False)]
                if not type_data.empty and 'etaVarianceHours' in type_data.columns:
                    return float(type_data['etaVarianceHours'].mean())
        except Exception as e:
            logger.warning(f"Could not get historical delay: {e}")
        return 2.0  # Default 2 hours variance
    
    def _generate_eta_explanation(self, vessel: Dict, factors: Dict, confidence: float) -> str:
        """Generate AI explanation for ETA prediction"""
        prompt = f"""
Analyze this ETA prediction and provide a brief professional explanation:

Vessel: {vessel.get('VesselName')} ({vessel.get('VesselType')})
LOA: {vessel.get('LOA')}m, Draft: {vessel.get('Draft')}m

Distance to JNPT: {factors['distance_nm']} NM
Current Speed: {factors['current_speed']} knots
Adjusted Speed (weather): {factors['adjusted_speed']} knots
Weather Factor: {factors['weather_factor']} (1.0 = ideal)
Wind: {factors['wind_speed']} knots, Waves: {factors['wave_height']}m
Historical Avg Delay: {factors['historical_delay_avg']:.1f} hours

Confidence Score: {confidence}%

Provide a 2-3 sentence explanation of the ETA prediction, factors affecting it, and any recommendations.
"""
        try:
            result = self.model.generate_text(prompt, max_tokens=200)
            if result.get('success'):
                return result.get('text', '')
        except Exception as e:
            logger.warning(f"AI explanation failed: {e}")
        
        # Fallback explanation
        return f"ETA based on {factors['distance_nm']} NM at {factors['adjusted_speed']} knots adjusted for weather conditions."
    
    # ========================================================================
    # BERTH ALLOCATION
    # ========================================================================
    
    def recommend_berth(self, vessel_id: int, eta: Optional[datetime] = None) -> BerthRecommendation:
        """
        Recommend optimal berth allocation for a vessel.
        Uses constraint validation and AI scoring.
        """
        vessel = self._get_vessel(vessel_id)
        if vessel is None:
            raise ValueError(f"Vessel {vessel_id} not found")
        
        # Get all berths
        berths = self._get_all_berths()
        
        scored_berths = []
        for berth in berths:
            score, violations, soft_scores = self._score_berth(vessel, berth)
            scored_berths.append({
                'berth': berth,
                'score': score,
                'violations': violations,
                'soft_scores': soft_scores,
                'is_feasible': len(violations) == 0
            })
        
        # Sort by score descending
        scored_berths.sort(key=lambda x: (x['is_feasible'], x['score']), reverse=True)
        
        if not scored_berths:
            raise ValueError("No berths available for evaluation")
        
        best = scored_berths[0]
        
        # Generate AI reasoning
        ai_reasoning = self._generate_berth_reasoning(vessel, best['berth'], best, scored_berths[:3])
        
        return BerthRecommendation(
            vessel_id=vessel_id,
            vessel_name=vessel['VesselName'],
            recommended_berth=best['berth'].get('BerthCode', best['berth'].get('berthCode', '')),
            terminal_name=best['berth'].get('TerminalName', best['berth'].get('terminalName', '')),
            score=round(best['score'], 1),
            is_feasible=best['is_feasible'],
            hard_constraint_violations=best['violations'],
            soft_constraint_scores=best['soft_scores'],
            estimated_waiting_time=0.0,  # TODO: Calculate from schedule
            ai_reasoning=ai_reasoning
        )
    
    def _score_berth(self, vessel: Dict, berth: Dict) -> Tuple[float, List[str], Dict[str, float]]:
        """Score a berth for vessel compatibility"""
        violations = []
        soft_scores = {}
        
        # Get values (handle both DB and seed data formats)
        v_loa = float(vessel.get('LOA', vessel.get('loa', 0)))
        v_beam = float(vessel.get('Beam', vessel.get('beam', 0)))
        v_draft = float(vessel.get('Draft', vessel.get('draft', 0)))
        v_type = vessel.get('VesselType', vessel.get('vesselType', '')).lower()
        
        b_max_loa = float(berth.get('MaxLOA', berth.get('maxLOA', 500)))
        b_max_beam = float(berth.get('MaxBeam', berth.get('maxBeam', 100)))
        b_max_draft = float(berth.get('MaxDraft', berth.get('maxDraft', 20)))
        b_type = berth.get('BerthType', berth.get('berthType', '')).lower()
        
        # Hard constraints (violations)
        if v_loa > b_max_loa:
            violations.append(f"LOA {v_loa}m exceeds limit {b_max_loa}m")
        if v_beam > b_max_beam:
            violations.append(f"Beam {v_beam}m exceeds limit {b_max_beam}m")
        if v_draft > b_max_draft:
            violations.append(f"Draft {v_draft}m exceeds limit {b_max_draft}m")
        
        # Type compatibility
        type_compatible = self._check_type_compatibility(v_type, b_type)
        if not type_compatible:
            violations.append(f"Type mismatch: {v_type} vessel at {b_type} berth")
        
        # Soft constraint scores
        # Physical fit score (how well vessel fits)
        loa_margin = (b_max_loa - v_loa) / b_max_loa if b_max_loa > 0 else 0
        beam_margin = (b_max_beam - v_beam) / b_max_beam if b_max_beam > 0 else 0
        draft_margin = (b_max_draft - v_draft) / b_max_draft if b_max_draft > 0 else 0
        
        soft_scores['physical_fit'] = min(1.0, (loa_margin + beam_margin + draft_margin) / 3) * 30
        soft_scores['type_match'] = 25 if type_compatible else 0
        soft_scores['utilization'] = 20  # TODO: Calculate from occupancy
        soft_scores['crane_availability'] = 15  # TODO: Check crane count
        soft_scores['priority_bonus'] = 10  # TODO: Based on vessel priority
        
        total_score = sum(soft_scores.values())
        if violations:
            total_score = 0  # Infeasible
        
        return total_score, violations, soft_scores
    
    def _check_type_compatibility(self, vessel_type: str, berth_type: str) -> bool:
        """Check if vessel type is compatible with berth type"""
        compatibility = {
            'container': ['container'],
            'bulk': ['bulk', 'general'],
            'tanker': ['liquid', 'tanker'],
            'general': ['general', 'bulk'],
            'roro': ['roro', 'general'],
        }
        
        vessel_type = vessel_type.lower()
        berth_type = berth_type.lower()
        
        allowed = compatibility.get(vessel_type, [vessel_type])
        return any(bt in berth_type for bt in allowed)
    
    def _generate_berth_reasoning(self, vessel: Dict, berth: Dict, best: Dict, top_3: List) -> str:
        """Generate AI reasoning for berth recommendation"""
        prompt = f"""
Explain this berth recommendation for:

Vessel: {vessel.get('VesselName')} 
Type: {vessel.get('VesselType')}, LOA: {vessel.get('LOA')}m, Beam: {vessel.get('Beam')}m, Draft: {vessel.get('Draft')}m

Recommended Berth: {berth.get('BerthName', berth.get('berthName'))}
Terminal: {berth.get('TerminalName', berth.get('terminalName', 'N/A'))}
Score: {best['score']}/100
Feasible: {best['is_feasible']}
Violations: {best['violations'] if best['violations'] else 'None'}

Other options considered: {len(top_3)} berths evaluated

Provide a brief (2-3 sentence) professional justification for this recommendation.
"""
        try:
            result = self.model.generate_text(prompt, max_tokens=200)
            if result.get('success'):
                return result.get('text', '')
        except Exception as e:
            logger.warning(f"AI reasoning failed: {e}")
        
        return f"Recommended based on physical compatibility and terminal type match."
    
    # ========================================================================
    # PIPELINE OPERATIONS
    # ========================================================================
    
    def run_full_pipeline(self, vessel_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Run full SmartBerth pipeline for specified vessels or all scheduled vessels.
        
        Pipeline steps:
        1. Load and validate vessel data
        2. Get AIS positions and calculate distances
        3. Predict ETAs with confidence scores
        4. Recommend berth allocations
        5. Detect conflicts
        6. Generate optimization summary
        """
        if not self._initialized:
            raise RuntimeError("SmartBerth Core not initialized. Call initialize() first.")
        
        start_time = datetime.now()
        results = {
            'timestamp': start_time.isoformat(),
            'model': self.settings.claude_model,
            'vessels_processed': 0,
            'eta_predictions': [],
            'berth_recommendations': [],
            'conflicts': [],
            'summary': '',
            'processing_time_seconds': 0
        }
        
        # Get vessels to process
        if vessel_ids is None:
            if self._ais_df is not None:
                vessel_ids = self._ais_df['VesselId'].unique().tolist()
            else:
                vessel_ids = []
        
        logger.info(f"Running pipeline for {len(vessel_ids)} vessels...")
        
        # Process each vessel
        for vid in vessel_ids:
            try:
                # ETA Prediction
                eta_pred = self.predict_eta(vid)
                results['eta_predictions'].append(asdict(eta_pred))
                
                # Berth Recommendation
                berth_rec = self.recommend_berth(vid)
                results['berth_recommendations'].append(asdict(berth_rec))
                
                results['vessels_processed'] += 1
                
            except Exception as e:
                logger.warning(f"Error processing vessel {vid}: {e}")
        
        # Generate summary using Claude
        results['summary'] = self._generate_pipeline_summary(results)
        
        # Calculate processing time
        results['processing_time_seconds'] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Pipeline complete. Processed {results['vessels_processed']} vessels in {results['processing_time_seconds']:.2f}s")
        
        return results
    
    def _generate_pipeline_summary(self, results: Dict) -> str:
        """Generate AI summary of pipeline results"""
        eta_count = len(results['eta_predictions'])
        berth_count = len(results['berth_recommendations'])
        feasible = sum(1 for b in results['berth_recommendations'] if b.get('is_feasible', False))
        
        prompt = f"""
Summarize these SmartBerth AI pipeline results:

Vessels Processed: {results['vessels_processed']}
ETA Predictions: {eta_count}
Berth Recommendations: {berth_count}
Feasible Allocations: {feasible}/{berth_count}

Provide a brief executive summary (3-4 sentences) of the berth planning status.
"""
        try:
            result = self.model.generate_text(prompt, max_tokens=200)
            if result.get('success'):
                return result.get('text', '')
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
        
        return f"Processed {results['vessels_processed']} vessels with {feasible}/{berth_count} feasible allocations."
    
    # ========================================================================
    # DATA ACCESS HELPERS
    # ========================================================================
    
    def _get_vessel(self, vessel_id: int) -> Optional[Dict]:
        """Get vessel by ID from test data or database"""
        if self._vessels_df is not None:
            vessel = self._vessels_df[self._vessels_df['VesselId'] == vessel_id]
            if not vessel.empty:
                return vessel.iloc[0].to_dict()
        
        # Try database
        try:
            return self.db.get_vessel_by_id(vessel_id)
        except:
            pass
        
        return None
    
    def _get_latest_ais(self, vessel_id: int) -> Optional[Dict]:
        """Get latest AIS position for vessel"""
        if self._ais_df is not None:
            ais = self._ais_df[self._ais_df['VesselId'] == vessel_id]
            if not ais.empty:
                return ais.iloc[0].to_dict()
        
        # Try database
        try:
            ais_list = self.db.get_latest_ais_for_vessel(vessel_id, limit=1)
            if ais_list:
                return ais_list[0]
        except:
            pass
        
        return None
    
    def _get_current_weather(self) -> Dict:
        """Get current weather conditions"""
        if self._weather_df is not None and not self._weather_df.empty:
            return self._weather_df.iloc[-1].to_dict()
        
        # Try database
        try:
            return self.db.get_current_weather() or {}
        except:
            pass
        
        return {'WindSpeed': 10, 'WaveHeight': 1.0, 'Visibility': 10}
    
    def _get_all_berths(self) -> List[Dict]:
        """Get all berths from seed data or database"""
        if self._seed_data and 'berths' in self._seed_data:
            return self._seed_data['berths']
        
        if self._berths_df is not None:
            return self._berths_df.to_dict('records')
        
        try:
            return self.db.get_all_berths()
        except:
            pass
        
        return []
    
    # ========================================================================
    # TRAINING DATA ANALYSIS
    # ========================================================================
    
    def analyze_training_data(self) -> Dict[str, Any]:
        """Analyze training data to extract patterns for ML"""
        analysis = {
            'dataset_sizes': {},
            'vessel_call_patterns': {},
            'eta_variance_stats': {},
            'dwell_time_stats': {},
            'berth_utilization': {},
        }
        
        for key, df in self._training_data.items():
            analysis['dataset_sizes'][key] = len(df)
        
        # Analyze vessel calls
        if 'vessel_calls' in self._training_data:
            df = self._training_data['vessel_calls']
            
            # ETA variance by vessel type
            if 'vesselType' in df.columns and 'etaVarianceHours' in df.columns:
                analysis['eta_variance_stats'] = df.groupby('vesselType')['etaVarianceHours'].agg(['mean', 'std', 'count']).to_dict()
            
            # Dwell time by terminal type
            if 'terminalType' in df.columns and 'dwellTimeHours' in df.columns:
                analysis['dwell_time_stats'] = df.groupby('terminalType')['dwellTimeHours'].agg(['mean', 'std', 'count']).to_dict()
            
            # Berth utilization
            if 'berthCode' in df.columns:
                analysis['berth_utilization'] = df['berthCode'].value_counts().head(10).to_dict()
        
        return analysis
    
    def get_training_insights(self) -> str:
        """Generate AI insights from training data analysis"""
        analysis = self.analyze_training_data()
        
        prompt = f"""
Analyze these SmartBerth training data statistics and provide operational insights:

Dataset Sizes: {analysis['dataset_sizes']}
ETA Variance by Vessel Type: {analysis.get('eta_variance_stats', {})}
Dwell Time by Terminal Type: {analysis.get('dwell_time_stats', {})}
Top Utilized Berths: {analysis.get('berth_utilization', {})}

Provide 3-4 actionable insights for improving berth planning operations.
"""
        try:
            result = self.model.generate_text(prompt, max_tokens=400)
            if result.get('success'):
                return result.get('text', '')
        except Exception as e:
            logger.warning(f"Insights generation failed: {e}")
        
        return "Training data analysis complete. See analysis dict for statistics."


# Global instance
_smartberth_core: Optional[SmartBerthCore] = None


def get_smartberth_core() -> SmartBerthCore:
    """Get or create SmartBerth Core instance"""
    global _smartberth_core
    if _smartberth_core is None:
        _smartberth_core = SmartBerthCore()
    return _smartberth_core
