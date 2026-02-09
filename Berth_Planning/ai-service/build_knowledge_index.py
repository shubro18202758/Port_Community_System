"""
SmartBerth AI - Comprehensive Knowledge Index Builder
=====================================================

This module builds a unified knowledge index from:
1. Knowledge Base Documents (markdown files)
2. Training Database (CSV files with real port operations data)
3. Data Flow Architecture documentation

The index enables intelligent retrieval for:
- Domain knowledge (constraints, rules, best practices)
- Real-world data patterns (vessels, berths, weather)
- Operational context (UKC, pilots, tugs, channels)

Milestone 1: Build the actual index from knowledge base documents
"""

import os
import csv
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class KnowledgeType(Enum):
    """Types of knowledge in the index"""
    DOMAIN_RULE = "domain_rule"           # Constraint rules, validation logic
    DOMAIN_CONCEPT = "domain_concept"     # Berth planning concepts
    OPERATIONAL_DATA = "operational_data" # Training data patterns
    ENTITY_PROFILE = "entity_profile"     # Port/Vessel/Berth profiles
    HISTORICAL = "historical"             # Past events, patterns
    PROCEDURE = "procedure"               # Standard operating procedures


@dataclass
class KnowledgeChunk:
    """A chunk of knowledge for indexing"""
    id: str
    content: str
    knowledge_type: KnowledgeType
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    entities: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None


@dataclass
class IndexStats:
    """Statistics about the built index"""
    total_chunks: int = 0
    chunks_by_type: Dict[str, int] = field(default_factory=dict)
    entities_indexed: int = 0
    sources_processed: int = 0
    build_time_seconds: float = 0.0


# ============================================================================
# TRAINING DATA PROCESSORS
# ============================================================================

