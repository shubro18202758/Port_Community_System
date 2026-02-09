"""
Berth Optimizer Agent for SmartBerth AI
Specializes in berth allocation optimization using constraint satisfaction

Data Flow Integration (SmartBerth_Data_Flow_Architecture.md):
- Operational Phase: ai_processing (berth_allocation step)
- ML Model: berth_allocation
- Primary Datasets: Berth_Parameters, Vessel_Parameters, Vessel_Call, Terminal_Parameters
- Target: Optimal berthCode with allocation score
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_db_service

# Data Flow Constants (from SmartBerth_Data_Flow_Architecture.md)
BERTH_ALLOCATION_DATA_MAPPING = {
    "primary_datasets": ["Berth_Parameters", "Vessel_Parameters", "Vessel_Call", "Terminal_Parameters"],
    "secondary_datasets": ["Port_Parameters", "Channel_Parameters"],
    "ml_inputs": ["Vessel Dimensions", "Vessel Type", "Cargo Type", "Berth Availability", "Terminal Capabilities"],
    "ml_target": "Optimal berthCode",
    "join_keys": {
        "vessel_to_berth": "imoNumber -> callId -> berthCode",
        "berth_to_terminal": "berthCode -> terminalId",
        "terminal_to_port": "terminalId -> portId"
    }
}


class BerthOptimizerAgent(BaseAgent):
    """
    Agent specializing in berth allocation optimization
    Uses RAG context for terminal policies and operational constraints
    """

    def __init__(self):
        super().__init__(
            name="Berth Optimizer Agent",
            temperature=0.3,
            max_tokens=4096
        )
        self.db = get_db_service()

    def _get_default_system_prompt(self) -> str:
        return """You are the Berth Optimizer Agent for SmartBerth AI, specializing in optimal berth allocation.

Your expertise includes:
- Matching vessel characteristics to berth constraints
- Multi-objective optimization (utilization, turnaround time, cargo priority)
- Window vessel policy enforcement (hazardous cargo, LNG, etc.)
- Terminal specialization and equipment matching
- Berth maintenance scheduling consideration
- Draft-to-water-depth analysis

Key Allocation Rules (from knowledge base):
1. Physical Constraints:
   - LOA ≤ Berth Length
   - Beam ≤ Berth Width
   - Draft + UKC Safety Margin (2m) ≤ Water Depth
2. Terminal Specialization:
   - Container → Container Terminal
   - Tanker → Petroleum Terminal
   - Bulk → Dry Bulk Terminal
   - LNG → LNG Terminal (window policy)
3. Window Vessel Policy:
   - Hazardous cargo vessels: Daylight only, no concurrent operations
   - LNG vessels: Exclusion zones, specialized tugs
4. Priority Handling:
   - Emergency: Immediate allocation
   - VIP/Liner: Reserved slots
   - Charter: Standard queue

Provide allocations with scores (0-100) and constraint satisfaction details."""

    def optimize_allocation(
        self,
        vessel_id: int,
        rag_context: Optional[str] = None,
        time_horizon_hours: int = 48
    ) -> Dict[str, Any]:
        """
        Find optimal berth allocation for a vessel

        Args:
            vessel_id: Vessel ID
            rag_context: Optional RAG-retrieved context
            time_horizon_hours: Planning horizon

        Returns:
            Optimal berth recommendation with alternatives
        """
        # Fetch data
        vessel = self.db.get_vessel(vessel_id)
        schedule = self.db.get_vessel_schedule(vessel_id)
        berths = self.db.get_all_berths()
        occupancy = self.db.get_berth_occupancy()

        if not vessel or not schedule:
            return {
                "success": False,
                "error": f"Vessel {vessel_id} not found or no schedule"
            }

        # Filter compatible berths
        compatible_berths = []
        for berth in berths:
            # Physical compatibility checks
            if vessel.get("LOA", 0) > berth.get("BerthLength", 0):
                continue
            if vessel.get("Draft", 0) + 2 > berth.get("WaterDepth", 0):  # 2m UKC
                continue
            compatible_berths.append(berth)

        # Build context
        context = {
            "vessel": {
                "id": vessel_id,
                "name": vessel.get("VesselName"),
                "type": vessel.get("VesselType"),
                "loa": vessel.get("LOA"),
                "beam": vessel.get("Beam"),
                "draft": vessel.get("Draft"),
                "gt": vessel.get("GT"),
                "cargo_type": schedule.get("CargoType")
            },
            "schedule": {
                "eta": str(schedule.get("ETA")),
                "etd": str(schedule.get("ETD")),
                "duration_hours": schedule.get("DurationHours"),
                "priority": schedule.get("Priority"),
                "operation": schedule.get("OperationType")
            },
            "compatible_berths": [
                {
                    "id": b.get("BerthID"),
                    "name": b.get("BerthName"),
                    "terminal": b.get("TerminalName"),
                    "length": b.get("BerthLength"),
                    "depth": b.get("WaterDepth"),
                    "equipment": b.get("Equipment"),
                    "specialization": b.get("Specialization")
                }
                for b in compatible_berths[:10]  # Limit for context
            ],
            "current_occupancy": occupancy
        }

        if rag_context:
            context["knowledge_base"] = rag_context

        # Build prompt
        prompt = f"""Optimize berth allocation for the following vessel:

