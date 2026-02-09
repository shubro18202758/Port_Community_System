"""
SmartBerth AI - Unified Training Pipeline
==========================================

This module provides comprehensive training for ALL pipeline components by learning from:
1. GLOBAL Training Database (ai-service/Train_Database) - Generic port operations data
2. MUNDRA SPECIFIC Training Data (documents/Data/Mundra) - Real Mundra port operations

Components trained:
- Knowledge Index (ChromaDB)
- Graph Engine (NetworkX)
- Manager Agents (intent classification, task routing)
- RAG System (retrieval-augmented generation)
- Core AI Agent (domain understanding)

Author: SmartBerth AI Team
Date: February 2026
"""

import os
import sys
import csv
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class TrainingConfig:
    """Configuration for unified training pipeline"""
    # Base paths
    ai_service_dir: str = ""
    
    # Data sources
    global_train_path: str = ""      # ai-service/Train_Database
    mundra_train_path: str = ""      # documents/Data/Mundra
    knowledge_base_path: str = ""    # ai-service/knowledge_base
    
    # Output paths
    chroma_path: str = ""
    graph_path: str = ""
    
    # Training parameters
    chunk_size: int = 800
    chunk_overlap: int = 100
    batch_size: int = 200
    
    def __post_init__(self):
        if not self.ai_service_dir:
            self.ai_service_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Set default paths relative to ai-service
        base = self.ai_service_dir
        docs_base = os.path.join(os.path.dirname(base), "documents")
        
        self.global_train_path = self.global_train_path or os.path.join(base, "Train_Database")
        self.mundra_train_path = self.mundra_train_path or os.path.join(docs_base, "Data", "Mundra")
        self.knowledge_base_path = self.knowledge_base_path or os.path.join(base, "knowledge_base")
        self.chroma_path = self.chroma_path or os.path.join(base, "chroma_db_unified")
        self.graph_path = self.graph_path or os.path.join(base, "graph_data")


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class KnowledgeType(Enum):
    """Types of knowledge in the index"""
    DOMAIN_RULE = "domain_rule"
    DOMAIN_CONCEPT = "domain_concept"
    OPERATIONAL_DATA = "operational_data"
    ENTITY_PROFILE = "entity_profile"
    HISTORICAL = "historical"
    PROCEDURE = "procedure"
    MUNDRA_SPECIFIC = "mundra_specific"  # New type for Mundra data


@dataclass
class KnowledgeChunk:
    """A chunk of knowledge for indexing"""
    id: str
    content: str
    knowledge_type: KnowledgeType
    source: str
    data_source: str  # 'global' or 'mundra'
    metadata: Dict[str, Any] = field(default_factory=dict)
    entities: List[str] = field(default_factory=list)


@dataclass  
class GraphNode:
    """Node for the knowledge graph"""
    id: str
    node_type: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    data_source: str = "global"


@dataclass
class GraphEdge:
    """Edge for the knowledge graph"""
    source_id: str
    target_id: str
    edge_type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingStats:
    """Statistics about training"""
    total_chunks: int = 0
    global_chunks: int = 0
    mundra_chunks: int = 0
    chunks_by_type: Dict[str, int] = field(default_factory=dict)
    graph_nodes: int = 0
    graph_edges: int = 0
    entities_indexed: int = 0
    files_processed: int = 0
    build_time_seconds: float = 0.0


# ============================================================================
# MUNDRA DATA PROCESSOR
# ============================================================================

class MundraDataProcessor:
    """Process Mundra-specific training data"""
    
    # Column mappings: Mundra CSV columns → knowledge extraction
    MUNDRA_SCHEMA = {
        'VESSELS.csv': {
            'key_cols': ['vessel_id', 'vessel_name', 'imo_mmsi', 'line_operator'],
            'numeric_cols': ['loa_m', 'beam_m', 'draft_m'],
            'entity_type': 'vessel'
        },
        'BERTHS.csv': {
            'key_cols': ['berth_id', 'terminal_code', 'cargo_allowed'],
            'numeric_cols': ['max_loa_m', 'max_beam_m', 'max_draft_m', 'max_displacement_t'],
            'entity_type': 'berth'
        },
        'VESSEL_SCHEDULE.csv': {
            'key_cols': ['schedule_id', 'vessel_id', 'vessel_name', 'terminal_code', 'berth_id'],
            'time_cols': ['eta_ts', 'ata_ts', 'etd_ts', 'atd_ts'],
            'entity_type': 'vessel_call'
        },
        'WEATHER_DATA.csv': {
            'key_cols': ['ts_hour'],
            'numeric_cols': ['wind_speed_mps', 'wind_gust_mps', 'rain_mm', 'visibility_km'],
            'entity_type': 'weather'
        },
        'TIDAL_DATA.csv': {
            'key_cols': ['cycle_id', 'ts', 'tide_phase'],
            'numeric_cols': ['tide_height_m'],
            'entity_type': 'tide'
        },
        'AIS_DATA.csv': {
            'key_cols': ['schedule_id', 'vessel_id', 'ts'],
            'numeric_cols': ['lat', 'lon', 'sog_kn', 'cog_deg'],
            'entity_type': 'ais'
        },
        'RESOURCES.csv': {
            'key_cols': ['resource_id', 'terminal_code', 'berth_id', 'resource_type'],
            'numeric_cols': ['count', 'capacity_per_hr', 'availability_pct'],
            'entity_type': 'resource'
        }
    }
    
    def __init__(self, mundra_path: str):
        self.mundra_path = mundra_path
        self.chunks: List[KnowledgeChunk] = []
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
        self.chunk_counter = 0
        
    def _make_id(self, prefix: str, data: str = "") -> str:
        """Generate unique ID"""
        self.chunk_counter += 1
        if data:
            hash_val = hashlib.md5(data.encode()).hexdigest()[:8]
            return f"mundra_{prefix}_{hash_val}_{self.chunk_counter}"
        return f"mundra_{prefix}_{self.chunk_counter}"
    
    def _read_csv(self, filename: str, limit: int = None) -> List[Dict]:
        """Read CSV file"""
        filepath = os.path.join(self.mundra_path, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Mundra file not found: {filepath}")
            return []
        
        rows = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                rows.append(row)
        return rows
    
    def process_all(self) -> Tuple[List[KnowledgeChunk], List[GraphNode], List[GraphEdge]]:
        """Process all Mundra training data"""
        logger.info(f"\n{'='*60}")
        logger.info("PROCESSING MUNDRA-SPECIFIC TRAINING DATA")
        logger.info(f"Path: {self.mundra_path}")
        logger.info('='*60)
        
        self._process_vessels()
        self._process_berths()
        self._process_vessel_schedule()
        self._process_weather()
        self._process_tidal()
        self._process_resources()
        self._process_ais_patterns()  # Extract patterns, not raw data
        
        # Create Mundra port overview chunk
        self._create_mundra_overview()
        
        logger.info(f"\nMundra processing complete:")
        logger.info(f"  Chunks: {len(self.chunks)}")
        logger.info(f"  Graph Nodes: {len(self.nodes)}")
        logger.info(f"  Graph Edges: {len(self.edges)}")
        
        return self.chunks, self.nodes, self.edges
    
    def _process_vessels(self):
        """Process Mundra vessels into knowledge"""
        data = self._read_csv('VESSELS.csv')
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} Mundra vessels...")
        
        # Group by operator
        by_operator = defaultdict(list)
        for row in data:
            operator = row.get('line_operator', 'Unknown')
            by_operator[operator].append(row)
        
        # Create vessel profiles
        for vessel in data[:500]:  # Sample for knowledge chunks
            loa = float(vessel.get('loa_m', 0) or 0)
            beam = float(vessel.get('beam_m', 0) or 0)
            draft = float(vessel.get('draft_m', 0) or 0)
            
            # Determine vessel size category
            if loa >= 300:
                size_cat = "Very Large"
            elif loa >= 200:
                size_cat = "Large"
            elif loa >= 150:
                size_cat = "Medium"
            else:
                size_cat = "Small"
            
            content = f"""Mundra Port Vessel: {vessel.get('vessel_name', 'Unknown')}
ID: {vessel.get('vessel_id')} | IMO/MMSI: {vessel.get('imo_mmsi', 'N/A')}
Operator: {vessel.get('line_operator', 'Unknown')}
Dimensions: LOA {loa}m × Beam {beam}m × Draft {draft}m
Size Category: {size_cat}
Port: Mundra (INMUN) - India's largest commercial port"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id('vessel', vessel.get('vessel_id', '')),
                content=content,
                knowledge_type=KnowledgeType.MUNDRA_SPECIFIC,
                source='VESSELS.csv',
                data_source='mundra',
                metadata={
                    'vessel_id': vessel.get('vessel_id'),
                    'loa': loa,
                    'beam': beam,
                    'draft': draft,
                    'operator': vessel.get('line_operator')
                },
                entities=[vessel.get('vessel_name', ''), 'Mundra', vessel.get('line_operator', '')]
            ))
            
            # Create graph node
            self.nodes.append(GraphNode(
                id=f"mundra_vessel_{vessel.get('vessel_id')}",
                node_type='vessel',
                label=vessel.get('vessel_name', 'Unknown'),
                properties={
                    'vessel_id': vessel.get('vessel_id'),
                    'loa': loa,
                    'beam': beam,
                    'draft': draft,
                    'operator': vessel.get('line_operator'),
                    'imo_mmsi': vessel.get('imo_mmsi')
                },
                data_source='mundra'
            ))
        
        # Create operator summary
        for operator, vessels in by_operator.items():
            loas = [float(v.get('loa_m', 0) or 0) for v in vessels]
            content = f"""Mundra Port - {operator} Fleet Summary