class TrainingDataProcessor:
    """Process CSV training data into knowledge chunks"""
    
    def __init__(self, train_db_path: str):
        self.train_db_path = train_db_path
        self.chunks: List[KnowledgeChunk] = []
        self.chunk_counter = 0
    
    def _make_chunk_id(self, prefix: str) -> str:
        self.chunk_counter += 1
        return f"{prefix}_{self.chunk_counter}"
    
    def process_all(self) -> List[KnowledgeChunk]:
        """Process all training data files"""
        logger.info(f"Processing training data from: {self.train_db_path}")
        
        # Process each data type
        self._process_ports()
        self._process_terminals()
        self._process_berths()
        self._process_vessels()
        self._process_vessel_calls()
        self._process_pilots()
        self._process_tugboats()
        self._process_channels()
        self._process_anchorages()
        self._process_ukc()
        self._process_weather_summary()
        
        logger.info(f"Generated {len(self.chunks)} knowledge chunks from training data")
        return self.chunks
    
    def _read_csv(self, filename: str) -> List[Dict]:
        """Read CSV file and return list of dictionaries"""
        filepath = os.path.join(self.train_db_path, filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def _process_ports(self):
        """Process port parameters into knowledge chunks"""
        data = self._read_csv("SmartBerth_AI_Port_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} port records...")
        
        # Create port profiles
        for row in data:
            content = f"""Port Profile: {row.get('portName', 'Unknown')} ({row.get('portCode', '')})
Country: {row.get('country', 'Unknown')}, City: {row.get('city', 'Unknown')}
Location: {row.get('latitude', '')}°N, {row.get('longitude', '')}°E
Timezone: {row.get('timezone', 'UTC')}
Contact: {row.get('contactEmail', '')} | {row.get('contactPhone', '')}
Status: {'Active' if row.get('isActive') == 'TRUE' else 'Inactive'}

This port is part of the SmartBerth network for intelligent berth planning and allocation."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id("port"),
                content=content,
                knowledge_type=KnowledgeType.ENTITY_PROFILE,
                source="SmartBerth_AI_Port_Parameters_Training_Data.csv",
                metadata={
                    "portId": row.get('portId'),
                    "portCode": row.get('portCode'),
                    "country": row.get('country'),
                    "timezone": row.get('timezone')
                },
                entities=[row.get('portName', ''), row.get('portCode', '')]
            ))
        
        # Create regional summary
        regions = {}
        for row in data:
            country = row.get('country', 'Unknown')
            if country not in regions:
                regions[country] = []
            regions[country].append(row.get('portCode', ''))
        
        summary_content = "SmartBerth Network Port Summary:\n\n"
        for country, ports in regions.items():
            summary_content += f"• {country}: {len(ports)} ports ({', '.join(ports[:5])}{'...' if len(ports) > 5 else ''})\n"
        
        summary_content += f"\nTotal: {len(data)} ports across {len(regions)} countries."
        
        self.chunks.append(KnowledgeChunk(
            id=self._make_chunk_id("port_summary"),
            content=summary_content,
            knowledge_type=KnowledgeType.DOMAIN_CONCEPT,
            source="SmartBerth_AI_Port_Parameters_Training_Data.csv",
            metadata={"total_ports": len(data), "countries": list(regions.keys())},
            entities=list(regions.keys())
        ))
    
    def _process_terminals(self):
        """Process terminal parameters"""
        data = self._read_csv("SmartBerth_AI_Terminal_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} terminal records...")
        
        # Group by terminal type
        by_type = {}
        for row in data:
            t_type = row.get('terminalType', 'Unknown')
            if t_type not in by_type:
                by_type[t_type] = []
            by_type[t_type].append(row)
        
        for term_type, terminals in by_type.items():
            content = f"""Terminal Type: {term_type}

Count: {len(terminals)} terminals across the SmartBerth network

Key Characteristics:
"""
            # Sample some terminals
            for term in terminals[:5]:
                content += f"""
• {term.get('terminalName', 'Unknown')} ({term.get('terminalCode', '')})
  - Port: {term.get('portId')} | Operator: {term.get('operatorName', 'Unknown')}
  - Berths: {term.get('totalBerths', 'N/A')}
  - Location: ({term.get('latitude', '')}, {term.get('longitude', '')})
  - Active: {term.get('isActive', 'FALSE')}
"""
            
            if len(terminals) > 5:
                content += f"\n... and {len(terminals) - 5} more {term_type} terminals."
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"terminal_{term_type.lower()}"),
                content=content,
                knowledge_type=KnowledgeType.ENTITY_PROFILE,
                source="SmartBerth_AI_Terminal_Parameters_Training_Data.csv",
                metadata={"terminalType": term_type, "count": len(terminals)},
                entities=[term_type] + [t.get('terminalCode', '') for t in terminals[:10]]
            ))
    
    def _process_berths(self):
        """Process berth parameters - critical for allocation decisions"""
        data = self._read_csv("SmartBerth_AI_Berth_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} berth records...")
        
        # Group by berth type
        by_type = {}
        for row in data:
            b_type = row.get('berthType', 'General')
            if b_type not in by_type:
                by_type[b_type] = []
            by_type[b_type].append(row)
        
        for berth_type, berths in by_type.items():
            # Calculate averages for this berth type
            lengths = [float(b.get('length', 0)) for b in berths if b.get('length')]
            depths = [float(b.get('depth', 0)) for b in berths if b.get('depth')]
            max_loas = [float(b.get('maxLOA', 0)) for b in berths if b.get('maxLOA')]
            
            content = f"""Berth Type Analysis: {berth_type}

Total Berths: {len(berths)} in SmartBerth network

Physical Characteristics:
• Average Length: {sum(lengths)/len(lengths):.1f}m (range: {min(lengths):.1f}m - {max(lengths):.1f}m)
• Average Depth: {sum(depths)/len(depths):.1f}m (range: {min(depths):.1f}m - {max(depths):.1f}m)
• Average Max LOA: {sum(max_loas)/len(max_loas):.1f}m (range: {min(max_loas):.1f}m - {max(max_loas):.1f}m)

This berth type is suitable for vessels matching these dimensional constraints.
Berth allocation algorithm should prioritize matching vessel dimensions to berth capacity."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"berth_type_{berth_type.lower()}"),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source="SmartBerth_AI_Berth_Parameters_Training_Data.csv",
                metadata={
                    "berthType": berth_type,
                    "count": len(berths),
                    "avgLength": sum(lengths)/len(lengths) if lengths else 0,
                    "avgDepth": sum(depths)/len(depths) if depths else 0
                },
                entities=[berth_type, "berth allocation", "dimensional constraints"]
            ))
    
    def _process_vessels(self):
        """Process vessel parameters"""
        data = self._read_csv("SmartBerth_AI_Vessel_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} vessel records...")
        
        # Group by vessel type
        by_type = {}
        for row in data:
            v_type = row.get('vessel_type', 'Unknown')
            if v_type not in by_type:
                by_type[v_type] = []
            by_type[v_type].append(row)
        
        for vessel_type, vessels in by_type.items():
            loas = [float(v.get('loa', 0)) for v in vessels if v.get('loa')]
            beams = [float(v.get('beam', 0)) for v in vessels if v.get('beam')]
            drafts = [float(v.get('draft', 0)) for v in vessels if v.get('draft')]
            
            if not loas:
                continue
            
            content = f"""Vessel Type Profile: {vessel_type.replace('_', ' ')}

Fleet Statistics (SmartBerth Network):
• Total Vessels: {len(vessels)}
• LOA Range: {min(loas):.1f}m - {max(loas):.1f}m (avg: {sum(loas)/len(loas):.1f}m)
• Beam Range: {min(beams):.1f}m - {max(beams):.1f}m (avg: {sum(beams)/len(beams):.1f}m) if beams else 'N/A'
• Draft Range: {min(drafts):.1f}m - {max(drafts):.1f}m (avg: {sum(drafts)/len(drafts):.1f}m) if drafts else 'N/A'

Cargo Types Handled:
"""
            cargo_types = set(v.get('cargoType', 'Unknown') for v in vessels)
            for cargo in list(cargo_types)[:5]:
                content += f"• {cargo}\n"
            
            content += f"""
Berth Requirements:
- Minimum berth length should exceed vessel LOA by 10-15%
- Water depth must accommodate maximum draft plus UKC allowance
- Beam considerations for fendering and mooring"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"vessel_type_{vessel_type.lower()}"),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source="SmartBerth_AI_Vessel_Parameters_Training_Data.csv",
                metadata={
                    "vesselType": vessel_type,
                    "count": len(vessels),
                    "avgLOA": sum(loas)/len(loas) if loas else 0,
                    "cargoTypes": list(cargo_types)[:5]
                },
                entities=[vessel_type] + list(cargo_types)[:5]
            ))
    
    def _process_vessel_calls(self):
        """Process vessel call assignment data - key training examples"""
        data = self._read_csv("SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} vessel call records...")
        
        # Analyze waiting times by port
        by_port = {}
        for row in data:
            port = row.get('portCode', 'Unknown')
            if port not in by_port:
                by_port[port] = []
            by_port[port].append(row)
        
        for port_code, calls in list(by_port.items())[:20]:  # Top 20 ports
            waiting_times = [float(c.get('waitingTimeHours', 0)) for c in calls if c.get('waitingTimeHours')]
            dwell_times = [float(c.get('dwellTimeHours', 0)) for c in calls if c.get('dwellTimeHours')]
            
            if not waiting_times:
                continue
            
            content = f"""Port Operations Analysis: {port_code}

