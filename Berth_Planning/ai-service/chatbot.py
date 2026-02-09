"""
SmartBerth AI Service - Chatbot
Conversational interface for port operators using Janus Pro 7B
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
import json

from database import get_db_service
from model import get_model
from rag import get_rag_pipeline
from services import get_eta_predictor, get_berth_allocator, get_constraint_validator

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Classification of user query intents"""
    VESSEL_STATUS = "vessel_status"
    VESSEL_QUEUE = "vessel_queue"
    BERTH_STATUS = "berth_status"
    BERTH_AVAILABILITY = "berth_availability"
    ETA_PREDICTION = "eta_prediction"
    ALLOCATION_REASON = "allocation_reason"
    CONFLICT_INFO = "conflict_info"
    DELAY_IMPACT = "delay_impact"
    WEATHER_STATUS = "weather_status"
    GENERAL_QUERY = "general_query"
    PLOT_REQUEST = "plot_request"
    DATA_QUERY = "data_query"  # Direct database query
    SCORING_EXPLANATION = "scoring_explanation"  # AI scoring formula explanation
    FORECAST_REQUEST = "forecast_request"  # AI-powered forecasts


@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    """Structured chat response"""
    text: str
    intent: QueryIntent
    entities: Dict[str, Any]
    structured_data: Optional[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    confidence: float


class SmartBerthChatbot:
    """
    Conversational AI chatbot for SmartBerth
    Handles natural language queries about vessels, berths, and operations
    """
    
    def __init__(self):
        self.db = get_db_service()
        self.model = get_model()
        self.rag = get_rag_pipeline()
        self.predictor = get_eta_predictor()
        self.allocator = get_berth_allocator()
        
        # Conversation history (per session)
        self.conversation_history: List[ChatMessage] = []
        
        # Intent patterns
        self.intent_patterns = {
            QueryIntent.VESSEL_STATUS: [
                r"status of vessel",
                r"tell me about vessel",
                r"where is vessel",
                r"vessel .* status",
                r"what is .* doing",
            ],
            QueryIntent.VESSEL_QUEUE: [
                r"vessels arriving",
                r"vessel queue",
                r"upcoming arrivals",
                r"next .* hours",
                r"waiting vessels",
                r"anchorage",
            ],
            QueryIntent.BERTH_STATUS: [
                r"berth .* status",
                r"which vessel .* berth",
                r"who is at berth",
                r"berth .* occupied",
                r"current berth",
            ],
            QueryIntent.BERTH_AVAILABILITY: [
                r"berth .* free",
                r"available berth",
                r"when .* berth .* available",
                r"berth availability",
                r"empty berth",
            ],
            QueryIntent.ETA_PREDICTION: [
                r"eta",
                r"arrival time",
                r"when will .* arrive",
                r"predicted arrival",
                r"expected time",
            ],
            QueryIntent.ALLOCATION_REASON: [
                r"why .* berth",
                r"reason for allocation",
                r"why was .* assigned",
                r"allocation reason",
                r"explain .* decision",
            ],
            QueryIntent.CONFLICT_INFO: [
                r"conflict",
                r"overlap",
                r"scheduling issue",
                r"clash",
                r"problem with",
            ],
            QueryIntent.DELAY_IMPACT: [
                r"impact .* delay",
                r"what if .* delayed",
                r"delay .* affect",
                r"cascade",
                r"downstream effect",
            ],
            QueryIntent.WEATHER_STATUS: [
                r"weather",
                r"wind",
                r"visibility",
                r"storm",
                r"conditions",
            ],
            QueryIntent.PLOT_REQUEST: [
                r"show .* chart",
                r"visualize",
                r"plot",
                r"graph",
                r"trend",
                r"demand",
            ],
            QueryIntent.DATA_QUERY: [
                r"list all",
                r"show all",
                r"get all",
                r"fetch .* data",
                r"how many",
                r"count of",
                r"total number",
                r"database",
                r"query",
                r"records",
                r"data for",
                r"details of all",
            ],
            QueryIntent.SCORING_EXPLANATION: [
                r"how .* score",
                r"scoring formula",
                r"explain .* ai score",
                r"what .* ai score",
                r"calculation .* score",
                r"how .* calculated",
                r"score breakdown",
            ],
            QueryIntent.FORECAST_REQUEST: [
                r"forecast",
                r"predict",
                r"estimate .* demand",
                r"future .* utilization",
                r"capacity forecast",
                r"expected .* arrival",
                r"projection",
            ],
        }
    
    def classify_intent(self, query: str) -> Tuple[QueryIntent, float]:
        """Classify the intent of a user query"""
        query_lower = query.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent, 0.85
        
        return QueryIntent.GENERAL_QUERY, 0.5
    
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from the query"""
        entities = {}
        query_lower = query.lower()
        
        # Extract vessel names (look for common patterns)
        vessel_patterns = [
            r"vessel\s+([A-Z][A-Za-z0-9\s\-]+)",
            r"ship\s+([A-Z][A-Za-z0-9\s\-]+)",
            r"([A-Z]{2,}[\s\-]?[A-Z0-9]+)",  # IMO-style names
        ]
        for pattern in vessel_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                entities['vessel_name'] = match.group(1).strip()
                break
        
        # Extract berth references
        berth_match = re.search(r"berth\s*(\d+|[A-Za-z]+\s*\d*)", query_lower)
        if berth_match:
            entities['berth_reference'] = berth_match.group(1).strip()
        
        # Extract time references
        time_patterns = {
            r"next\s+(\d+)\s+hours?": 'hours_ahead',
            r"in\s+(\d+)\s+hours?": 'hours_ahead',
            r"(\d+)\s+hours?\s+late": 'delay_hours',
            r"(\d+)\s+hours?\s+delayed?": 'delay_hours',
        }
        for pattern, key in time_patterns.items():
            match = re.search(pattern, query_lower)
            if match:
                entities[key] = int(match.group(1))
        
        # Extract dates
        if "today" in query_lower:
            entities['date'] = datetime.utcnow().date().isoformat()
        elif "tomorrow" in query_lower:
            entities['date'] = (datetime.utcnow() + timedelta(days=1)).date().isoformat()
        
        return entities
    
    def _handle_vessel_status(self, entities: Dict[str, Any]) -> ChatResponse:
        """Handle vessel status queries"""
        vessel_name = entities.get('vessel_name')
        
        if not vessel_name:
            # Get all approaching vessels
            vessels = self.db.get_vessels_by_status('Approaching')
            if not vessels:
                vessels = self.db.get_vessels_by_status('Scheduled')
            
            if vessels:
                vessel_list = "\n".join([
                    f"• {v['VesselName']} - {v['Status']} - ETA: {v.get('ETA', 'N/A')}"
                    for v in vessels[:5]
                ])
                return ChatResponse(
                    text=f"Here are the vessels I'm tracking:\n\n{vessel_list}\n\nAsk about a specific vessel for more details.",
                    intent=QueryIntent.VESSEL_STATUS,
                    entities=entities,
                    structured_data={'vessels': vessels[:5]},
                    actions=[{'type': 'view_vessel', 'vessel_id': v['VesselId']} for v in vessels[:3]],
                    confidence=0.9
                )
            return ChatResponse(
                text="No vessels currently being tracked. Please check the vessel queue for upcoming arrivals.",
                intent=QueryIntent.VESSEL_STATUS,
                entities=entities,
                structured_data=None,
                actions=[],
                confidence=0.7
            )
        
        # Search for specific vessel
        vessels = self.db.get_all_vessels()
        matching = [v for v in vessels if vessel_name.lower() in v['VesselName'].lower()]
        
        if not matching:
            return ChatResponse(
                text=f"I couldn't find a vessel matching '{vessel_name}'. Please check the vessel name and try again.",
                intent=QueryIntent.VESSEL_STATUS,
                entities=entities,
                structured_data=None,
                actions=[],
                confidence=0.6
            )
        
        vessel = matching[0]
        
        # Get prediction
        prediction = self.predictor.predict_eta(vessel['VesselId'])
        
        response_text = f"""**{vessel['VesselName']}** ({vessel.get('VesselType', 'Unknown type')})

📍 **Status**: {prediction.status.upper()}
🚢 **Type**: {vessel.get('VesselType', 'N/A')} | **LOA**: {vessel.get('LOA', 'N/A')}m
📦 **Cargo**: {vessel.get('CargoType', 'N/A')}

⏱️ **ETA Information**:
- Original ETA: {prediction.original_eta or 'Not set'}
- Predicted ETA: {prediction.predicted_eta or 'N/A'}
- Deviation: {prediction.deviation_minutes} minutes
- Confidence: {prediction.confidence_score}%

💡 **AI Analysis**: {prediction.ai_explanation}"""

        return ChatResponse(
            text=response_text,
            intent=QueryIntent.VESSEL_STATUS,
            entities=entities,
            structured_data=asdict(prediction),
            actions=[
                {'type': 'view_vessel', 'vessel_id': vessel['VesselId']},
                {'type': 'view_prediction', 'vessel_id': vessel['VesselId']}
            ],
            confidence=0.95
        )
    
    def _handle_vessel_queue(self, entities: Dict[str, Any]) -> ChatResponse:
        """Handle vessel queue queries"""
        hours_ahead = entities.get('hours_ahead', 24)
        
        # Get approaching/scheduled vessels
        vessels = self.db.get_vessels_by_status('Approaching')
        scheduled = self.db.get_vessels_by_status('Scheduled')
        vessels.extend(scheduled)
        
        # Filter by time window
        cutoff = datetime.utcnow() + timedelta(hours=hours_ahead)
        filtered = []
        for v in vessels:
            eta = v.get('ETA')
            if eta and eta <= cutoff:
                filtered.append(v)
        
        if not filtered:
            return ChatResponse(
                text=f"No vessels expected in the next {hours_ahead} hours.",
                intent=QueryIntent.VESSEL_QUEUE,
                entities=entities,
                structured_data={'vessels': []},
                actions=[],
                confidence=0.8
            )
        
        # Sort by ETA
        filtered.sort(key=lambda x: x.get('ETA') or datetime.max)
        
        queue_text = f"**Vessel Queue - Next {hours_ahead} hours**\n\n"
        for i, v in enumerate(filtered[:10], 1):
            eta = v.get('ETA')
            eta_str = eta.strftime('%H:%M') if eta else 'N/A'
            queue_text += f"{i}. **{v['VesselName']}** - {v['VesselType']} - ETA: {eta_str}\n"
        
        queue_text += f"\n*{len(filtered)} vessels in queue*"
        
        return ChatResponse(
            text=queue_text,
            intent=QueryIntent.VESSEL_QUEUE,
            entities=entities,
            structured_data={'vessels': filtered[:10], 'total': len(filtered)},
            actions=[{'type': 'view_queue'}],
            confidence=0.9
        )
    
    def _handle_berth_status(self, entities: Dict[str, Any]) -> ChatResponse:
        """Handle berth status queries"""
        berth_ref = entities.get('berth_reference')
        
        berths = self.db.get_all_berths()
        schedules = self.db.get_active_schedules()
        
        if berth_ref:
            # Find specific berth
            matching = [b for b in berths if berth_ref.lower() in b['BerthName'].lower() 
                       or berth_ref in str(b.get('BerthCode', ''))]
            
            if not matching:
                return ChatResponse(
                    text=f"Berth '{berth_ref}' not found. Available berths: {', '.join(b['BerthName'] for b in berths[:5])}...",
                    intent=QueryIntent.BERTH_STATUS,
                    entities=entities,
                    structured_data=None,
                    actions=[],
                    confidence=0.6
                )
            
            berth = matching[0]
            
            # Find current occupant
            occupant = None
            for s in schedules:
                if s.get('BerthId') == berth['BerthId'] and s.get('Status') in ['Berthed']:
                    occupant = s
                    break
            
            if occupant:
                text = f"""**{berth['BerthName']}** ({berth.get('TerminalName', 'N/A')})

🚢 **Currently Occupied by**: {occupant['VesselName']}
📊 **Status**: {occupant['Status']}
⏱️ **ETD**: {occupant.get('ETD', 'Not set')}

*Berth Specs*: Max LOA {berth.get('MaxLOA', 'N/A')}m | Max Draft {berth.get('MaxDraft', 'N/A')}m"""
            else:
                text = f"""**{berth['BerthName']}** ({berth.get('TerminalName', 'N/A')})

✅ **Status**: Available

*Berth Specs*: Max LOA {berth.get('MaxLOA', 'N/A')}m | Max Draft {berth.get('MaxDraft', 'N/A')}m | Type: {berth.get('BerthType', 'N/A')}"""
            
            return ChatResponse(
                text=text,
                intent=QueryIntent.BERTH_STATUS,
                entities=entities,
                structured_data={'berth': berth, 'occupant': occupant},
                actions=[{'type': 'view_berth', 'berth_id': berth['BerthId']}],
                confidence=0.9
            )
        
        # Overview of all berths
        occupied = []
        available = []
        
        occupied_berth_ids = {s['BerthId'] for s in schedules if s.get('BerthId') and s.get('Status') in ['Berthed']}
        
        for berth in berths:
            if berth['BerthId'] in occupied_berth_ids:
                occupied.append(berth['BerthName'])
            else:
                available.append(berth['BerthName'])
        
        text = f"""**Berth Overview**

🔴 **Occupied** ({len(occupied)}): {', '.join(occupied[:5])}{'...' if len(occupied) > 5 else ''}

🟢 **Available** ({len(available)}): {', '.join(available[:5])}{'...' if len(available) > 5 else ''}

Ask about a specific berth for details."""
        
        return ChatResponse(
            text=text,
            intent=QueryIntent.BERTH_STATUS,
            entities=entities,
            structured_data={'occupied': occupied, 'available': available},
            actions=[{'type': 'view_berths'}],
            confidence=0.85
        )
    
    def _handle_weather_status(self, entities: Dict[str, Any]) -> ChatResponse:
        """Handle weather status queries"""
        weather = self.db.get_current_weather()
        
        if not weather:
            return ChatResponse(
                text="Weather data is not currently available. Please check the weather monitoring system.",
                intent=QueryIntent.WEATHER_STATUS,
                entities=entities,
                structured_data=None,
                actions=[],
                confidence=0.7
            )
        
        wind = weather.get('WindSpeed', 0)
        visibility = weather.get('Visibility', 'N/A')
        wave = weather.get('WaveHeight', 0)
        conditions = weather.get('Conditions', 'Unknown')
        
        # Operational impact assessment
        impacts = []
        if wind > 25:
            impacts.append("⚠️ High winds may affect crane operations")
        if visibility < 1:
            impacts.append("⚠️ Low visibility may delay pilot boarding")
        if wave > 1.5:
            impacts.append("⚠️ Wave height may impact berthing")
        
        impact_text = "\n".join(impacts) if impacts else "✅ Conditions suitable for normal operations"
        
        text = f"""**Current Weather Conditions**

🌤️ **Conditions**: {conditions}
💨 **Wind Speed**: {wind} knots
👁️ **Visibility**: {visibility} NM
🌊 **Wave Height**: {wave}m

**Operational Impact**:
{impact_text}"""
        
        return ChatResponse(
            text=text,
            intent=QueryIntent.WEATHER_STATUS,
            entities=entities,
            structured_data=weather,
            actions=[],
            confidence=0.9
        )
    
    def _handle_general_query(self, query: str, entities: Dict[str, Any]) -> ChatResponse:
        """Handle general queries using RAG and LLM"""
        # Use RAG for context
        result = self.rag.generate_explanation(query)
        
        if result.get('success'):
            return ChatResponse(
                text=result.get('explanation', 'I could not find relevant information.'),
                intent=QueryIntent.GENERAL_QUERY,
                entities=entities,
                structured_data={'context_sources': result.get('context_used', [])},
                actions=[],
                confidence=0.7
            )
        
        # Fallback to direct LLM
        model = get_model()
        if model.model is not None:
            response = model.generate_text(
                prompt=query,
                system_prompt="You are SmartBerth AI, an intelligent assistant for port operations. Answer questions about vessel scheduling, berth allocation, and maritime operations. Be concise and professional.",
                max_tokens=200
            )
            if response.get('success'):
                return ChatResponse(
                    text=response.get('text', ''),
                    intent=QueryIntent.GENERAL_QUERY,
                    entities=entities,
                    structured_data=None,
                    actions=[],
                    confidence=0.6
                )
        
        return ChatResponse(
            text="I'm not sure how to help with that. You can ask me about:\n• Vessel status and ETA\n• Berth availability\n• Weather conditions\n• Scheduling conflicts\n• AI scoring explanations\n• Forecasts and predictions\n• Database queries",
            intent=QueryIntent.GENERAL_QUERY,
            entities=entities,
            structured_data=None,
            actions=[],
            confidence=0.4
        )
    
    def _handle_data_query(self, query: str, entities: Dict[str, Any]) -> ChatResponse:
        """Handle direct database queries for vessels, berths, schedules, and resources"""
        query_lower = query.lower()
        
        try:
            # Determine data type requested
            if 'vessel' in query_lower:
                data = self.db.get_all_vessels()
                data_type = "vessels"
            elif 'berth' in query_lower:
                data = self.db.get_all_berths()
                data_type = "berths"
            elif 'schedule' in query_lower:
                data = self.db.get_active_schedules()
                data_type = "schedules"
            elif 'resource' in query_lower or 'equipment' in query_lower:
                data = self.db.get_available_resources()
                data_type = "resources"
            elif 'terminal' in query_lower:
                terminals = {}
                berths = self.db.get_all_berths()
                for b in berths:
                    t_name = b.get('TerminalName', 'Unknown')
                    if t_name not in terminals:
                        terminals[t_name] = {'count': 0, 'berths': []}
                    terminals[t_name]['count'] += 1
                    terminals[t_name]['berths'].append(b.get('BerthName'))
                data = [{'terminal': k, **v} for k, v in terminals.items()]
                data_type = "terminals"
            else:
                # Return summary of available data
                vessel_count = len(self.db.get_all_vessels())
                berth_count = len(self.db.get_all_berths())
                schedule_count = len(self.db.get_active_schedules())
                
                text = f"""**Database Summary**
                
📊 **Available Data:**
• **Vessels**: {vessel_count} records
• **Berths**: {berth_count} records
• **Active Schedules**: {schedule_count} records

🔍 **Query Examples:**
• "List all vessels"
• "Show all berths"
• "Get all schedules"
• "How many vessels are in the system?"
• "Show terminal information\""""
                
                return ChatResponse(
                    text=text,
                    intent=QueryIntent.DATA_QUERY,
                    entities=entities,
                    structured_data={'vessels': vessel_count, 'berths': berth_count, 'schedules': schedule_count},
                    actions=[],
                    confidence=0.9
                )
            
            # Count check
            if 'how many' in query_lower or 'count' in query_lower or 'total' in query_lower:
                text = f"There are **{len(data)} {data_type}** in the database."
                return ChatResponse(
                    text=text,
                    intent=QueryIntent.DATA_QUERY,
                    entities=entities,
                    structured_data={'count': len(data), 'type': data_type},
                    actions=[],
                    confidence=0.95
                )
            
            # Format data for display
            if data_type == "vessels":
                items = [f"• **{v.get('VesselName')}** - {v.get('VesselType', 'N/A')} - {v.get('Status', 'N/A')}" for v in data[:15]]
            elif data_type == "berths":
                items = [f"• **{b.get('BerthName')}** - {b.get('TerminalName', 'N/A')} - LOA: {b.get('MaxLOA', 'N/A')}m" for b in data[:15]]
            elif data_type == "schedules":
                items = [f"• **{s.get('VesselName', 'N/A')}** → {s.get('BerthName', 'N/A')} - {s.get('Status', 'N/A')}" for s in data[:15]]
            elif data_type == "terminals":
                items = [f"• **{t.get('terminal')}**: {t.get('count')} berths" for t in data]
            else:
                items = [f"• {str(d)[:100]}" for d in data[:15]]
            
            text = f"**{data_type.title()} Data** ({len(data)} records)\n\n" + "\n".join(items)
            if len(data) > 15:
                text += f"\n\n*...and {len(data) - 15} more*"
            
            return ChatResponse(
                text=text,
                intent=QueryIntent.DATA_QUERY,
                entities=entities,
                structured_data={'data': data, 'type': data_type, 'count': len(data)},
                actions=[{'type': f'view_{data_type}'}],
                confidence=0.9
            )
            
        except Exception as e:
            logger.error(f"Data query error: {e}")
            return ChatResponse(
                text=f"Error fetching data: {str(e)}. Please try a more specific query.",
                intent=QueryIntent.DATA_QUERY,
                entities=entities,
                structured_data=None,
                actions=[],
                confidence=0.5
            )
    
    def _handle_scoring_explanation(self, entities: Dict[str, Any]) -> ChatResponse:
        """Handle AI scoring formula explanation requests"""
        from services import get_scoring_formula_explanation
        
        formulas = get_scoring_formula_explanation()
        
        text = """**🤖 AI Scoring Formula Explanation**

The berth allocation AI score is calculated using a **weighted formula**:

```
Total Score = (Constraint × 0.4) + (Utilization × 0.2) + (Waiting × 0.3) + (Priority × 0.1)
```

**📊 Component Breakdown:**

**1. Constraint Score (40%)**
• Hard violations (physical limits) → 0%
• Soft violations → 100% - (count × 10%)
• Perfect compatibility → 100%

**2. Utilization Score (20%)**
• Optimal range: 50-70% berth usage
• Uses deterministic variance based on berth ID and timestamp
• Higher score = better capacity management

**3. Waiting Time Score (30%)**
• Based on queue position & vessel types ahead
• Adjusted for time of day and priority
• Night arrivals: -5%, Weekends: -3%

**4. Priority Score (10%)**
• Critical: 100%, High: 80%, Normal: 60%, Low: 40%

💡 *All formulas are deterministic - same inputs always produce same scores.*"""

        return ChatResponse(
            text=text,
            intent=QueryIntent.SCORING_EXPLANATION,
            entities=entities,
            structured_data=formulas,
            actions=[],
            confidence=0.95
        )
    
    def _handle_forecast_request(self, query: str, entities: Dict[str, Any]) -> ChatResponse:
        """Handle AI-powered forecast and prediction requests"""
        query_lower = query.lower()
        
        try:
            # Get current data for predictions
            vessels = self.db.get_all_vessels()
            berths = self.db.get_all_berths()
            schedules = self.db.get_active_schedules()
            
            approaching = [v for v in vessels if v.get('Status') == 'Approaching']
            scheduled = [v for v in vessels if v.get('Status') == 'Scheduled']
            
            # Calculate forecasts using deterministic formulas
            now = datetime.utcnow()
            
            # 24-hour forecast
            arrivals_24h = sum(1 for v in approaching + scheduled 
                            if v.get('ETA') and v.get('ETA') <= now + timedelta(hours=24))
            
            # Berth utilization forecast
            occupied_berths = len(set(s.get('BerthId') for s in schedules if s.get('Status') == 'Berthed'))
            utilization_pct = (occupied_berths / max(len(berths), 1)) * 100
            
            # Demand forecast formula:
            # demand_score = (approaching_count * 1.0 + scheduled_count * 0.7) / berth_count
            demand_score = ((len(approaching) * 1.0 + len(scheduled) * 0.7) / max(len(berths), 1)) * 100
            
            # Peak hour analysis
            hour = now.hour
            peak_multiplier = 1.2 if 8 <= hour <= 18 else 0.8
            adjusted_demand = demand_score * peak_multiplier
            
            text = f"""**📈 AI Forecast Report**
*Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}*

**🚢 Vessel Arrivals (Next 24 Hours)**
• Expected arrivals: **{arrivals_24h}** vessels
• Currently approaching: **{len(approaching)}**
• Scheduled: **{len(scheduled)}**

**🏗️ Berth Utilization**
• Current utilization: **{utilization_pct:.1f}%**
• Occupied berths: **{occupied_berths}/{len(berths)}**
• Available capacity: **{len(berths) - occupied_berths}** berths

**📊 Demand Forecast**
• Raw demand score: **{demand_score:.1f}**
• Peak-adjusted demand: **{adjusted_demand:.1f}**
• Time factor: **{'Peak hours (1.2x)' if peak_multiplier > 1 else 'Off-peak (0.8x)'}**

**🔮 Formula Used:**
```
Demand = (Approaching × 1.0 + Scheduled × 0.7) / Total_Berths × 100
Peak_Adjusted = Demand × Peak_Multiplier (1.2 for 08:00-18:00, else 0.8)
```

💡 *Status: {'⚠️ High demand - prepare additional resources' if adjusted_demand > 80 else '✅ Normal operations'}*"""

            return ChatResponse(
                text=text,
                intent=QueryIntent.FORECAST_REQUEST,
                entities=entities,
                structured_data={
                    'arrivals_24h': arrivals_24h,
                    'approaching': len(approaching),
                    'scheduled': len(scheduled),
                    'utilization_pct': utilization_pct,
                    'demand_score': demand_score,
                    'adjusted_demand': adjusted_demand,
                    'formulas': {
                        'demand': '(Approaching × 1.0 + Scheduled × 0.7) / Total_Berths × 100',
                        'peak_adjusted': 'Demand × Peak_Multiplier'
                    }
                },
                actions=[{'type': 'view_forecast'}],
                confidence=0.92
            )
            
        except Exception as e:
            logger.error(f"Forecast error: {e}")
            return ChatResponse(
                text=f"Unable to generate forecast: {str(e)}",
                intent=QueryIntent.FORECAST_REQUEST,
                entities=entities,
                structured_data=None,
                actions=[],
                confidence=0.5
            )
    
    def process_message(self, user_message: str) -> ChatResponse:
        """Process a user message and generate response"""
        # Add to history
        self.conversation_history.append(ChatMessage(
            role="user",
            content=user_message,
            timestamp=datetime.utcnow()
        ))
        
        # Classify intent
        intent, confidence = self.classify_intent(user_message)
        
        # Extract entities
        entities = self.extract_entities(user_message)
        
        # Route to appropriate handler
        response = None
        
        if intent == QueryIntent.VESSEL_STATUS:
            response = self._handle_vessel_status(entities)
        elif intent == QueryIntent.VESSEL_QUEUE:
            response = self._handle_vessel_queue(entities)
        elif intent in [QueryIntent.BERTH_STATUS, QueryIntent.BERTH_AVAILABILITY]:
            response = self._handle_berth_status(entities)
        elif intent == QueryIntent.WEATHER_STATUS:
            response = self._handle_weather_status(entities)
        elif intent == QueryIntent.ETA_PREDICTION:
            response = self._handle_vessel_status(entities)  # ETA is part of vessel status
        elif intent == QueryIntent.DATA_QUERY:
            response = self._handle_data_query(user_message, entities)
        elif intent == QueryIntent.SCORING_EXPLANATION:
            response = self._handle_scoring_explanation(entities)
        elif intent == QueryIntent.FORECAST_REQUEST:
            response = self._handle_forecast_request(user_message, entities)
        else:
            response = self._handle_general_query(user_message, entities)
        
        # Add to history
        self.conversation_history.append(ChatMessage(
            role="assistant",
            content=response.text,
            timestamp=datetime.utcnow(),
            metadata={'intent': intent.value, 'confidence': response.confidence}
        ))
        
        return response
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history as list of dicts"""
        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'metadata': msg.metadata
            }
            for msg in self.conversation_history
        ]


# Global chatbot instance
chatbot = SmartBerthChatbot()


def get_chatbot() -> SmartBerthChatbot:
    """Get the global chatbot instance"""
    return chatbot