Vessels Operating: {len(vessels)}
Average LOA: {sum(loas)/len(loas):.1f}m
LOA Range: {min(loas):.1f}m - {max(loas):.1f}m
This operator regularly calls at Mundra Port terminals."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id('operator', operator),
                content=content,
                knowledge_type=KnowledgeType.MUNDRA_SPECIFIC,
                source='VESSELS.csv',
                data_source='mundra',
                metadata={'operator': operator, 'vessel_count': len(vessels)},
                entities=[operator, 'Mundra', 'fleet']
            ))
    
    def _process_berths(self):
        """Process Mundra berths"""
        data = self._read_csv('BERTHS.csv')
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} Mundra berths...")
        
        # Group by terminal
        by_terminal = defaultdict(list)
        for row in data:
            terminal = row.get('terminal_code', 'Unknown')
            by_terminal[terminal].append(row)
        
        # Create berth profiles
        for berth in data:
            max_loa = float(berth.get('max_loa_m', 0) or 0)
            max_beam = float(berth.get('max_beam_m', 0) or 0)
            max_draft = float(berth.get('max_draft_m', 0) or 0)
            
            content = f"""Mundra Port Berth: {berth.get('berth_id')}
Terminal: {berth.get('terminal_code')}
Cargo Types: {berth.get('cargo_allowed', 'General')}
Max Dimensions: LOA {max_loa}m × Beam {max_beam}m × Draft {max_draft}m
Max Displacement: {berth.get('max_displacement_t', 'N/A')} tonnes
Equipment: {berth.get('equipment', 'Standard')}
Priority Rules: {berth.get('priority_rules', 'Standard')}
Location: Mundra Port, Gujarat, India"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id('berth', berth.get('berth_id', '')),
                content=content,
                knowledge_type=KnowledgeType.MUNDRA_SPECIFIC,
                source='BERTHS.csv',
                data_source='mundra',
                metadata={
                    'berth_id': berth.get('berth_id'),
                    'terminal': berth.get('terminal_code'),
                    'max_loa': max_loa,
                    'max_draft': max_draft,
                    'cargo_allowed': berth.get('cargo_allowed')
                },
                entities=[berth.get('berth_id', ''), berth.get('terminal_code', ''), 'Mundra']
            ))
            
            # Graph node
            self.nodes.append(GraphNode(
                id=f"mundra_berth_{berth.get('berth_id')}",
                node_type='berth',
                label=berth.get('berth_id', ''),
                properties={
                    'berth_id': berth.get('berth_id'),
                    'terminal': berth.get('terminal_code'),
                    'max_loa': max_loa,
                    'max_beam': max_beam,
                    'max_draft': max_draft,
                    'cargo_allowed': berth.get('cargo_allowed')
                },
                data_source='mundra'
            ))
        
        # Terminal summaries
        for terminal, berths in by_terminal.items():
            cargo_types = set()
            for b in berths:
                cargo_types.update(b.get('cargo_allowed', '').split(','))
            
            content = f"""Mundra Port Terminal: {terminal}