Historical Vessel Calls: {len(calls)}

Performance Metrics:
• Average Waiting Time: {sum(waiting_times)/len(waiting_times):.1f} hours
• Max Waiting Time: {max(waiting_times):.1f} hours
• Average Dwell Time: {sum(dwell_times)/len(dwell_times):.1f} hours if dwell_times else 'N/A'

Common Vessel Types:
"""
            vessel_types = {}
            for call in calls:
                vt = call.get('vesselType', 'Unknown')
                vessel_types[vt] = vessel_types.get(vt, 0) + 1
            
            for vt, count in sorted(vessel_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                content += f"• {vt}: {count} calls ({count/len(calls)*100:.1f}%)\n"
            
            content += f"""
Resource Requirements (average):
• Tugs Required: {sum(int(c.get('tugsRequired', 0)) for c in calls)/len(calls):.1f}
• Pilots Required: {sum(int(c.get('pilotsRequired', 0)) for c in calls)/len(calls):.1f}

This data represents historical berth assignment decisions for optimization learning."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"port_ops_{port_code.lower()}"),
                content=content,
                knowledge_type=KnowledgeType.HISTORICAL,
                source="SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv",
                metadata={
                    "portCode": port_code,
                    "totalCalls": len(calls),
                    "avgWaitingTime": sum(waiting_times)/len(waiting_times) if waiting_times else 0
                },
                entities=[port_code] + list(vessel_types.keys())[:5]
            ))
        
        # Overall assignment statistics
        total_calls = len(data)
        all_waiting = [float(c.get('waitingTimeHours', 0)) for c in data if c.get('waitingTimeHours')]
        
        summary = f"""SmartBerth Vessel Call Assignment Training Data Summary

Total Historical Calls: {total_calls}
Ports Covered: {len(by_port)}

Network-wide Performance:
• Overall Average Waiting Time: {sum(all_waiting)/len(all_waiting):.1f} hours
• Calls with Zero Wait: {sum(1 for w in all_waiting if w == 0)} ({sum(1 for w in all_waiting if w == 0)/len(all_waiting)*100:.1f}%)
• Calls with >24hr Wait: {sum(1 for w in all_waiting if w > 24)} ({sum(1 for w in all_waiting if w > 24)/len(all_waiting)*100:.1f}%)

This training data is used by the AI to learn optimal berth assignment patterns."""
        
        self.chunks.append(KnowledgeChunk(
            id=self._make_chunk_id("vessel_calls_summary"),
            content=summary,
            knowledge_type=KnowledgeType.HISTORICAL,
            source="SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv",
            metadata={"totalCalls": total_calls, "portsCount": len(by_port)},
            entities=["vessel calls", "berth assignment", "waiting time", "optimization"]
        ))
    
    def _process_pilots(self):
        """Process pilotage parameters"""
        data = self._read_csv("SmartBerth_AI_Pilotage_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} pilot records...")
        
        # Group by pilot type
        by_type = {}
        for row in data:
            p_type = row.get('pilotType', 'Harbor')
            if p_type not in by_type:
                by_type[p_type] = []
            by_type[p_type].append(row)
        
        for pilot_type, pilots in by_type.items():
            exp_years = [int(p.get('experienceYears', 0)) for p in pilots if p.get('experienceYears')]
            
            content = f"""Pilot Resource Profile: {pilot_type} Pilots

Total Available: {len(pilots)}
Average Experience: {sum(exp_years)/len(exp_years):.1f} years

Certification Levels:
"""
            cert_levels = {}
            for p in pilots:
                level = p.get('certificationLevel', 'Unknown')
                cert_levels[level] = cert_levels.get(level, 0) + 1
            
            for level, count in sorted(cert_levels.items(), key=lambda x: x[1], reverse=True):
                content += f"• {level}: {count} pilots\n"
            
            # Night operations capability
            night_capable = sum(1 for p in pilots if p.get('nightOperations') == 'TRUE')
            adverse_weather = sum(1 for p in pilots if p.get('adverseWeather') == 'TRUE')
            
            content += f"""
Special Capabilities:
• Night Operations Certified: {night_capable} ({night_capable/len(pilots)*100:.1f}%)
• Adverse Weather Certified: {adverse_weather} ({adverse_weather/len(pilots)*100:.1f}%)

Pilot scheduling must consider certification levels, vessel restrictions, and weather conditions."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"pilot_{pilot_type.lower()}"),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source="SmartBerth_AI_Pilotage_Parameters_Training_Data.csv",
                metadata={"pilotType": pilot_type, "count": len(pilots)},
                entities=[pilot_type, "pilot", "pilotage", "scheduling"]
            ))
    
    def _process_tugboats(self):
        """Process tugboat parameters"""
        data = self._read_csv("SmartBerth_AI_Tugboat_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} tugboat records...")
        
        # Group by tug type
        by_type = {}
        for row in data:
            t_type = row.get('tugType', 'Conventional')
            if t_type not in by_type:
                by_type[t_type] = []
            by_type[t_type].append(row)
        
        for tug_type, tugs in by_type.items():
            bollard_pulls = [int(t.get('bollardPull', 0)) for t in tugs if t.get('bollardPull')]
            
            if not bollard_pulls:
                continue
            
            content = f"""Tug Fleet Profile: {tug_type} ({tugs[0].get('tugTypeFullName', tug_type)})

