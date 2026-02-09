"""
Conflict Resolver Agent for SmartBerth AI
Specializes in detecting and resolving berth scheduling conflicts
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from .base_agent import BaseAgent

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database import get_db_service


class ConflictResolverAgent(BaseAgent):
    """
    Agent specializing in conflict detection and resolution
    Uses RAG context for conflict resolution strategies
    """

    def __init__(self):
        super().__init__(
            name="Conflict Resolver Agent",
            temperature=0.4,  # Slightly higher for creative solutions
            max_tokens=4096
        )
        self.db = get_db_service()

    def _get_default_system_prompt(self) -> str:
        return """You are the Conflict Resolver Agent for SmartBerth AI, specializing in scheduling conflict detection and resolution.

Your expertise includes:
- Detecting temporal overlaps in berth allocations
- Identifying resource conflicts (pilots, tugs, equipment)
- Resolving priority-based scheduling conflicts
- Proposing alternative allocations
- Cascading impact analysis
- Window vessel policy conflicts

Conflict Types:
1. Temporal Overlap: Two vessels at same berth with overlapping times
2. Resource Bottleneck: Insufficient pilots/tugs for concurrent operations
3. Terminal Capacity: Too many vessels for available equipment
4. Window Policy Violation: Hazardous operations during restricted hours
5. Priority Conflict: Lower priority blocking higher priority vessel

Resolution Strategies:
1. Time Shift: Move one vessel earlier/later
2. Berth Swap: Move to alternative compatible berth
3. Priority Override: Bump lower priority vessel
4. Resource Reallocation: Adjust pilot/tug assignments
5. Operation Split: Partial operations at different berths