Total Berths: {len(berths)}
Cargo Types Handled: {', '.join(cargo_types)}
This terminal is part of Mundra Port, India's largest private port."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id('terminal', terminal),
                content=content,
                knowledge_type=KnowledgeType.MUNDRA_SPECIFIC,
                source='BERTHS.csv',
                data_source='mundra',
                metadata={'terminal': terminal, 'berth_count': len(berths)},
                entities=[terminal, 'Mundra', 'terminal']
            ))
            
            # Terminal node
            self.nodes.append(GraphNode(
                id=f"mundra_terminal_{terminal}",
                node_type='terminal',
                label=terminal,
                properties={'berth_count': len(berths), 'cargo_types': list(cargo_types)},
                data_source='mundra'
            ))
            
            # Terminal -> Berth edges
            for berth in berths:
                self.edges.append(GraphEdge(
                    source_id=f"mundra_terminal_{terminal}",
                    target_id=f"mundra_berth_{berth.get('berth_id')}",
                    edge_type='HAS_BERTH'
                ))
    
    def _process_vessel_schedule(self):
        """Process vessel schedule/calls"""
        data = self._read_csv('VESSEL_SCHEDULE.csv')
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} Mundra vessel schedules...")
        
        # Extract patterns from schedules
        cargo_by_terminal = defaultdict(lambda: defaultdict(int))
        vessel_call_stats = defaultdict(int)
        
        for row in data:
            terminal = row.get('terminal_code', 'Unknown')
            cargo = row.get('cargo_type', 'Unknown')
            cargo_by_terminal[terminal][cargo] += 1
            vessel_call_stats[row.get('vessel_id', '')] += 1
        
        # Create cargo flow patterns
        for terminal, cargos in cargo_by_terminal.items():
            top_cargos = sorted(cargos.items(), key=lambda x: -x[1])[:5]
            content = f"""Mundra Port {terminal} - Cargo Flow Analysis
Total Vessel Calls: {sum(cargos.values())}
Top Cargo Types:
"""
            for cargo, count in top_cargos:
                pct = count / sum(cargos.values()) * 100
                content += f"  • {cargo}: {count} calls ({pct:.1f}%)\n"
            
            content += "\nThis pattern helps in berth allocation optimization."
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id('cargo_flow', terminal),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source='VESSEL_SCHEDULE.csv',
                data_source='mundra',
                metadata={'terminal': terminal, 'total_calls': sum(cargos.values())},
                entities=[terminal, 'cargo', 'Mundra']
            ))
        
        # Sample vessel calls for graph
        for row in data[:1000]:
            vessel_id = row.get('vessel_id')
            berth_id = row.get('berth_id')
            
            if vessel_id and berth_id:
                self.nodes.append(GraphNode(
                    id=f"mundra_call_{row.get('schedule_id')}",
                    node_type='vessel_call',
                    label=f"Call-{row.get('schedule_id')}",
                    properties={
                        'vessel_id': vessel_id,
                        'berth_id': berth_id,
                        'cargo_type': row.get('cargo_type'),
                        'eta': row.get('eta_ts'),
                        'status': row.get('status', 'scheduled')
                    },
                    data_source='mundra'
                ))
                
                # Vessel -> Call edge
                self.edges.append(GraphEdge(
                    source_id=f"mundra_vessel_{vessel_id}",
                    target_id=f"mundra_call_{row.get('schedule_id')}",
                    edge_type='HAS_CALL'
                ))
                
                # Call -> Berth edge
                self.edges.append(GraphEdge(
                    source_id=f"mundra_call_{row.get('schedule_id')}",
                    target_id=f"mundra_berth_{berth_id}",
                    edge_type='ASSIGNED_TO'
                ))
    
    def _process_weather(self):
        """Process weather data patterns"""
        data = self._read_csv('WEATHER_DATA.csv')
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} Mundra weather records...")
        
        # Extract weather patterns
        wind_speeds = [float(r.get('wind_speed_mps', 0) or 0) for r in data]
        visibility = [float(r.get('visibility_km', 10) or 10) for r in data]
        storms = sum(1 for r in data if r.get('storm_flag') in ['1', 'True', 'true', True])
        
        content = f"""Mundra Port Weather Patterns Analysis
Data Period: {len(data)} hourly records

Wind Conditions:
  • Average Speed: {sum(wind_speeds)/len(wind_speeds):.1f} m/s
  • Max Speed: {max(wind_speeds):.1f} m/s
  • Min Speed: {min(wind_speeds):.1f} m/s

Visibility:
  • Average: {sum(visibility)/len(visibility):.1f} km
  • Minimum: {min(visibility):.1f} km

Storm Events: {storms} ({storms/len(data)*100:.1f}% of time)

Weather impacts:
- High winds (>15 m/s): Suspend cargo operations
- Low visibility (<1 km): Restrict vessel movements
- Storms: Emergency berth clearing protocol

This data helps predict operational windows at Mundra Port."""
        
        self.chunks.append(KnowledgeChunk(
            id=self._make_id('weather_pattern'),
            content=content,
            knowledge_type=KnowledgeType.OPERATIONAL_DATA,
            source='WEATHER_DATA.csv',
            data_source='mundra',
            metadata={
                'avg_wind': sum(wind_speeds)/len(wind_speeds),
                'storm_frequency': storms/len(data)
            },
            entities=['weather', 'Mundra', 'operations']
        ))
    
    def _process_tidal(self):
        """Process tidal data patterns"""
        data = self._read_csv('TIDAL_DATA.csv')
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} Mundra tidal records...")
        
        heights = [float(r.get('tide_height_m', 0) or 0) for r in data]
        high_tides = [h for r, h in zip(data, heights) if 'high' in r.get('tide_phase', '').lower()]
        low_tides = [h for r, h in zip(data, heights) if 'low' in r.get('tide_phase', '').lower()]
        
        content = f"""Mundra Port Tidal Patterns
Data: {len(data)} tidal observations

Tidal Range:
  • Maximum Height: {max(heights):.2f}m
  • Minimum Height: {min(heights):.2f}m
  • Tidal Range: {max(heights) - min(heights):.2f}m

High Tide Average: {sum(high_tides)/len(high_tides):.2f}m (from {len(high_tides)} observations)
Low Tide Average: {sum(low_tides)/len(low_tides):.2f}m (from {len(low_tides)} observations)

Tidal windows are critical for:
- Deep-draft vessel entry/exit
- UKC calculations
- Berth allocation timing

Mundra experiences semi-diurnal tides typical of the Gulf of Kutch."""
        
        self.chunks.append(KnowledgeChunk(
            id=self._make_id('tidal_pattern'),
            content=content,
            knowledge_type=KnowledgeType.OPERATIONAL_DATA,
            source='TIDAL_DATA.csv',
            data_source='mundra',
            metadata={
                'tidal_range': max(heights) - min(heights),
                'max_height': max(heights)
            },
            entities=['tide', 'Mundra', 'UKC', 'navigation']
        ))
    
    def _process_resources(self):
        """Process port resources"""
        data = self._read_csv('RESOURCES.csv')
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} Mundra resource records...")
        
        by_type = defaultdict(list)
        for r in data:
            by_type[r.get('resource_type', 'Unknown')].append(r)
        
        for res_type, resources in by_type.items():
            total_count = sum(int(r.get('count', 0) or 0) for r in resources)
            avg_avail = sum(float(r.get('availability_pct', 100) or 100) for r in resources) / len(resources)
            
            content = f"""Mundra Port Resource: {res_type}
Total Units: {total_count}
Distribution: {len(resources)} locations
Average Availability: {avg_avail:.1f}%

Resources are distributed across terminals for optimal coverage."""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id('resource', res_type),
                content=content,
                knowledge_type=KnowledgeType.MUNDRA_SPECIFIC,
                source='RESOURCES.csv',
                data_source='mundra',
                metadata={'resource_type': res_type, 'total': total_count},
                entities=[res_type, 'Mundra', 'resource']
            ))
    
    def _process_ais_patterns(self):
        """Extract AIS movement patterns (not raw data)"""
        data = self._read_csv('AIS_DATA.csv', limit=10000)  # Sample for pattern extraction
        if not data:
            return
        
        logger.info(f"  Extracting AIS patterns from {len(data)} records...")
        
        # Extract speed patterns
        speeds = [float(r.get('sog_kn', 0) or 0) for r in data]
        
        # Navigation status distribution
        nav_status = defaultdict(int)
        for r in data:
            nav_status[r.get('nav_status', 'Unknown')] += 1
        
        content = f"""Mundra Port Vessel Movement Patterns (AIS Analysis)
Sample Size: {len(data)} AIS positions

Speed Over Ground:
  • Average: {sum(speeds)/len(speeds):.1f} knots
  • Maximum: {max(speeds):.1f} knots
  • Stationary (<0.5 kn): {sum(1 for s in speeds if s < 0.5)} positions

Navigation Status Distribution:
"""
        for status, count in sorted(nav_status.items(), key=lambda x: -x[1])[:5]:
            content += f"  • {status}: {count} ({count/len(data)*100:.1f}%)\n"
        
        content += """
These patterns help predict:
- Vessel arrival times
- Berth availability windows
- Traffic density at port approaches"""
        
        self.chunks.append(KnowledgeChunk(
            id=self._make_id('ais_patterns'),
            content=content,
            knowledge_type=KnowledgeType.OPERATIONAL_DATA,
            source='AIS_DATA.csv',
            data_source='mundra',
            metadata={'avg_speed': sum(speeds)/len(speeds)},
            entities=['AIS', 'Mundra', 'vessel tracking', 'navigation']
        ))
    
    def _create_mundra_overview(self):
        """Create comprehensive Mundra port overview"""
        content = """Mundra Port (INMUN) - Comprehensive Overview

LOCATION & SIGNIFICANCE:
Mundra Port is India's largest private commercial port, located in the Kutch district of Gujarat.
It is operated by Adani Ports and SEZ Limited (APSEZ).

PORT CHARACTERISTICS:
• Type: Deep-water, multi-cargo port
• Latitude: 22.7°N, Longitude: 69.7°E
• Approach Channel: ~18-20m depth
• Tidal Range: ~3-4m (semi-diurnal)

TERMINALS & FACILITIES:
The port has multiple specialized terminals for:
- Container cargo
- Bulk cargo (coal, minerals)
- Liquid cargo (crude oil, chemicals)
- Break-bulk cargo

OPERATIONAL CAPABILITIES:
• 24/7 operations
• Handles vessels up to 18m draft
• Modern cargo handling equipment
• Integrated rail and road connectivity

KEY CONSTRAINTS FOR BERTH PLANNING:
1. Tidal windows for deep-draft vessels
2. Weather restrictions (monsoon season)
3. Terminal specialization by cargo type
4. Under Keel Clearance (UKC) requirements
5. Pilot and tug availability

This port data is used for training SmartBerth AI for intelligent berth allocation."""
        
        self.chunks.append(KnowledgeChunk(
            id=self._make_id('mundra_overview'),
            content=content,
            knowledge_type=KnowledgeType.DOMAIN_CONCEPT,
            source='Mundra_Overview',
            data_source='mundra',
            metadata={'port_code': 'INMUN', 'country': 'India'},
            entities=['Mundra', 'INMUN', 'India', 'Adani', 'Gujarat', 'port']
        ))
        
        # Mundra port node
        self.nodes.append(GraphNode(
            id='mundra_port_INMUN',
            node_type='port',
            label='Mundra Port',
            properties={
                'port_code': 'INMUN',
                'country': 'India',
                'state': 'Gujarat',
                'operator': 'Adani Ports',
                'type': 'Commercial'
            },
            data_source='mundra'
        ))