Fleet Size: {len(tugs)}

Bollard Pull Capacity:
• Average: {sum(bollard_pulls)/len(bollard_pulls):.0f} tons
• Range: {min(bollard_pulls)} - {max(bollard_pulls)} tons

Classes Available:
"""
            classes = {}
            for t in tugs:
                tc = t.get('tugClass', 'Unknown')
                classes[tc] = classes.get(tc, 0) + 1
            
            for tc, count in sorted(classes.items()):
                content += f"• {tc}: {count} tugs\n"
            
            # FiFi capability
            fifi = {}
            for t in tugs:
                ff = t.get('fifiClass', 'None')
                fifi[ff] = fifi.get(ff, 0) + 1
            
            content += "\nFire-Fighting Capability:\n"
            for ff, count in sorted(fifi.items()):
                content += f"• {ff}: {count} tugs\n"
            
            content += """
Tug assignment depends on vessel size, weather conditions, and berth configuration.
Larger vessels require higher bollard pull capacity for safe maneuvering."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"tug_{tug_type.lower()}"),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source="SmartBerth_AI_Tugboat_Parameters_Training_Data.csv",
                metadata={"tugType": tug_type, "count": len(tugs), "avgBollardPull": sum(bollard_pulls)/len(bollard_pulls)},
                entities=[tug_type, "tugboat", "tug", "bollard pull", "berthing assistance"]
            ))
    
    def _process_channels(self):
        """Process channel parameters - critical for navigation"""
        data = self._read_csv("SmartBerth_AI_Channel_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} channel records...")
        
        # Sample channels for knowledge
        for row in data[:20]:  # First 20 channels
            content = f"""Navigation Channel: {row.get('channelName', 'Unknown')}

Physical Characteristics:
• Length: {row.get('channelLength', 'N/A')}m
• Width: {row.get('channelWidth', 'N/A')}m
• Depth: {row.get('channelDepth', 'N/A')}m (Chart Datum: {row.get('channelDepthAtChartDatum', 'N/A')}m)
• Configuration: {row.get('oneWayOrTwoWay', 'One-Way')}

Vessel Restrictions:
• Max LOA: {row.get('maxVesselLOA', 'N/A')}m
• Max Beam: {row.get('maxVesselBeam', 'N/A')}m
• Max Draft: {row.get('maxVesselDraft', 'N/A')}m
• Speed Limit: {row.get('speedLimit', 'N/A')} knots

Operational Requirements:
• Traffic Separation: {'Yes' if row.get('trafficSeparationScheme') == 'TRUE' else 'No'}
• Tidal Window Required: {'Yes' if row.get('tidalWindowRequired') == 'TRUE' else 'No'}
• Pilotage Compulsory: {'Yes' if row.get('pilotageCompulsory') == 'TRUE' else 'No'}
• Tug Escort Required: {'Yes' if row.get('tugEscortRequired') == 'TRUE' else 'No'}
• Day/Night: {row.get('dayNightRestrictions', '24/7 Operations')}

Environmental Limits:
• Minimum Visibility: {row.get('visibilityMinimum', 'N/A')}m
• Wind Speed Limit: {row.get('windSpeedLimit', 'N/A')} knots
• Current Speed Limit: {row.get('currentSpeedLimit', 'N/A')} knots"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"channel_{row.get('channelId', 0)}"),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source="SmartBerth_AI_Channel_Parameters_Training_Data.csv",
                metadata={
                    "channelId": row.get('channelId'),
                    "portId": row.get('portId'),
                    "maxLOA": row.get('maxVesselLOA'),
                    "maxDraft": row.get('maxVesselDraft')
                },
                entities=[row.get('channelName', ''), "navigation channel", "vessel transit"]
            ))
    
    def _process_anchorages(self):
        """Process anchorage parameters"""
        data = self._read_csv("SmartBerth_AI_Anchorage_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} anchorage records...")
        
        # Group by type
        by_type = {}
        for row in data:
            a_type = row.get('anchorageType', 'General')
            if a_type not in by_type:
                by_type[a_type] = []
            by_type[a_type].append(row)
        
        for anch_type, anchorages in by_type.items():
            avg_wait = [float(a.get('averageWaitingTime', 0)) for a in anchorages if a.get('averageWaitingTime')]
            total_capacity = sum(int(a.get('maxVessels', 0)) for a in anchorages)
            
            content = f"""Anchorage Type: {anch_type}