Always calculate impact scores and propose the least disruptive solution."""

    def detect_conflicts(
        self,
        time_start: datetime,
        time_end: datetime,
        rag_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect all conflicts within a time window

        Args:
            time_start: Start of analysis window
            time_end: End of analysis window
            rag_context: Optional RAG-retrieved context

        Returns:
            Detected conflicts with severity scores
        """
        # Get scheduled vessels in window
        schedules = self.db.get_schedules_in_window(time_start, time_end)
        allocations = self.db.get_allocations_in_window(time_start, time_end)
        resources = self.db.get_resource_availability(time_start, time_end)

        conflicts = {
            "temporal": [],
            "resource": [],
            "policy": [],
            "priority": []
        }

        # Check temporal conflicts
        for i, alloc1 in enumerate(allocations):
            for alloc2 in allocations[i+1:]:
                if alloc1.get("BerthID") == alloc2.get("BerthID"):
                    # Check time overlap
                    start1 = alloc1.get("StartTime")
                    end1 = alloc1.get("EndTime")
                    start2 = alloc2.get("StartTime")
                    end2 = alloc2.get("EndTime")

                    if start1 < end2 and start2 < end1:
                        conflicts["temporal"].append({
                            "type": "temporal_overlap",
                            "berth_id": alloc1.get("BerthID"),
                            "vessel_1": {
                                "id": alloc1.get("VesselID"),
                                "name": alloc1.get("VesselName"),
                                "start": str(start1),
                                "end": str(end1)
                            },
                            "vessel_2": {
                                "id": alloc2.get("VesselID"),
                                "name": alloc2.get("VesselName"),
                                "start": str(start2),
                                "end": str(end2)
                            },
                            "overlap_minutes": self._calculate_overlap(
                                start1, end1, start2, end2
                            ),
                            "severity": "HIGH"
                        })

        return {
            "success": True,
            "time_window": {
                "start": str(time_start),
                "end": str(time_end)
            },
            "conflicts": conflicts,
            "total_conflicts": sum(len(v) for v in conflicts.values()),
            "vessels_analyzed": len(schedules),
            "allocations_analyzed": len(allocations)
        }

    def _calculate_overlap(
        self,
        start1: datetime,
        end1: datetime,
        start2: datetime,
        end2: datetime
    ) -> int:
        """Calculate overlap duration in minutes"""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        if overlap_start < overlap_end:
            return int((overlap_end - overlap_start).total_seconds() / 60)
        return 0

    def resolve_conflict(
        self,
        conflict: Dict[str, Any],
        rag_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Propose resolution for a specific conflict

        Args:
            conflict: Conflict details
            rag_context: Optional RAG-retrieved context

        Returns:
            Resolution options with impact analysis
        """
        # Get additional context
        vessel1_id = conflict.get("vessel_1", {}).get("id")
        vessel2_id = conflict.get("vessel_2", {}).get("id")

        vessel1 = self.db.get_vessel(vessel1_id) if vessel1_id else {}
        vessel2 = self.db.get_vessel(vessel2_id) if vessel2_id else {}
        schedule1 = self.db.get_vessel_schedule(vessel1_id) if vessel1_id else {}
        schedule2 = self.db.get_vessel_schedule(vessel2_id) if vessel2_id else {}

        # Find alternative berths
        berth_id = conflict.get("berth_id")
        alt_berths = self.db.get_alternative_berths(berth_id)

        # Build context
        context = {
            "conflict": conflict,
            "vessel_1": {
                "details": vessel1,
                "schedule": schedule1
            },
            "vessel_2": {
                "details": vessel2,
                "schedule": schedule2
            },
            "alternative_berths": alt_berths[:5] if alt_berths else []
        }

        if rag_context:
            context["knowledge_base"] = rag_context

        # Build prompt
        prompt = f"""Analyze this scheduling conflict and propose resolution options:

CONFLICT TYPE: {conflict.get('type')}
SEVERITY: {conflict.get('severity')}

Vessel 1: {vessel1.get('VesselName', 'Unknown')}
- Type: {vessel1.get('VesselType')}
- LOA: {vessel1.get('LOA')}m, Draft: {vessel1.get('Draft')}m
- Priority: {schedule1.get('Priority')}
- Scheduled: {conflict.get('vessel_1', {}).get('start')} to {conflict.get('vessel_1', {}).get('end')}

Vessel 2: {vessel2.get('VesselName', 'Unknown')}
- Type: {vessel2.get('VesselType')}
- LOA: {vessel2.get('LOA')}m, Draft: {vessel2.get('Draft')}m
- Priority: {schedule2.get('Priority')}
- Scheduled: {conflict.get('vessel_2', {}).get('start')} to {conflict.get('vessel_2', {}).get('end')}

Overlap: {conflict.get('overlap_minutes', 0)} minutes

Alternative Berths Available: {len(alt_berths) if alt_berths else 0}

Provide resolution options in the following JSON format:
{{
    "primary_resolution": {{
        "strategy": "<time_shift|berth_swap|priority_override>",
        "action": {{
            "target_vessel": "<vessel_1|vessel_2>",
            "change_type": "<move_earlier|move_later|change_berth>",
            "new_value": "<new time or berth>",
            "justification": "<why this action>"
        }},
        "impact_score": <0-100 where 0=no impact, 100=major disruption>,
        "cascading_effects": ["<any downstream impacts>"]
    }},
    "alternative_resolutions": [
        {{
            "strategy": "<strategy>",
            "brief": "<description>",
            "impact_score": <0-100>
        }}
    ],
    "recommendation": "<final recommendation>",
    "urgency": "<immediate|within_hours|can_wait>"
}}"""

        try:
            result = self.invoke_structured(prompt=prompt, context=context)
            result["success"] = True
            result["original_conflict"] = conflict
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_conflict": conflict
            }

    def resolve_all(
        self,
        time_start: datetime,
        time_end: datetime,
        rag_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Detect and resolve all conflicts in a time window

        Args:
            time_start: Start of analysis window
            time_end: End of analysis window
            rag_context: Optional RAG context

        Returns:
            All conflicts with proposed resolutions
        """
        # First detect
        detection = self.detect_conflicts(time_start, time_end, rag_context)

        if not detection.get("success"):
            return detection

        # Then resolve each
        resolutions = []
        all_conflicts = []

        for conflict_type, conflicts in detection.get("conflicts", {}).items():
            for conflict in conflicts:
                resolution = self.resolve_conflict(conflict, rag_context)
                resolutions.append({
                    "conflict_type": conflict_type,
                    "conflict": conflict,
                    "resolution": resolution
                })
                all_conflicts.append(conflict)

        return {
            "success": True,
            "time_window": detection.get("time_window"),
            "total_conflicts": len(all_conflicts),
            "resolutions": resolutions,
            "summary": {
                "temporal_conflicts": len(detection["conflicts"]["temporal"]),
                "resource_conflicts": len(detection["conflicts"]["resource"]),
                "policy_conflicts": len(detection["conflicts"]["policy"]),
                "priority_conflicts": len(detection["conflicts"]["priority"])
            },
            "agent_stats": self.get_stats()
        }

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the conflict resolver agent

        Args:
            state: Contains time_start, time_end, and optional rag_context

        Returns:
            Updated state with conflict analysis and resolutions
        """
        time_start = state.get("time_start", datetime.now())
        time_end = state.get("time_end", datetime.now() + timedelta(hours=48))
        rag_context = state.get("rag_context")

        result = self.resolve_all(time_start, time_end, rag_context)

        state["conflict_analysis"] = result
        state["agent_stats"] = self.get_stats()

        return state