# ============================================================================
# GLOBAL DATA PROCESSOR (reuses existing logic)
# ============================================================================

class GlobalDataProcessor:
    """Process global training database"""
    
    def __init__(self, train_db_path: str):
        self.train_db_path = train_db_path
        self.chunks: List[KnowledgeChunk] = []
        self.nodes: List[GraphNode] = []
        self.edges: List[GraphEdge] = []
        self.chunk_counter = 0
    
    def _make_id(self, prefix: str) -> str:
        self.chunk_counter += 1
        return f"global_{prefix}_{self.chunk_counter}"
    
    def _read_csv(self, filename: str, limit: int = None) -> List[Dict]:
        filepath = os.path.join(self.train_db_path, filename)
        if not os.path.exists(filepath):
            return []
        
        rows = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                rows.append(row)
        return rows
    
    def process_all(self) -> Tuple[List[KnowledgeChunk], List[GraphNode], List[GraphEdge]]:
        """Process all global training data"""
        logger.info(f"\n{'='*60}")
        logger.info("PROCESSING GLOBAL TRAINING DATABASE")
        logger.info(f"Path: {self.train_db_path}")
        logger.info('='*60)
        
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
        self._process_weather()
        self._process_ais_patterns()
        
        logger.info(f"\nGlobal processing complete:")
        logger.info(f"  Chunks: {len(self.chunks)}")
        logger.info(f"  Graph Nodes: {len(self.nodes)}")
        logger.info(f"  Graph Edges: {len(self.edges)}")
        
        return self.chunks, self.nodes, self.edges
    
    def _process_ports(self):
        """Process port data"""
        data = self._read_csv("SmartBerth_AI_Port_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global port records...")
        
        for row in data:
            content = f"""Port Profile: {row.get('portName', 'Unknown')} ({row.get('portCode', '')})
Country: {row.get('country', 'Unknown')}, City: {row.get('city', 'Unknown')}
Location: {row.get('latitude', '')}°N, {row.get('longitude', '')}°E
Timezone: {row.get('timezone', 'UTC')}
Status: {'Active' if row.get('isActive') == 'TRUE' else 'Inactive'}"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id('port'),
                content=content,
                knowledge_type=KnowledgeType.ENTITY_PROFILE,
                source='SmartBerth_AI_Port_Parameters_Training_Data.csv',
                data_source='global',
                metadata={'portCode': row.get('portCode'), 'country': row.get('country')},
                entities=[row.get('portName', ''), row.get('portCode', '')]
            ))
            
            self.nodes.append(GraphNode(
                id=f"global_port_{row.get('portId')}",
                node_type='port',
                label=row.get('portName', ''),
                properties=dict(row),
                data_source='global'
            ))
    
    def _process_terminals(self):
        """Process terminal data"""
        data = self._read_csv("SmartBerth_AI_Terminal_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global terminal records...")
        
        by_type = defaultdict(list)
        for row in data:
            by_type[row.get('terminalType', 'Unknown')].append(row)
        
        for term_type, terminals in by_type.items():
            content = f"""Terminal Type: {term_type}