Network Coverage: {len(anchorages)} anchorages
Total Vessel Capacity: {total_capacity}
Average Waiting Time: {sum(avg_wait)/len(avg_wait):.1f} hours

Typical Characteristics:
• Max Vessel LOA Range: {min(float(a.get('maxVesselLOA', 0)) for a in anchorages):.0f}m - {max(float(a.get('maxVesselLOA', 0)) for a in anchorages):.0f}m
• Max Draft Range: {min(float(a.get('maxVesselDraft', 0)) for a in anchorages):.1f}m - {max(float(a.get('maxVesselDraft', 0)) for a in anchorages):.1f}m

Special Features:
• STS Operations Permitted: {sum(1 for a in anchorages if a.get('stsCargOpsPermitted') == 'TRUE')} anchorages
• Quarantine Anchorages: {sum(1 for a in anchorages if a.get('quarantineAnchorage') == 'TRUE')} anchorages

Anchorage selection depends on vessel size, cargo type, and expected waiting duration."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"anchorage_{anch_type.lower()}"),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source="SmartBerth_AI_Anchorage_Parameters_Training_Data.csv",
                metadata={"anchorageType": anch_type, "count": len(anchorages), "totalCapacity": total_capacity},
                entities=[anch_type, "anchorage", "waiting area", "vessel queue"]
            ))
    
    def _process_ukc(self):
        """Process UKC (Under Keel Clearance) calculations"""
        data = self._read_csv("SmartBerth_AI_UKC_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} UKC records...")
        
        # Analyze UKC patterns by vessel type
        by_vessel_type = {}
        for row in data:
            vt = row.get('vesselType', 'Unknown')
            if vt not in by_vessel_type:
                by_vessel_type[vt] = []
            by_vessel_type[vt].append(row)
        
        for vessel_type, records in by_vessel_type.items():
            ukc_values = [float(r.get('calculatedUKC', 0)) for r in records if r.get('calculatedUKC')]
            required_ukc = [float(r.get('requiredUKC', 0)) for r in records if r.get('requiredUKC')]
            
            if not ukc_values:
                continue
            
            # Count status distribution
            status_dist = {}
            for r in records:
                status = r.get('ukcStatus', 'Unknown')
                status_dist[status] = status_dist.get(status, 0) + 1
            
            content = f"""UKC Analysis: {vessel_type.replace('_', ' ')}

Sample Size: {len(records)} transit calculations

UKC Statistics:
• Average Calculated UKC: {sum(ukc_values)/len(ukc_values):.2f}m
• Average Required UKC: {sum(required_ukc)/len(required_ukc):.2f}m
• UKC Range: {min(ukc_values):.2f}m - {max(ukc_values):.2f}m

Transit Status Distribution:
"""
            for status, count in sorted(status_dist.items(), key=lambda x: x[1], reverse=True):
                content += f"• {status}: {count} ({count/len(records)*100:.1f}%)\n"
            
            # Analyze allowances
            squat_vals = [float(r.get('squatAllowance', 0)) for r in records if r.get('squatAllowance')]
            wave_vals = [float(r.get('waveResponseAllowance', 0)) for r in records if r.get('waveResponseAllowance')]
            
            content += f"""
Typical Allowances:
• Squat Allowance: {sum(squat_vals)/len(squat_vals):.2f}m average
• Wave Response: {sum(wave_vals)/len(wave_vals):.2f}m average

UKC Formula: Static Draft + Squat + Heel + Wave Response + Safety Margin
Transit should only proceed when calculatedUKC >= requiredUKC."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"ukc_{vessel_type.lower()}"),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source="SmartBerth_AI_UKC_Training_Data.csv",
                metadata={
                    "vesselType": vessel_type,
                    "sampleSize": len(records),
                    "avgUKC": sum(ukc_values)/len(ukc_values) if ukc_values else 0
                },
                entities=[vessel_type, "UKC", "under keel clearance", "navigation safety", "tidal window"]
            ))
    
    def _process_weather_summary(self):
        """Process weather data into summary patterns"""
        data = self._read_csv("SmartBerth_AI_Weather_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"Processing {len(data)} weather records (summary only)...")
        
        # Group by port and get statistics
        by_port = {}
        for row in data[:10000]:  # Sample first 10k for speed
            port = row.get('portCode', 'Unknown')
            if port not in by_port:
                by_port[port] = []
            by_port[port].append(row)
        
        # Create weather profiles for top ports
        for port_code, records in list(by_port.items())[:15]:
            wind_speeds = [float(r.get('windSpeed', 0)) for r in records if r.get('windSpeed')]
            wave_heights = [float(r.get('waveHeight', 0)) for r in records if r.get('waveHeight')]
            visibilities = [float(r.get('visibility', 10000)) for r in records if r.get('visibility')]
            
            if not wind_speeds:
                continue
            
            # Count conditions
            conditions = {}
            for r in records:
                cond = r.get('weatherCondition', 'Unknown')
                conditions[cond] = conditions.get(cond, 0) + 1
            
            alert_count = sum(1 for r in records if r.get('isAlert') == 'TRUE')
            
            content = f"""Weather Profile: Port {port_code}