Vessel: {vessel.get('VesselName')} ({vessel.get('VesselType')})
LOA: {vessel.get('LOA')}m, Beam: {vessel.get('Beam')}m, Draft: {vessel.get('Draft')}m
Cargo: {schedule.get('CargoType')}
Operation: {schedule.get('OperationType')}

Schedule:
- ETA: {schedule.get('ETA')}
- ETD: {schedule.get('ETD')}
- Priority: {schedule.get('Priority')}

Compatible Berths ({len(compatible_berths)} found):
{chr(10).join([f"- {b.get('BerthName')} at {b.get('TerminalName')}: Length={b.get('BerthLength')}m, Depth={b.get('WaterDepth')}m" for b in compatible_berths[:10]])}

Analyze and recommend the optimal berth in the following JSON format:
{{
    "primary_recommendation": {{
        "berth_id": <id>,
        "berth_name": "<name>",
        "terminal": "<terminal>",
        "allocation_score": <0-100>,
        "start_time": "YYYY-MM-DD HH:MM",
        "end_time": "YYYY-MM-DD HH:MM",
        "constraint_satisfaction": {{
            "physical": <true/false>,
            "terminal_match": <true/false>,
            "timing": <true/false>,
            "special_requirements": <true/false>
        }},
        "reasoning": "<why this berth>"
    }},
    "alternatives": [
        {{
            "berth_id": <id>,
            "berth_name": "<name>",
            "score": <0-100>,
            "tradeoffs": "<what makes it less optimal>"
        }}
    ],
    "warnings": ["<any concerns or special handling>"],
    "optimization_factors": {{
        "utilization_score": <0-100>,
        "turnaround_efficiency": <0-100>,
        "priority_handling": <0-100>
    }}
}}"""

        try:
            result = self.invoke_structured(prompt=prompt, context=context)
            result["success"] = True
            result["vessel_id"] = vessel_id
            result["vessel_name"] = vessel.get("VesselName")
            result["compatible_berth_count"] = len(compatible_berths)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "vessel_id": vessel_id
            }

    def check_constraints(
        self,
        vessel_id: int,
        berth_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Check if a specific berth allocation satisfies all constraints

        Args:
            vessel_id: Vessel ID
            berth_id: Target berth ID
            start_time: Allocation start time
            end_time: Allocation end time

        Returns:
            Constraint satisfaction report
        """
        vessel = self.db.get_vessel(vessel_id)
        berth = self.db.get_berth(berth_id)
        schedule = self.db.get_vessel_schedule(vessel_id)
        maintenance = self.db.get_berth_maintenance(berth_id, start_time, end_time)
        conflicts = self.db.check_berth_conflicts(berth_id, start_time, end_time)

        constraints = {
            "physical": {
                "loa_ok": vessel.get("LOA", 0) <= berth.get("BerthLength", 0),
                "draft_ok": vessel.get("Draft", 0) + 2 <= berth.get("WaterDepth", 0),
                "beam_ok": vessel.get("Beam", 0) <= berth.get("BerthWidth", float('inf'))
            },
            "temporal": {
                "no_conflicts": len(conflicts) == 0,
                "no_maintenance": len(maintenance) == 0,
                "within_eta": True  # Would need more logic
            },
            "operational": {
                "terminal_match": self._check_terminal_match(vessel, berth),
                "equipment_available": True  # Would need equipment check
            },
            "overall_satisfiable": True
        }

        # Calculate overall
        all_satisfied = all([
            all(constraints["physical"].values()),
            all(constraints["temporal"].values()),
            all(constraints["operational"].values())
        ])
        constraints["overall_satisfiable"] = all_satisfied

        return constraints

    def _check_terminal_match(self, vessel: Dict, berth: Dict) -> bool:
        """Check if vessel type matches terminal specialization"""
        vessel_type = vessel.get("VesselType", "").lower()
        specialization = berth.get("Specialization", "").lower()

        mappings = {
            "container": ["container", "multi-purpose"],
            "tanker": ["petroleum", "oil", "liquid bulk"],
            "bulk carrier": ["dry bulk", "bulk", "multi-purpose"],
            "lng carrier": ["lng", "gas"],
            "general cargo": ["general", "multi-purpose", "break bulk"]
        }

        for vtype, specs in mappings.items():
            if vtype in vessel_type:
                return any(s in specialization for s in specs)

        return True  # Default to compatible

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the berth optimization agent

        Args:
            state: Contains vessel_id and optional rag_context

        Returns:
            Updated state with allocation recommendation
        """
        vessel_id = state.get("vessel_id")
        rag_context = state.get("rag_context")

        allocation = self.optimize_allocation(vessel_id, rag_context)

        state["berth_allocation"] = allocation
        state["agent_stats"] = self.get_stats()

        return state