Count: {len(terminals)} terminals in SmartBerth network"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id(f'terminal_{term_type}'),
                content=content,
                knowledge_type=KnowledgeType.ENTITY_PROFILE,
                source='SmartBerth_AI_Terminal_Parameters_Training_Data.csv',
                data_source='global',
                metadata={'terminalType': term_type, 'count': len(terminals)},
                entities=[term_type, 'terminal']
            ))
        
        for row in data:
            self.nodes.append(GraphNode(
                id=f"global_terminal_{row.get('terminalId')}",
                node_type='terminal',
                label=row.get('terminalName', ''),
                properties=dict(row),
                data_source='global'
            ))
            
            # Terminal -> Port edge
            self.edges.append(GraphEdge(
                source_id=f"global_terminal_{row.get('terminalId')}",
                target_id=f"global_port_{row.get('portId')}",
                edge_type='BELONGS_TO'
            ))
    
    def _process_berths(self):
        """Process berth data"""
        data = self._read_csv("SmartBerth_AI_Berth_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global berth records...")
        
        by_type = defaultdict(list)
        for row in data:
            by_type[row.get('berthType', 'General')].append(row)
        
        for berth_type, berths in by_type.items():
            lengths = [float(b.get('length', 0) or 0) for b in berths]
            depths = [float(b.get('depth', 0) or 0) for b in berths]
            
            if not lengths:
                continue
            
            content = f"""Berth Type: {berth_type}
Total: {len(berths)} berths
Avg Length: {sum(lengths)/len(lengths):.1f}m
Avg Depth: {sum(depths)/len(depths):.1f}m"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id(f'berth_{berth_type}'),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source='SmartBerth_AI_Berth_Parameters_Training_Data.csv',
                data_source='global',
                metadata={'berthType': berth_type, 'count': len(berths)},
                entities=[berth_type, 'berth']
            ))
        
        for row in data:
            self.nodes.append(GraphNode(
                id=f"global_berth_{row.get('berthId')}",
                node_type='berth',
                label=row.get('berthName', ''),
                properties=dict(row),
                data_source='global'
            ))
            
            self.edges.append(GraphEdge(
                source_id=f"global_berth_{row.get('berthId')}",
                target_id=f"global_terminal_{row.get('terminalId')}",
                edge_type='PART_OF'
            ))
    
    def _process_vessels(self):
        """Process vessel data"""
        data = self._read_csv("SmartBerth_AI_Vessel_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global vessel records...")
        
        by_type = defaultdict(list)
        for row in data:
            by_type[row.get('vessel_type', 'Unknown')].append(row)
        
        for vessel_type, vessels in by_type.items():
            loas = [float(v.get('loa', 0) or 0) for v in vessels]
            if not loas:
                continue
            
            content = f"""Vessel Type: {vessel_type}
Fleet Size: {len(vessels)}
LOA Range: {min(loas):.1f}m - {max(loas):.1f}m
Average LOA: {sum(loas)/len(loas):.1f}m"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id(f'vessel_type_{vessel_type}'),
                content=content,
                knowledge_type=KnowledgeType.ENTITY_PROFILE,
                source='SmartBerth_AI_Vessel_Parameters_Training_Data.csv',
                data_source='global',
                metadata={'vesselType': vessel_type, 'count': len(vessels)},
                entities=[vessel_type, 'vessel']
            ))
        
        for row in data[:3000]:  # Limit for graph
            self.nodes.append(GraphNode(
                id=f"global_vessel_{row.get('vessel_id')}",
                node_type='vessel',
                label=row.get('vessel_name', ''),
                properties=dict(row),
                data_source='global'
            ))
    
    def _process_vessel_calls(self):
        """Process vessel call assignments"""
        data = self._read_csv("SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global vessel call records...")
        
        # Extract patterns
        by_port = defaultdict(int)
        by_status = defaultdict(int)
        
        for row in data:
            by_port[row.get('portCode', 'Unknown')] += 1
            by_status[row.get('status', 'Unknown')] += 1
        
        content = f"""Vessel Call Assignment Summary
Total Calls: {len(data)}
Ports: {len(by_port)}
Top Ports: {', '.join(f"{k}({v})" for k, v in sorted(by_port.items(), key=lambda x:-x[1])[:5])}"""
        
        self.chunks.append(KnowledgeChunk(
            id=self._make_id('vessel_calls_summary'),
            content=content,
            knowledge_type=KnowledgeType.OPERATIONAL_DATA,
            source='SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv',
            data_source='global',
            metadata={'total_calls': len(data)},
            entities=['vessel call', 'berth assignment']
        ))
        
        for row in data[:5000]:
            self.nodes.append(GraphNode(
                id=f"global_call_{row.get('callId')}",
                node_type='vessel_call',
                label=f"Call-{row.get('callId')}",
                properties=dict(row),
                data_source='global'
            ))
    
    def _process_pilots(self):
        """Process pilot data"""
        data = self._read_csv("SmartBerth_AI_Pilotage_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global pilot records...")
        
        by_class = defaultdict(list)
        for row in data:
            by_class[row.get('pilotClass', 'Unknown')].append(row)
        
        for pilot_class, pilots in by_class.items():
            content = f"""Pilot Class: {pilot_class}
Total Pilots: {len(pilots)}
Certification Levels: {set(p.get('certificationLevel') for p in pilots)}"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id(f'pilot_class_{pilot_class}'),
                content=content,
                knowledge_type=KnowledgeType.ENTITY_PROFILE,
                source='SmartBerth_AI_Pilotage_Parameters_Training_Data.csv',
                data_source='global',
                metadata={'pilotClass': pilot_class, 'count': len(pilots)},
                entities=[pilot_class, 'pilot']
            ))
        
        for row in data:
            self.nodes.append(GraphNode(
                id=f"global_pilot_{row.get('pilotId')}",
                node_type='pilot',
                label=row.get('pilotName', ''),
                properties=dict(row),
                data_source='global'
            ))
    
    def _process_tugboats(self):
        """Process tugboat data"""
        data = self._read_csv("SmartBerth_AI_Tugboat_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global tugboat records...")
        
        by_type = defaultdict(list)
        for row in data:
            by_type[row.get('tugType', 'Unknown')].append(row)
        
        for tug_type, tugs in by_type.items():
            bollard_pulls = [float(t.get('bollardPull', 0) or 0) for t in tugs]
            
            content = f"""Tugboat Type: {tug_type}
