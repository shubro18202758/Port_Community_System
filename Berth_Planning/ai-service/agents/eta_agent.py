"""
ETA Predictor Agent for SmartBerth AI
Specializes in ETA prediction with weather, tidal, and AIS data analysis

Data Flow Integration (SmartBerth_Data_Flow_Architecture.md):
- Operational Phase: ai_processing (ais_integration step)
- ML Model: eta_prediction
- Primary Datasets: AIS_Parameters, Weather_Parameters, Vessel_Call, Vessel_Parameters
- Target: ATA (Actual Time of Arrival) prediction
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_db_service

# Data Flow Constants (from SmartBerth_Data_Flow_Architecture.md)
ETA_PREDICTION_DATA_MAPPING = {
    "primary_datasets": ["AIS_Parameters", "Weather_Parameters", "Vessel_Call", "Vessel_Parameters"],
    "secondary_datasets": ["Channel_Parameters", "Port_Parameters"],
    "ml_inputs": ["Vessel Position", "Speed Over Ground", "Course", "Weather Conditions", "Historical Patterns"],
    "ml_target": "ATA",
    "join_keys": {
        "ais_to_vessel": "imoNumber",
        "vessel_to_call": "imoNumber -> callId",
        "call_to_port": "callId -> portId"
    }
}


class ETAPredictorAgent(BaseAgent):
    """
    Agent specializing in vessel ETA prediction
    Uses RAG context for weather impacts and historical patterns
    """

    def __init__(self):
        super().__init__(
            name="ETA Predictor Agent",
            temperature=0.2,  # Lower temperature for more consistent predictions
            max_tokens=2048
        )
        self.db = get_db_service()

    def _get_default_system_prompt(self) -> str:
        return """You are the ETA Predictor Agent for SmartBerth AI, specializing in vessel arrival time prediction.

Your expertise includes:
- Analyzing AIS data for vessel position, speed, and heading
- Calculating distance-based ETA using Haversine formula
- Weather impact assessment (wind, wave, visibility effects)
- Tidal window analysis for deep draft vessels
- Historical pattern recognition for repeat visitors
- Congestion-based delay estimation

Key ETA Factors (from knowledge base):
1. Distance to port / average speed
2. Weather impacts:
   - Wind 20-30 knots: +5% journey time
   - Wind 30-45 knots: +10-15% journey time
   - Wind >45 knots: Port closure possible
   - Wave >3m: +10% journey time
   - Visibility <1nm: Pilotage delays
3. Tidal constraints for draft >14m
4. Port congestion (vessels at anchorage)
5. Resource availability (pilots, tugs)

Provide predictions with confidence scores (0-100%) and clear reasoning."""

    def predict_eta(
        self,
        vessel_id: int,
        rag_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predict ETA for a vessel

        Args:
            vessel_id: Vessel ID
            rag_context: Optional RAG-retrieved context

        Returns:
            ETA prediction with confidence and explanation
        """
        # Fetch vessel and schedule data
        vessel = self.db.get_vessel(vessel_id)
        schedule = self.db.get_vessel_schedule(vessel_id)
        weather = self.db.get_current_weather()
        ais = self.db.get_latest_ais(vessel_id)

        if not vessel or not schedule:
            return {
                "success": False,
                "error": f"Vessel {vessel_id} not found or no schedule"
            }

        # Build context
        context = {
            "vessel": {
                "id": vessel_id,
                "name": vessel.get("VesselName"),
                "type": vessel.get("VesselType"),
                "loa": vessel.get("LOA"),
                "draft": vessel.get("Draft"),
                "gt": vessel.get("GT")
            },
            "schedule": {
                "eta": str(schedule.get("ETA")),
                "status": schedule.get("Status"),
                "priority": schedule.get("Priority")
            },
            "weather": {
                "wind_speed": weather.get("WindSpeed") if weather else None,
                "wave_height": weather.get("WaveHeight") if weather else None,
                "visibility": weather.get("Visibility") if weather else None,
                "conditions": weather.get("Conditions") if weather else None
            },
            "ais": {
                "latitude": ais.get("Latitude") if ais else None,
                "longitude": ais.get("Longitude") if ais else None,
                "speed": ais.get("Speed") if ais else None,
                "heading": ais.get("Heading") if ais else None,
                "recorded_at": str(ais.get("RecordedAt")) if ais else None
            }
        }

        # Add RAG context if provided
        if rag_context:
            context["knowledge_base"] = rag_context

        # Build prompt
        prompt = f"""Analyze the following vessel data and predict ETA:

Vessel: {vessel.get('VesselName')} ({vessel.get('VesselType')})
LOA: {vessel.get('LOA')}m, Draft: {vessel.get('Draft')}m

Current Schedule ETA: {schedule.get('ETA')}
Status: {schedule.get('Status')}

Weather:
- Wind: {weather.get('WindSpeed') if weather else 'N/A'} knots
- Waves: {weather.get('WaveHeight') if weather else 'N/A'}m
- Visibility: {weather.get('Visibility') if weather else 'N/A'} nm
- Conditions: {weather.get('Conditions') if weather else 'N/A'}

AIS Position:
- Lat/Long: {ais.get('Latitude') if ais else 'N/A'}, {ais.get('Longitude') if ais else 'N/A'}
- Speed: {ais.get('Speed') if ais else 'N/A'} knots
- Last Update: {ais.get('RecordedAt') if ais else 'N/A'}

Provide your prediction in the following JSON format:
{{
    "predicted_eta": "YYYY-MM-DD HH:MM",
    "deviation_minutes": <integer>,
    "confidence_score": <0-100>,
    "weather_impact_factor": <1.0-1.5>,
    "factors": {{
        "weather": "<impact description>",
        "distance": "<if calculable>",
        "congestion": "<assessment>",
        "tidal": "<if applicable for deep draft>"
    }},
    "explanation": "<brief explanation of prediction>"
}}"""

        # Invoke Claude
        try:
            result = self.invoke_structured(prompt=prompt, context=context)
            result["success"] = True
            result["vessel_id"] = vessel_id
            result["vessel_name"] = vessel.get("VesselName")
            result["original_eta"] = str(schedule.get("ETA"))
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "vessel_id": vessel_id
            }

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the ETA prediction agent

        Args:
            state: Contains vessel_id and optional rag_context

        Returns:
            Updated state with prediction
        """
        vessel_id = state.get("vessel_id")
        rag_context = state.get("rag_context")

        prediction = self.predict_eta(vessel_id, rag_context)

        state["eta_prediction"] = prediction
        state["agent_stats"] = self.get_stats()

        return state