Data Period: Based on {len(records)} hourly observations

Wind Conditions:
• Average Speed: {sum(wind_speeds)/len(wind_speeds):.1f} knots
• Max Speed: {max(wind_speeds):.1f} knots
• High Wind Events (>25 knots): {sum(1 for w in wind_speeds if w > 25)} observations

Sea State:
• Average Wave Height: {sum(wave_heights)/len(wave_heights):.2f}m
• Max Wave Height: {max(wave_heights):.2f}m

Visibility:
• Average: {sum(visibilities)/len(visibilities):.0f}m
• Low Visibility Events (<1000m): {sum(1 for v in visibilities if v < 1000)} observations

Weather Conditions:
"""
            for cond, count in sorted(conditions.items(), key=lambda x: x[1], reverse=True)[:5]:
                content += f"• {cond}: {count/len(records)*100:.1f}%\n"
            
            content += f"""
Weather Alerts: {alert_count} ({alert_count/len(records)*100:.1f}% of time)

Weather impacts vessel operations through:
- Wind limits for crane operations and vessel handling
- Wave height affects UKC and vessel motion
- Visibility affects pilotage and channel transit"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_chunk_id(f"weather_{port_code.lower()}"),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source="SmartBerth_AI_Weather_Parameters_Training_Data.csv",
                metadata={
                    "portCode": port_code,
                    "observations": len(records),
                    "avgWindSpeed": sum(wind_speeds)/len(wind_speeds) if wind_speeds else 0,
                    "alertRate": alert_count/len(records) if records else 0
                },
                entities=[port_code, "weather", "wind", "waves", "visibility", "operations"]
            ))


# ============================================================================
# DOCUMENT PROCESSORS
# ============================================================================