Fleet: {len(tugs)} tugs
Bollard Pull Range: {min(bollard_pulls):.0f}t - {max(bollard_pulls):.0f}t"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id(f'tug_type_{tug_type}'),
                content=content,
                knowledge_type=KnowledgeType.ENTITY_PROFILE,
                source='SmartBerth_AI_Tugboat_Parameters_Training_Data.csv',
                data_source='global',
                metadata={'tugType': tug_type, 'count': len(tugs)},
                entities=[tug_type, 'tugboat']
            ))
        
        for row in data:
            self.nodes.append(GraphNode(
                id=f"global_tug_{row.get('tugId')}",
                node_type='tugboat',
                label=row.get('tugName', ''),
                properties=dict(row),
                data_source='global'
            ))
    
    def _process_channels(self):
        """Process channel data"""
        data = self._read_csv("SmartBerth_AI_Channel_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global channel records...")
        
        for row in data:
            content = f"""Channel: {row.get('channelName', 'Unknown')}
Length: {row.get('channelLength', 'N/A')}m
Width: {row.get('channelWidth', 'N/A')}m
Depth: {row.get('channelDepth', 'N/A')}m
Traffic: {row.get('oneWayOrTwoWay', 'N/A')}
Max LOA: {row.get('maxVesselLOA', 'N/A')}m"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id('channel'),
                content=content,
                knowledge_type=KnowledgeType.ENTITY_PROFILE,
                source='SmartBerth_AI_Channel_Parameters_Training_Data.csv',
                data_source='global',
                metadata={'channelId': row.get('channelId')},
                entities=[row.get('channelName', ''), 'channel', 'navigation']
            ))
            
            self.nodes.append(GraphNode(
                id=f"global_channel_{row.get('channelId')}",
                node_type='channel',
                label=row.get('channelName', ''),
                properties=dict(row),
                data_source='global'
            ))
    
    def _process_anchorages(self):
        """Process anchorage data"""
        data = self._read_csv("SmartBerth_AI_Anchorage_Parameters_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global anchorage records...")
        
        for row in data:
            content = f"""Anchorage: {row.get('anchorageName', 'Unknown')}
Type: {row.get('anchorageType', 'N/A')}
Depth: {row.get('depth', 'N/A')}m
Max Vessels: {row.get('maxVessels', 'N/A')}
Max LOA: {row.get('maxVesselLOA', 'N/A')}m"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id('anchorage'),
                content=content,
                knowledge_type=KnowledgeType.ENTITY_PROFILE,
                source='SmartBerth_AI_Anchorage_Parameters_Training_Data.csv',
                data_source='global',
                metadata={'anchorageId': row.get('anchorageId')},
                entities=[row.get('anchorageName', ''), 'anchorage']
            ))
            
            self.nodes.append(GraphNode(
                id=f"global_anchorage_{row.get('anchorageId')}",
                node_type='anchorage',
                label=row.get('anchorageName', ''),
                properties=dict(row),
                data_source='global'
            ))
    
    def _process_ukc(self):
        """Process UKC training data"""
        data = self._read_csv("SmartBerth_AI_UKC_Training_Data.csv")
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global UKC records...")
        
        # Extract UKC patterns by vessel type
        by_vessel_type = defaultdict(list)
        for row in data:
            by_vessel_type[row.get('vesselType', 'Unknown')].append(row)
        
        for vessel_type, records in by_vessel_type.items():
            ukc_values = [float(r.get('requiredUKC', 0) or 0) for r in records]
            if not ukc_values:
                continue
            
            content = f"""UKC Requirements: {vessel_type}
Records: {len(records)}
Average Required UKC: {sum(ukc_values)/len(ukc_values):.2f}m
Range: {min(ukc_values):.2f}m - {max(ukc_values):.2f}m"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id(f'ukc_{vessel_type}'),
                content=content,
                knowledge_type=KnowledgeType.DOMAIN_RULE,
                source='SmartBerth_AI_UKC_Training_Data.csv',
                data_source='global',
                metadata={'vesselType': vessel_type},
                entities=['UKC', vessel_type, 'safety']
            ))
    
    def _process_weather(self):
        """Process weather data"""
        data = self._read_csv("SmartBerth_AI_Weather_Parameters_Training_Data.csv", limit=10000)
        if not data:
            return
        
        logger.info(f"  Processing {len(data)} global weather records...")
        
        by_port = defaultdict(list)
        for row in data:
            by_port[row.get('portCode', 'Unknown')].append(row)
        
        for port, records in list(by_port.items())[:50]:  # Limit ports
            wind_speeds = [float(r.get('windSpeed', 0) or 0) for r in records]
            
            content = f"""Weather Profile: {port}
Records: {len(records)}
Avg Wind: {sum(wind_speeds)/len(wind_speeds):.1f} knots
Max Wind: {max(wind_speeds):.1f} knots"""
            
            self.chunks.append(KnowledgeChunk(
                id=self._make_id(f'weather_{port}'),
                content=content,
                knowledge_type=KnowledgeType.OPERATIONAL_DATA,
                source='SmartBerth_AI_Weather_Parameters_Training_Data.csv',
                data_source='global',
                metadata={'portCode': port},
                entities=[port, 'weather']
            ))
    
    def _process_ais_patterns(self):
        """Extract AIS patterns"""
        data = self._read_csv("SmartBerth_AI_AIS_Parameters_Training_Data.csv", limit=10000)
        if not data:
            return
        
        logger.info(f"  Extracting AIS patterns from {len(data)} records...")
        
        by_status = defaultdict(int)
        for row in data:
            by_status[row.get('navigationStatus', 'Unknown')] += 1
        
        content = f"""Global AIS Navigation Status Distribution
