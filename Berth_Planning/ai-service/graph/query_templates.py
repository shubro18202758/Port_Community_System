"""
SmartBerth AI - Cypher Query Templates
5 Cypher query templates for relationship-based reasoning
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """Types of graph queries"""
    SUITABLE_BERTHS = "suitable_berths"
    BERTH_EXPLANATION = "berth_explanation"
    CONFLICT_CASCADE = "conflict_cascade"
    RESOURCE_CONTENTION = "resource_contention"
    ALTERNATIVE_BERTHS = "alternative_berths"


@dataclass
class QueryTemplate:
    """A Cypher query template with metadata"""
    name: str
    description: str
    query_type: QueryType
    cypher: str
    parameters: List[str]
    explanation_prompt: str


class CypherQueryTemplates:
    """
    Collection of 5 Cypher query templates for SmartBerth reasoning:
    1. Find suitable berths for vessel
    2. Explain berth recommendation (multi-hop)
    3. Conflict cascade analysis
    4. Resource contention detection
    5. Alternative berth finder (with historical preference)
    """
    
    # Template 1: Find Suitable Berths for Vessel
    SUITABLE_BERTHS = QueryTemplate(
        name="Find Suitable Berths",
        description="Find all berths that can accommodate a vessel based on physical constraints",
        query_type=QueryType.SUITABLE_BERTHS,
        cypher="""
        // Find suitable berths for a vessel based on LOA, beam, draft constraints
        MATCH (v:Vessel {id: $vessel_id})
        MATCH (b:Berth)
        WHERE b.max_loa >= v.loa 
          AND b.max_beam >= v.beam 
          AND b.max_draft >= v.draft
          AND b.status = 'Active'
        
        // Get terminal and port info
        OPTIONAL MATCH (b)-[:BELONGS_TO]->(t:Terminal)-[:LOCATED_AT]->(p:Port)
        
        // Check for existing compatibility relationship
        OPTIONAL MATCH (v)-[comp:COMPATIBLE_WITH]->(b)
        
        // Check for scheduling conflicts
        OPTIONAL MATCH (other:Schedule)-[:ASSIGNED_TO]->(b)
        WHERE other.status IN ['Confirmed', 'Scheduled']
          AND other.eta <= $check_time_end 
          AND other.etd >= $check_time_start
        
        RETURN 
            b.id AS berth_id,
            b.name AS berth_name,
            b.type AS berth_type,
            t.name AS terminal_name,
            p.name AS port_name,
            b.max_loa - v.loa AS loa_margin,
            b.max_beam - v.beam AS beam_margin,
            b.max_draft - v.draft AS draft_margin,
            b.cargo_types AS cargo_types,
            b.has_shore_power AS has_shore_power,
            count(other) AS conflicting_schedules,
            comp IS NOT NULL AS pre_validated
        ORDER BY 
            conflicting_schedules ASC,
            loa_margin + beam_margin + draft_margin DESC
        """,
        parameters=["vessel_id", "check_time_start", "check_time_end"],
        explanation_prompt="""
        Explain why each berth is suitable for this vessel.
        Consider: physical fit (LOA, beam, draft margins), terminal capabilities,
        cargo type compatibility, and scheduling availability.
        Highlight the best options and any trade-offs.
        """
    )
    
    # Template 2: Berth Recommendation Explanation (Multi-hop)
    BERTH_EXPLANATION = QueryTemplate(
        name="Explain Berth Recommendation",
        description="Multi-hop traversal to explain why a berth is recommended",
        query_type=QueryType.BERTH_EXPLANATION,
        cypher="""
        // Multi-hop explanation of berth recommendation
        MATCH (v:Vessel {id: $vessel_id})
        MATCH (b:Berth {id: $berth_id})
        
        // Path 1: Physical constraints check
        WITH v, b,
            CASE 
                WHEN v.loa <= b.max_loa AND v.beam <= b.max_beam AND v.draft <= b.max_draft 
                THEN 'COMPATIBLE' 
                ELSE 'INCOMPATIBLE' 
            END AS physical_status,
            b.max_loa - v.loa AS loa_margin,
            b.max_beam - v.beam AS beam_margin,
            b.max_draft - v.draft AS draft_margin
        
        // Path 2: Terminal and port hierarchy
        OPTIONAL MATCH (b)-[:BELONGS_TO]->(t:Terminal)-[:LOCATED_AT]->(p:Port)
        
        // Path 3: Available resources at port
        OPTIONAL MATCH (pilot:Pilot)-[:OPERATES_AT]->(p)
        WHERE pilot.status = 'Available'
          AND pilot.max_loa >= v.loa
        
        OPTIONAL MATCH (tug:Tugboat)-[:BASED_AT]->(p)
        WHERE tug.status = 'Available'
        
        // Path 4: Channel access
        OPTIONAL MATCH (ch:Channel)-[:CONNECTS]->(p)
        WHERE ch.max_loa >= v.loa 
          AND ch.max_beam >= v.beam
          AND ch.max_draft >= v.draft
        
        // Path 5: Historical preference
        OPTIONAL MATCH (v)-[hist:HISTORICALLY_USED]->(b)
        
        // Path 6: Current/upcoming schedules at berth
        OPTIONAL MATCH (sched:Schedule)-[:ASSIGNED_TO]->(b)
        WHERE sched.status IN ['Confirmed', 'Scheduled', 'InProgress']
        
        RETURN 
            v.name AS vessel_name,
            v.type AS vessel_type,
            v.loa AS vessel_loa,
            v.beam AS vessel_beam,
            v.draft AS vessel_draft,
            
            b.name AS berth_name,
            b.type AS berth_type,
            b.max_loa AS berth_max_loa,
            b.max_beam AS berth_max_beam,
            b.max_draft AS berth_max_draft,
            b.cargo_types AS berth_cargo_types,
            
            physical_status,
            loa_margin,
            beam_margin,
            draft_margin,
            
            t.name AS terminal_name,
            t.type AS terminal_type,
            p.name AS port_name,
            
            count(DISTINCT pilot) AS available_pilots,
            count(DISTINCT tug) AS available_tugs,
            count(DISTINCT ch) AS accessible_channels,
            
            hist.visit_count AS historical_visits,
            hist.last_visit AS last_visit_date,
            
            collect(DISTINCT {
                schedule_id: sched.id,
                eta: sched.eta,
                etd: sched.etd,
                status: sched.status
            }) AS existing_schedules
        """,
        parameters=["vessel_id", "berth_id"],
        explanation_prompt="""
        Provide a comprehensive explanation of why this berth is recommended for the vessel.
        Walk through each constraint check:
        1. Physical fit analysis (LOA, beam, draft with margins)
        2. Terminal capabilities and cargo compatibility
        3. Resource availability (pilots, tugs)
        4. Channel accessibility for vessel dimensions
        5. Historical preference (if vessel has used this berth before)
        6. Current occupancy and scheduling status
        Conclude with a confidence score and any concerns.
        """
    )
    
    # Template 3: Conflict Cascade Analysis
    CONFLICT_CASCADE = QueryTemplate(
        name="Conflict Cascade Analysis",
        description="Analyze cascading effects when a schedule conflict occurs",
        query_type=QueryType.CONFLICT_CASCADE,
        cypher="""
        // Analyze cascade effects of a schedule conflict
        MATCH (primary:Schedule {id: $schedule_id})-[:ASSIGNED_TO]->(b:Berth)
        MATCH (primary_vessel:Vessel)-[:SCHEDULED_FOR]->(primary)
        
        // Find overlapping schedules at same berth
        MATCH (conflict:Schedule)-[:ASSIGNED_TO]->(b)
        WHERE conflict.id <> primary.id
          AND conflict.eta < primary.etd
          AND conflict.etd > primary.eta
          AND conflict.status IN ['Confirmed', 'Scheduled']
        
        // Get conflicting vessels
        MATCH (conflict_vessel:Vessel)-[:SCHEDULED_FOR]->(conflict)
        
        // Find alternative berths for conflicting vessels
        OPTIONAL MATCH (conflict_vessel)-[:COMPATIBLE_WITH]->(alt_berth:Berth)
        WHERE alt_berth.id <> b.id
          AND alt_berth.status = 'Active'
        
        // Check if alternative berths are available
        OPTIONAL MATCH (alt_conflict:Schedule)-[:ASSIGNED_TO]->(alt_berth)
        WHERE alt_conflict.eta < conflict.etd
          AND alt_conflict.etd > conflict.eta
          AND alt_conflict.status IN ['Confirmed', 'Scheduled']
        
        // Get terminal info for alternatives
        OPTIONAL MATCH (alt_berth)-[:BELONGS_TO]->(alt_term:Terminal)
        
        RETURN 
            primary.id AS primary_schedule_id,
            primary.eta AS primary_eta,
            primary.etd AS primary_etd,
            primary_vessel.name AS primary_vessel,
            b.name AS contested_berth,
            
            collect(DISTINCT {
                schedule_id: conflict.id,
                vessel_name: conflict_vessel.name,
                vessel_type: conflict_vessel.type,
                eta: conflict.eta,
                etd: conflict.etd,
                priority: conflict.priority,
                cargo_type: conflict.cargo_type,
                alternative_berths: collect(DISTINCT {
                    berth_id: alt_berth.id,
                    berth_name: alt_berth.name,
                    terminal: alt_term.name,
                    is_available: alt_conflict IS NULL
                })
            }) AS affected_schedules,
            
            count(DISTINCT conflict) AS total_conflicts,
            count(DISTINCT CASE WHEN alt_berth IS NOT NULL THEN conflict END) AS resolvable_conflicts
        """,
        parameters=["schedule_id"],
        explanation_prompt="""
        Analyze the scheduling conflict and its cascading effects.
        For each affected vessel/schedule:
        1. Explain the nature of the conflict (timing overlap)
        2. Assess priority levels and cargo urgency
        3. List viable alternative berths
        4. Recommend a resolution strategy
        5. Estimate operational impact (delays, costs)
        Provide a step-by-step resolution plan.
        """
    )
    
    # Template 4: Resource Contention Detection
    RESOURCE_CONTENTION = QueryTemplate(
        name="Resource Contention Detection",
        description="Detect resource contention (pilots, tugs, berths) at a given time window",
        query_type=QueryType.RESOURCE_CONTENTION,
        cypher="""
        // Detect resource contention at a port during a time window
        MATCH (p:Port {id: $port_id})
        
        // Find all scheduled operations in time window
        MATCH (sched:Schedule)-[:ASSIGNED_TO]->(b:Berth)-[:BELONGS_TO]->(t:Terminal)-[:LOCATED_AT]->(p)
        WHERE sched.eta <= $time_end AND sched.etd >= $time_start
          AND sched.status IN ['Confirmed', 'Scheduled', 'InProgress']
        
        MATCH (v:Vessel)-[:SCHEDULED_FOR]->(sched)
        
        // Count available resources
        OPTIONAL MATCH (pilot:Pilot)-[:OPERATES_AT]->(p)
        WHERE pilot.status = 'Available'
          AND pilot.max_loa >= v.loa
        
        OPTIONAL MATCH (tug:Tugboat)-[:BASED_AT]->(p)
        WHERE tug.status = 'Available'
        
        // Group by hour for demand analysis
        WITH p, sched, v, b,
            collect(DISTINCT pilot) AS qualified_pilots,
            collect(DISTINCT tug) AS available_tugs,
            datetime(sched.eta).hour AS arrival_hour
        
        RETURN 
            p.name AS port_name,
            count(DISTINCT sched) AS total_operations,
            count(DISTINCT b) AS berths_in_use,
            
            // Resource summary
            size(qualified_pilots) AS total_qualified_pilots,
            size(available_tugs) AS total_available_tugs,
            
            // Peak demand analysis
            collect({
                hour: arrival_hour,
                vessels: count(DISTINCT v),
                operations: count(DISTINCT sched)
            }) AS hourly_demand,
            
            // Detailed schedule list
            collect(DISTINCT {
                schedule_id: sched.id,
                vessel: v.name,
                vessel_type: v.type,
                vessel_loa: v.loa,
                berth: b.name,
                eta: sched.eta,
                etd: sched.etd,
                priority: sched.priority,
                pilots_available: size([p IN qualified_pilots WHERE p.max_loa >= v.loa]),
                tugs_needed: CASE WHEN v.loa > 200 THEN 2 ELSE 1 END
            }) AS operations,
            
            // Contention flags
            CASE 
                WHEN count(DISTINCT sched) > size(qualified_pilots) THEN 'PILOT_SHORTAGE'
                ELSE 'OK'
            END AS pilot_status,
            CASE 
                WHEN count(DISTINCT sched) * 2 > size(available_tugs) THEN 'TUG_SHORTAGE'
                ELSE 'OK'
            END AS tug_status
        """,
        parameters=["port_id", "time_start", "time_end"],
        explanation_prompt="""
        Analyze resource contention at this port during the specified time window.
        Report on:
        1. Overall operational load (number of vessel movements)
        2. Berth utilization
        3. Pilot availability vs demand (flag shortages)
        4. Tugboat availability vs demand
        5. Peak hours and bottlenecks
        6. Recommendations to resolve contention (staggering arrivals, additional resources)
        """
    )
    
    # Template 5: Alternative Berth Finder with Historical Preference
    ALTERNATIVE_BERTHS = QueryTemplate(
        name="Alternative Berth Finder",
        description="Find alternative berths considering historical preference and compatibility",
        query_type=QueryType.ALTERNATIVE_BERTHS,
        cypher="""
        // Find alternative berths for a vessel, ranked by historical preference
        MATCH (v:Vessel {id: $vessel_id})
        
        // Exclude the original berth if specified
        OPTIONAL MATCH (original:Berth {id: $exclude_berth_id})
        
        // Find compatible berths
        MATCH (b:Berth)
        WHERE b.max_loa >= v.loa 
          AND b.max_beam >= v.beam 
          AND b.max_draft >= v.draft
          AND b.status = 'Active'
          AND (original IS NULL OR b.id <> original.id)
        
        // Get terminal and port
        MATCH (b)-[:BELONGS_TO]->(t:Terminal)-[:LOCATED_AT]->(p:Port)
        
        // Check historical usage
        OPTIONAL MATCH (v)-[hist:HISTORICALLY_USED]->(b)
        
        // Check availability in requested time window
        OPTIONAL MATCH (conflict:Schedule)-[:ASSIGNED_TO]->(b)
        WHERE conflict.eta < $time_end 
          AND conflict.etd > $time_start
          AND conflict.status IN ['Confirmed', 'Scheduled']
        
        // Check cargo type compatibility
        WITH v, b, t, p, hist, conflict,
            CASE 
                WHEN v.type = 'Container' AND b.cargo_types CONTAINS 'Container' THEN 10
                WHEN v.type = 'Tanker' AND b.cargo_types CONTAINS 'Liquid' THEN 10
                WHEN v.type = 'Bulk' AND b.cargo_types CONTAINS 'Bulk' THEN 10
                WHEN v.type = 'LNG' AND b.cargo_types CONTAINS 'LNG' THEN 10
                ELSE 0
            END AS cargo_match_score
        
        RETURN 
            b.id AS berth_id,
            b.name AS berth_name,
            b.type AS berth_type,
            t.name AS terminal_name,
            p.name AS port_name,
            
            // Margins
            b.max_loa - v.loa AS loa_margin,
            b.max_beam - v.beam AS beam_margin,
            b.max_draft - v.draft AS draft_margin,
            
            // Historical preference
            COALESCE(hist.visit_count, 0) AS historical_visits,
            hist.last_visit AS last_visit,
            
            // Availability
            count(conflict) AS scheduling_conflicts,
            count(conflict) = 0 AS is_available,
            
            // Cargo compatibility
            b.cargo_types AS cargo_types,
            cargo_match_score,
            
            // Equipment
            b.has_shore_power AS has_shore_power,
            b.has_bunkering AS has_bunkering,
            
            // Composite ranking score
            (COALESCE(hist.visit_count, 0) * 5) + 
            cargo_match_score + 
            CASE WHEN count(conflict) = 0 THEN 20 ELSE 0 END +
            (b.max_loa - v.loa) / 10 AS ranking_score
            
        ORDER BY 
            scheduling_conflicts ASC,
            ranking_score DESC,
            historical_visits DESC
        LIMIT $limit
        """,
        parameters=["vessel_id", "exclude_berth_id", "time_start", "time_end", "limit"],
        explanation_prompt="""
        Present alternative berth options for this vessel.
        For each alternative, explain:
        1. Physical suitability (with safety margins)
        2. Historical usage pattern (familiarity bonus)
        3. Cargo handling compatibility
        4. Current availability status
        5. Terminal location and capabilities
        6. Overall recommendation score
        Conclude with a ranked recommendation and rationale.
        """
    )
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, QueryTemplate]:
        """Get all query templates"""
        return {
            QueryType.SUITABLE_BERTHS.value: cls.SUITABLE_BERTHS,
            QueryType.BERTH_EXPLANATION.value: cls.BERTH_EXPLANATION,
            QueryType.CONFLICT_CASCADE.value: cls.CONFLICT_CASCADE,
            QueryType.RESOURCE_CONTENTION.value: cls.RESOURCE_CONTENTION,
            QueryType.ALTERNATIVE_BERTHS.value: cls.ALTERNATIVE_BERTHS,
        }
    
    @classmethod
    def get_template(cls, query_type: QueryType) -> Optional[QueryTemplate]:
        """Get a specific query template"""
        templates = cls.get_all_templates()
        return templates.get(query_type.value)
    
    @classmethod
    def get_template_by_name(cls, name: str) -> Optional[QueryTemplate]:
        """Get template by name string"""
        try:
            query_type = QueryType(name)
            return cls.get_template(query_type)
        except ValueError:
            return None


def get_query_templates() -> CypherQueryTemplates:
    """Get query templates instance"""
    return CypherQueryTemplates()


if __name__ == "__main__":
    print("=" * 60)
    print("SmartBerth AI - Cypher Query Templates")
    print("=" * 60)
    
    templates = CypherQueryTemplates.get_all_templates()
    
    for name, template in templates.items():
        print(f"\n📋 Template: {template.name}")
        print(f"   Type: {name}")
        print(f"   Description: {template.description}")
        print(f"   Parameters: {', '.join(template.parameters)}")
        print(f"   Query length: {len(template.cypher)} chars")