class DocumentProcessor:
    """Process markdown knowledge documents"""
    
    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = knowledge_base_path
        self.chunks: List[KnowledgeChunk] = []
        self.chunk_counter = 0
    
    def _make_chunk_id(self, prefix: str) -> str:
        self.chunk_counter += 1
        return f"{prefix}_{self.chunk_counter}"
    
    def process_all(self) -> List[KnowledgeChunk]:
        """Process all markdown documents"""
        logger.info(f"Processing knowledge documents from: {self.knowledge_base_path}")
        
        for filename in os.listdir(self.knowledge_base_path):
            if filename.endswith('.md') and filename != 'KNOWLEDGE_SUMMARY.md':
                self._process_document(os.path.join(self.knowledge_base_path, filename))
        
        logger.info(f"Generated {len(self.chunks)} knowledge chunks from documents")
        return self.chunks
    
    def _process_document(self, filepath: str):
        """Process a single markdown document"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        filename = os.path.basename(filepath)
        
        # Determine knowledge type based on filename
        if 'constraint' in filename.lower():
            k_type = KnowledgeType.DOMAIN_RULE
        elif 'knowledge' in filename.lower() or 'domain' in filename.lower():
            k_type = KnowledgeType.DOMAIN_CONCEPT
        elif 'procedure' in filename.lower() or 'process' in filename.lower():
            k_type = KnowledgeType.PROCEDURE
        else:
            k_type = KnowledgeType.DOMAIN_CONCEPT
        
        # Extract sections
        sections = self._extract_sections(content)
        
        for section in sections:
            if len(section['content'].strip()) < 50:
                continue
            
            # Chunk large sections
            chunks = self._chunk_content(section['content'], 800, 100)
            
            for i, chunk in enumerate(chunks):
                self.chunks.append(KnowledgeChunk(
                    id=self._make_chunk_id(f"doc_{filename.replace('.md', '')}"),
                    content=chunk,
                    knowledge_type=k_type,
                    source=filename,
                    metadata={
                        "section": section['header'],
                        "section_level": section['level'],
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    },
                    entities=self._extract_entities(chunk)
                ))
    
    def _extract_sections(self, content: str) -> List[Dict]:
        """Extract sections from markdown"""
        sections = []
        current = {"header": "Introduction", "content": "", "level": 0}
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current["content"].strip():
                    sections.append(current)
                current = {"header": line[3:].strip(), "content": "", "level": 2}
            elif line.startswith('### '):
                if current["content"].strip():
                    sections.append(current)
                current = {"header": line[4:].strip(), "content": "", "level": 3}
            elif line.startswith('# '):
                if current["content"].strip():
                    sections.append(current)
                current = {"header": line[2:].strip(), "content": "", "level": 1}
            else:
                current["content"] += line + "\n"
        
        if current["content"].strip():
            sections.append(current)
        
        return sections
    
    def _chunk_content(self, content: str, chunk_size: int, overlap: int) -> List[str]:
        """Split content into overlapping chunks"""
        words = content.split()
        chunks = []
        
        i = 0
        while i < len(words):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
            i += chunk_size - overlap
        
        return chunks if chunks else [content]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential entities from text"""
        entities = []
        
        # Look for port-related terms
        if 'berth' in text.lower():
            entities.append('berth')
        if 'vessel' in text.lower():
            entities.append('vessel')
        if 'ukc' in text.lower() or 'under keel' in text.lower():
            entities.append('UKC')
        if 'pilot' in text.lower():
            entities.append('pilot')
        if 'tug' in text.lower():
            entities.append('tug')
        if 'weather' in text.lower():
            entities.append('weather')
        if 'constraint' in text.lower():
            entities.append('constraint')
        if 'allocation' in text.lower():
            entities.append('allocation')
        if 'eta' in text.lower():
            entities.append('ETA')
        
        return entities


# ============================================================================
# INDEX BUILDER
# ============================================================================