Sample: {len(data)} positions
"""
        for status, count in sorted(by_status.items(), key=lambda x: -x[1])[:5]:
            content += f"  • {status}: {count} ({count/len(data)*100:.1f}%)\n"
        
        self.chunks.append(KnowledgeChunk(
            id=self._make_id('ais_patterns'),
            content=content,
            knowledge_type=KnowledgeType.OPERATIONAL_DATA,
            source='SmartBerth_AI_AIS_Parameters_Training_Data.csv',
            data_source='global',
            metadata={'sample_size': len(data)},
            entities=['AIS', 'navigation', 'vessel tracking']
        ))


# ============================================================================
# KNOWLEDGE BASE PROCESSOR
# ============================================================================

class KnowledgeBaseProcessor:
    """Process markdown knowledge base documents"""
    
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        self.chunks: List[KnowledgeChunk] = []
        self.chunk_counter = 0
    
    def _make_id(self, prefix: str) -> str:
        self.chunk_counter += 1
        return f"kb_{prefix}_{self.chunk_counter}"
    
    def process_all(self) -> List[KnowledgeChunk]:
        """Process all knowledge base documents"""
        if not os.path.exists(self.kb_path):
            logger.warning(f"Knowledge base path not found: {self.kb_path}")
            return []
        
        logger.info(f"\n{'='*60}")
        logger.info("PROCESSING KNOWLEDGE BASE DOCUMENTS")
        logger.info(f"Path: {self.kb_path}")
        logger.info('='*60)
        
        for filename in os.listdir(self.kb_path):
            if filename.endswith('.md'):
                self._process_markdown(filename)
        
        logger.info(f"  Generated {len(self.chunks)} chunks from knowledge base")
        return self.chunks
    
    def _process_markdown(self, filename: str):
        """Process a markdown file"""
        filepath = os.path.join(self.kb_path, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine knowledge type
        if 'constraint' in filename.lower():
            k_type = KnowledgeType.DOMAIN_RULE
        elif 'procedure' in filename.lower():
            k_type = KnowledgeType.PROCEDURE
        else:
            k_type = KnowledgeType.DOMAIN_CONCEPT
        
        # Split into sections and chunk
        sections = self._extract_sections(content)
        
        for section in sections:
            if len(section['content'].strip()) < 50:
                continue
            
            chunks = self._chunk_content(section['content'], 800, 100)
            
            for i, chunk in enumerate(chunks):
                self.chunks.append(KnowledgeChunk(
                    id=self._make_id(filename.replace('.md', '')),
                    content=chunk,
                    knowledge_type=k_type,
                    source=filename,
                    data_source='knowledge_base',
                    metadata={
                        'section': section['header'],
                        'chunk_index': i
                    },
                    entities=self._extract_entities(chunk)
                ))
    
    def _extract_sections(self, content: str) -> List[Dict]:
        """Extract sections from markdown"""
        sections = []
        current = {"header": "Introduction", "content": ""}
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current["content"].strip():
                    sections.append(current)
                current = {"header": line[3:].strip(), "content": ""}
            elif line.startswith('### '):
                if current["content"].strip():
                    sections.append(current)
                current = {"header": line[4:].strip(), "content": ""}
            elif line.startswith('# '):
                if current["content"].strip():
                    sections.append(current)
                current = {"header": line[2:].strip(), "content": ""}
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
        """Extract entities from text"""
        entities = []
        keywords = ['berth', 'vessel', 'ukc', 'pilot', 'tug', 'weather', 
                   'constraint', 'allocation', 'eta', 'tide', 'channel']
        
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                entities.append(kw)
        
        return entities


# ============================================================================
# UNIFIED TRAINING PIPELINE
# ============================================================================

class UnifiedTrainingPipeline:
    """Main pipeline that orchestrates all training"""
    
    def __init__(self, config: TrainingConfig = None):
        self.config = config or TrainingConfig()
        self.all_chunks: List[KnowledgeChunk] = []
        self.all_nodes: List[GraphNode] = []
        self.all_edges: List[GraphEdge] = []
        self.stats = TrainingStats()
    
    def run(self) -> TrainingStats:
        """Execute the complete training pipeline"""
        start_time = datetime.now()
        
        print("\n" + "="*70)
        print("  SMARTBERTH AI - UNIFIED TRAINING PIPELINE")
        print("  Training on Global + Mundra-Specific Data")
        print("="*70)
        
        # Verify paths
        self._verify_paths()
        
        # Process all data sources
        self._process_knowledge_base()
        self._process_global_data()
        self._process_mundra_data()
        
        # Load to ChromaDB
        self._load_to_chromadb()
        
        # Build graph
        self._build_graph()
        
        # Calculate final stats
        self.stats.total_chunks = len(self.all_chunks)
        self.stats.global_chunks = sum(1 for c in self.all_chunks if c.data_source == 'global')
        self.stats.mundra_chunks = sum(1 for c in self.all_chunks if c.data_source == 'mundra')
        self.stats.graph_nodes = len(self.all_nodes)
        self.stats.graph_edges = len(self.all_edges)
        
        # Count by type
        for chunk in self.all_chunks:
            kt = chunk.knowledge_type.value
            self.stats.chunks_by_type[kt] = self.stats.chunks_by_type.get(kt, 0) + 1
        
        # Extract unique entities
        all_entities = set()
        for chunk in self.all_chunks:
            all_entities.update(chunk.entities)
        self.stats.entities_indexed = len(all_entities)
        
        self.stats.build_time_seconds = (datetime.now() - start_time).total_seconds()
        
        # Print summary
        self._print_summary()
        
        # Export stats
        self._export_stats()
        
        return self.stats
    
    def _verify_paths(self):
        """Verify all data paths exist"""
        logger.info("\nVerifying data paths...")
        
        paths = [
            ("Global Train DB", self.config.global_train_path),
            ("Mundra Train Data", self.config.mundra_train_path),
            ("Knowledge Base", self.config.knowledge_base_path)
        ]
        
        for name, path in paths:
            if os.path.exists(path):
                files = len([f for f in os.listdir(path) if f.endswith(('.csv', '.md'))])
                logger.info(f"  ✓ {name}: {path} ({files} files)")
            else:
                logger.warning(f"  ✗ {name}: {path} (NOT FOUND)")
    
    def _process_knowledge_base(self):
        """Process knowledge base documents"""
        processor = KnowledgeBaseProcessor(self.config.knowledge_base_path)
        chunks = processor.process_all()
        self.all_chunks.extend(chunks)
        self.stats.files_processed += processor.chunk_counter
    
    def _process_global_data(self):
        """Process global training database"""
        processor = GlobalDataProcessor(self.config.global_train_path)
        chunks, nodes, edges = processor.process_all()
        self.all_chunks.extend(chunks)
        self.all_nodes.extend(nodes)
        self.all_edges.extend(edges)
    
    def _process_mundra_data(self):
        """Process Mundra-specific training data"""
        processor = MundraDataProcessor(self.config.mundra_train_path)
        chunks, nodes, edges = processor.process_all()
        self.all_chunks.extend(chunks)
        self.all_nodes.extend(nodes)
        self.all_edges.extend(edges)
    
    def _load_to_chromadb(self):
        """Load all chunks to ChromaDB"""
        try:
            import chromadb
            
            logger.info(f"\n{'='*60}")
            logger.info("LOADING TO CHROMADB")
            logger.info('='*60)
            
            os.makedirs(self.config.chroma_path, exist_ok=True)
            client = chromadb.PersistentClient(path=self.config.chroma_path)
            
            # Delete existing collection
            try:
                client.delete_collection("smartberth_unified")
                logger.info("  Deleted existing collection")
            except:
                pass
            
            # Create new collection
            collection = client.create_collection(
                name="smartberth_unified",
                metadata={"description": "SmartBerth Unified Knowledge Index (Global + Mundra)"}
            )
            
            # Prepare batch data
            ids = []
            documents = []
            metadatas = []
            
            for chunk in self.all_chunks:
                ids.append(chunk.id)
                documents.append(chunk.content)
                metadatas.append({
                    "knowledge_type": chunk.knowledge_type.value,
                    "source": chunk.source,
                    "data_source": chunk.data_source,
                    "entities": json.dumps(chunk.entities),
                    **{k: str(v) if not isinstance(v, (str, int, float, bool)) else v 
                       for k, v in chunk.metadata.items()}
                })
            
            # Add in batches
            batch_size = self.config.batch_size
            for i in range(0, len(ids), batch_size):
                end_idx = min(i + batch_size, len(ids))
                collection.add(
                    ids=ids[i:end_idx],
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )
                logger.info(f"  Added batch {i//batch_size + 1}/{(len(ids)-1)//batch_size + 1}")
            
            logger.info(f"  ✓ Loaded {len(ids)} chunks to ChromaDB")
            
        except ImportError:
            logger.error("ChromaDB not installed")
        except Exception as e:
            logger.error(f"Error loading to ChromaDB: {e}")
    
    def _build_graph(self):
        """Build knowledge graph with NetworkX"""
        try:
            import networkx as nx
            
            logger.info(f"\n{'='*60}")
            logger.info("BUILDING KNOWLEDGE GRAPH")
            logger.info('='*60)
            
            G = nx.DiGraph()
            
            # Add nodes
            for node in self.all_nodes:
                G.add_node(
                    node.id,
                    node_type=node.node_type,
                    label=node.label,
                    data_source=node.data_source,
                    **node.properties
                )
            
            # Add edges
            valid_edges = 0
            for edge in self.all_edges:
                if G.has_node(edge.source_id) and G.has_node(edge.target_id):
                    G.add_edge(
                        edge.source_id,
                        edge.target_id,
                        edge_type=edge.edge_type,
                        **edge.properties
                    )
                    valid_edges += 1
            
            logger.info(f"  Nodes: {G.number_of_nodes()}")
            logger.info(f"  Edges: {valid_edges}")
            
            # Save graph
            os.makedirs(self.config.graph_path, exist_ok=True)
            graph_file = os.path.join(self.config.graph_path, "knowledge_graph.gml")
            
            # Convert properties to strings for GML format
            for node in G.nodes():
                for key, value in list(G.nodes[node].items()):
                    if isinstance(value, (dict, list)):
                        G.nodes[node][key] = json.dumps(value, default=str)
                    elif value is None:
                        G.nodes[node][key] = ""
            
            for u, v in G.edges():
                for key, value in list(G.edges[u, v].items()):
                    if isinstance(value, (dict, list)):
                        G.edges[u, v][key] = json.dumps(value, default=str)
                    elif value is None:
                        G.edges[u, v][key] = ""
            
            nx.write_gml(G, graph_file)
            logger.info(f"  ✓ Saved graph to {graph_file}")
            
            # Save as JSON for debugging
            json_file = os.path.join(self.config.graph_path, "knowledge_graph.json")
            graph_data = {
                "nodes": [{"id": n, **G.nodes[n]} for n in list(G.nodes())[:1000]],  # Sample
                "edges": [{"source": u, "target": v, **G.edges[u, v]} for u, v in list(G.edges())[:2000]]
            }
            with open(json_file, 'w') as f:
                json.dump(graph_data, f, indent=2, default=str)
            logger.info(f"  ✓ Saved graph sample to {json_file}")
            
        except ImportError:
            logger.warning("NetworkX not installed - skipping graph build")
        except Exception as e:
            logger.error(f"Error building graph: {e}")
    
    def _print_summary(self):
        """Print training summary"""
        print("\n" + "="*70)
        print("  TRAINING COMPLETE!")
        print("="*70)
        print(f"""
  📊 KNOWLEDGE INDEX:
     Total Chunks: {self.stats.total_chunks}
     ├── Global Data: {self.stats.global_chunks} chunks
     └── Mundra Data: {self.stats.mundra_chunks} chunks
  
  📈 CHUNKS BY TYPE:""")
        for kt, count in sorted(self.stats.chunks_by_type.items(), key=lambda x: -x[1]):
            print(f"     • {kt}: {count}")
        
        print(f"""
  🔗 KNOWLEDGE GRAPH:
     Nodes: {self.stats.graph_nodes}
     Edges: {self.stats.graph_edges}
  
  🏷️  Entities Indexed: {self.stats.entities_indexed}
  ⏱️  Build Time: {self.stats.build_time_seconds:.2f}s
  
  💾 OUTPUT:
     ChromaDB: {self.config.chroma_path}
     Graph: {self.config.graph_path}
""")
        print("="*70)
    
    def _export_stats(self):
        """Export training statistics"""
        stats_file = os.path.join(self.config.ai_service_dir, "training_stats.json")
        with open(stats_file, 'w') as f:
            json.dump({
                "total_chunks": self.stats.total_chunks,
                "global_chunks": self.stats.global_chunks,
                "mundra_chunks": self.stats.mundra_chunks,
                "chunks_by_type": self.stats.chunks_by_type,
                "graph_nodes": self.stats.graph_nodes,
                "graph_edges": self.stats.graph_edges,
                "entities_indexed": self.stats.entities_indexed,
                "build_time_seconds": self.stats.build_time_seconds,
                "build_timestamp": datetime.now().isoformat(),
                "data_sources": {
                    "global": self.config.global_train_path,
                    "mundra": self.config.mundra_train_path
                }
            }, f, indent=2)
        logger.info(f"Exported stats to: {stats_file}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    config = TrainingConfig()
    pipeline = UnifiedTrainingPipeline(config)
    stats = pipeline.run()
    
    print("\n✅ Unified training pipeline completed successfully!")
    print(f"   All components now trained on {stats.total_chunks} knowledge chunks")
    print(f"   (Global: {stats.global_chunks} + Mundra: {stats.mundra_chunks})")


if __name__ == "__main__":
    main()