class KnowledgeIndexBuilder:
    """Build and manage the unified knowledge index"""
    
    def __init__(
        self,
        knowledge_base_path: str,
        training_data_path: str,
        chroma_path: str = None
    ):
        self.knowledge_base_path = knowledge_base_path
        self.training_data_path = training_data_path
        self.chroma_path = chroma_path or os.path.join(
            os.path.dirname(knowledge_base_path), "chroma_db_unified"
        )
        self.all_chunks: List[KnowledgeChunk] = []
        self.stats = IndexStats()
    
    def build_index(self) -> IndexStats:
        """Build the complete knowledge index"""
        start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("SmartBerth AI - Building Unified Knowledge Index")
        logger.info("=" * 60)
        
        # Process knowledge documents
        doc_processor = DocumentProcessor(self.knowledge_base_path)
        doc_chunks = doc_processor.process_all()
        self.all_chunks.extend(doc_chunks)
        
        # Process training data
        train_processor = TrainingDataProcessor(self.training_data_path)
        train_chunks = train_processor.process_all()
        self.all_chunks.extend(train_chunks)
        
        # Build statistics
        self.stats.total_chunks = len(self.all_chunks)
        for chunk in self.all_chunks:
            type_name = chunk.knowledge_type.value
            self.stats.chunks_by_type[type_name] = self.stats.chunks_by_type.get(type_name, 0) + 1
        
        # Count unique entities
        all_entities = set()
        for chunk in self.all_chunks:
            all_entities.update(chunk.entities)
        self.stats.entities_indexed = len(all_entities)
        
        self.stats.build_time_seconds = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Index Build Complete!")
        logger.info(f"  Total Chunks: {self.stats.total_chunks}")
        logger.info(f"  Entities: {self.stats.entities_indexed}")
        logger.info(f"  Build Time: {self.stats.build_time_seconds:.2f}s")
        logger.info(f"  Chunks by Type:")
        for k, v in self.stats.chunks_by_type.items():
            logger.info(f"    - {k}: {v}")
        logger.info("=" * 60)
        
        return self.stats
    
    def load_to_chromadb(self, collection_name: str = "smartberth_unified") -> bool:
        """Load all chunks into ChromaDB"""
        try:
            import chromadb
            
            logger.info(f"\nLoading {len(self.all_chunks)} chunks to ChromaDB...")
            logger.info(f"  Path: {self.chroma_path}")
            
            os.makedirs(self.chroma_path, exist_ok=True)
            client = chromadb.PersistentClient(path=self.chroma_path)
            
            # Delete existing collection
            try:
                client.delete_collection(collection_name)
                logger.info(f"  Deleted existing collection: {collection_name}")
            except:
                pass
            
            # Create new collection
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": "SmartBerth Unified Knowledge Index"}
            )
            
            # Prepare data for batch insert
            ids = []
            documents = []
            metadatas = []
            
            for chunk in self.all_chunks:
                ids.append(chunk.id)
                documents.append(chunk.content)
                metadatas.append({
                    "knowledge_type": chunk.knowledge_type.value,
                    "source": chunk.source,
                    "entities": json.dumps(chunk.entities),
                    **{k: str(v) if not isinstance(v, (str, int, float, bool)) else v 
                       for k, v in chunk.metadata.items()}
                })
            
            # Add in batches
            batch_size = 200
            for i in range(0, len(ids), batch_size):
                end_idx = min(i + batch_size, len(ids))
                collection.add(
                    ids=ids[i:end_idx],
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )
                logger.info(f"  Added batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")
            
            logger.info(f"\n✓ Successfully loaded {len(ids)} chunks to ChromaDB")
            return True
            
        except ImportError:
            logger.error("ChromaDB not installed. Run: pip install chromadb")
            return False
        except Exception as e:
            logger.error(f"Error loading to ChromaDB: {e}")
            return False
    
    def export_stats(self, filepath: str):
        """Export index statistics to JSON"""
        with open(filepath, 'w') as f:
            json.dump({
                "total_chunks": self.stats.total_chunks,
                "chunks_by_type": self.stats.chunks_by_type,
                "entities_indexed": self.stats.entities_indexed,
                "sources_processed": self.stats.sources_processed,
                "build_time_seconds": self.stats.build_time_seconds,
                "build_timestamp": datetime.now().isoformat()
            }, f, indent=2)
        logger.info(f"Exported stats to: {filepath}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point for building the knowledge index"""
    # Determine paths - all relative to ai-service folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    knowledge_base_path = os.path.join(script_dir, "knowledge_base")
    training_data_path = os.path.join(script_dir, "Train_Database")
    chroma_path = os.path.join(script_dir, "chroma_db_unified")
    
    # Build index
    builder = KnowledgeIndexBuilder(
        knowledge_base_path=knowledge_base_path,
        training_data_path=training_data_path,
        chroma_path=chroma_path
    )
    
    stats = builder.build_index()
    
    # Load to ChromaDB
    if builder.load_to_chromadb():
        # Export statistics
        stats_path = os.path.join(script_dir, "knowledge_index_stats.json")
        builder.export_stats(stats_path)
        
        print("\n" + "=" * 60)
        print("Knowledge Index Build Successful!")
        print(f"  📚 Total Chunks: {stats.total_chunks}")
        print(f"  🏷️  Entities: {stats.entities_indexed}")
        print(f"  ⏱️  Build Time: {stats.build_time_seconds:.2f}s")
        print(f"  💾 ChromaDB: {chroma_path}")
        print("=" * 60)


if __name__ == "__main__":
    main()
