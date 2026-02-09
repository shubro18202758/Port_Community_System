"""
SmartBerth AI - In-Memory Knowledge Graph
==========================================

A NetworkX-based graph engine that loads all training data entities
and relationships without requiring an external database like Neo4j.

This provides 100% availability for graph queries.

Graph Structure:
================
PORT --[HAS_TERMINAL]--> TERMINAL --[HAS_BERTH]--> BERTH
PORT --[HAS_CHANNEL]--> CHANNEL
PORT --[HAS_ANCHORAGE]--> ANCHORAGE
PORT --[HAS_PILOT]--> PILOT
PORT --[HAS_TUG]--> TUGBOAT

VESSEL --[IS_TYPE]--> VESSEL_TYPE
VESSEL --[MADE_CALL]--> VESSEL_CALL
VESSEL_CALL --[AT_BERTH]--> BERTH
VESSEL_CALL --[AT_PORT]--> PORT

BERTH --[SUPPORTS_TYPE]--> VESSEL_TYPE
TERMINAL --[OF_TYPE]--> TERMINAL_TYPE
"""

import os
import csv
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

logger = logging.getLogger(__name__)


# ============================================================================
# NODE AND EDGE TYPES
# ============================================================================

class NodeType(str, Enum):
    """Types of nodes in the knowledge graph"""
    PORT = "PORT"
    TERMINAL = "TERMINAL"
    BERTH = "BERTH"
    CHANNEL = "CHANNEL"
    ANCHORAGE = "ANCHORAGE"
    
    VESSEL = "VESSEL"
    VESSEL_TYPE = "VESSEL_TYPE"
    VESSEL_CALL = "VESSEL_CALL"
    
    PILOT = "PILOT"
    TUGBOAT = "TUGBOAT"
    
    WEATHER_RECORD = "WEATHER_RECORD"
    UKC_RECORD = "UKC_RECORD"


class EdgeType(str, Enum):
    """Types of relationships in the knowledge graph"""
    # Port hierarchy
    HAS_TERMINAL = "HAS_TERMINAL"
    HAS_BERTH = "HAS_BERTH"
    HAS_CHANNEL = "HAS_CHANNEL"
    HAS_ANCHORAGE = "HAS_ANCHORAGE"
    HAS_PILOT = "HAS_PILOT"
    HAS_TUG = "HAS_TUG"
    
    # Vessel relationships
    IS_TYPE = "IS_TYPE"
    MADE_CALL = "MADE_CALL"
    AT_BERTH = "AT_BERTH"
    AT_PORT = "AT_PORT"
    AT_TERMINAL = "AT_TERMINAL"
    
    # Capability relationships
    SUPPORTS_TYPE = "SUPPORTS_TYPE"
    TERMINAL_TYPE = "OF_TYPE"
    
    # Resource relationships
    ASSIGNED_TO = "ASSIGNED_TO"
    OPERATED_BY = "OPERATED_BY"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class GraphStats:
    """Statistics about the knowledge graph"""
    total_nodes: int = 0
    total_edges: int = 0
    nodes_by_type: Dict[str, int] = field(default_factory=dict)
    edges_by_type: Dict[str, int] = field(default_factory=dict)
    ports: int = 0
    terminals: int = 0
    berths: int = 0
    vessels: int = 0
    vessel_calls: int = 0
    pilots: int = 0
    tugboats: int = 0


# ============================================================================
# IN-MEMORY KNOWLEDGE GRAPH
# ============================================================================

class InMemoryKnowledgeGraph:
    """
    In-memory knowledge graph using NetworkX.
    
    Loads all training data and builds a queryable graph structure
    without requiring Neo4j or any external database.
    """
    
    def __init__(self, training_data_dir: str = None):
        """
        Initialize the in-memory knowledge graph.
        
        Args:
            training_data_dir: Path to directory containing training CSVs
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX is required. Install with: pip install networkx")
        
        self.graph = nx.MultiDiGraph()  # Directed graph with multiple edges
        self._loaded = False
        self._stats = GraphStats()
        
        # Find training data directory
        if training_data_dir:
            self.training_dir = training_data_dir
        else:
            # Default locations
            script_dir = os.path.dirname(os.path.abspath(__file__))
            possible_paths = [
                os.path.join(script_dir, "..", "..", "Train_Database"),
                os.path.join(script_dir, "..", "Train_Database"),
                os.path.join(script_dir, "Train_Database"),
            ]
            
            self.training_dir = None
            for path in possible_paths:
                if os.path.exists(path):
                    self.training_dir = os.path.abspath(path)
                    break
        
        # Index structures for fast lookups
        self._port_index: Dict[str, str] = {}  # port_code -> node_id
        self._terminal_index: Dict[str, str] = {}
        self._berth_index: Dict[str, str] = {}
        self._vessel_index: Dict[str, str] = {}  # imo_number -> node_id
        self._vessel_name_index: Dict[str, str] = {}  # name -> node_id
        
        logger.info(f"InMemoryKnowledgeGraph initialized (training_dir={self.training_dir})")
    
    def load(self) -> bool:
        """
        Load all training data into the graph.
        
        Returns:
            True if loading succeeded
        """
        if self._loaded:
            logger.info("Graph already loaded")
            return True
        
        if not self.training_dir or not os.path.exists(self.training_dir):
            logger.warning(f"Training data directory not found: {self.training_dir}")
            return False
        
        logger.info(f"Loading training data from: {self.training_dir}")
        
        try:
            # Load in order of dependencies
            self._load_ports()
            self._load_terminals()
            self._load_berths()
            self._load_channels()
            self._load_anchorages()
            self._load_vessels()
            self._load_pilots()
            self._load_tugboats()
            self._load_vessel_calls()
            self._load_ukc_data()
            self._load_weather_data()
            
            # Update statistics
            self._update_stats()
            
            self._loaded = True
            logger.info(f"✓ Graph loaded: {self._stats.total_nodes} nodes, {self._stats.total_edges} edges")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return False
    
    def _read_csv(self, filename: str) -> List[Dict]:
        """Read a CSV file and return list of dicts"""
        filepath = os.path.join(self.training_dir, filename)
        
        if not os.path.exists(filepath):
            logger.debug(f"CSV not found: {filename}")
            return []
        
        rows = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean up keys and values
                    cleaned = {k.strip(): v.strip() if v else '' for k, v in row.items()}
                    rows.append(cleaned)
        except Exception as e:
            logger.warning(f"Error reading {filename}: {e}")
        
        return rows
    
    def _add_node(self, node_id: str, node_type: NodeType, **properties) -> str:
        """Add a node to the graph"""
        self.graph.add_node(
            node_id,
            node_type=node_type.value,
            **properties
        )
        return node_id
    
    def _add_edge(self, source: str, target: str, edge_type: EdgeType, **properties):
        """Add an edge to the graph"""
        if source in self.graph and target in self.graph:
            self.graph.add_edge(
                source, target,
                edge_type=edge_type.value,
                **properties
            )
    
    # =========================================================================
    # DATA LOADERS
    # =========================================================================
    
    def _load_ports(self):
        """Load port data"""
        rows = self._read_csv("SmartBerth_AI_Port_Parameters_Training_Data.csv")
        
        for row in rows:
            port_code = row.get('port_code') or row.get('portCode') or row.get('PORT_CODE', '')
            port_id = row.get('port_id') or row.get('portId') or row.get('PORT_ID', '')
            if not port_code:
                continue
            
            node_id = f"PORT_{port_code}"
            self._add_node(
                node_id,
                NodeType.PORT,
                port_code=port_code,
                port_id=port_id,
                port_name=row.get('port_name') or row.get('portName', ''),
                country=row.get('country', ''),
                latitude=self._safe_float(row.get('latitude', 0)),
                longitude=self._safe_float(row.get('longitude', 0)),
                timezone=row.get('timezone', ''),
                max_draft=self._safe_float(row.get('max_draft') or row.get('maxDraft', 0)),
                total_berths=self._safe_int(row.get('total_berths') or row.get('totalBerths', 0)),
            )
            self._port_index[port_code] = node_id
            # Also index by numeric port_id for relationship linking
            if port_id:
                self._port_index[str(port_id)] = node_id
        
        logger.info(f"  Loaded {len([k for k in self._port_index if not k.isdigit()])} ports")
    
    def _load_terminals(self):
        """Load terminal data"""
        rows = self._read_csv("SmartBerth_AI_Terminal_Parameters_Training_Data.csv")
        
        for row in rows:
            terminal_id = row.get('terminal_id') or row.get('terminalId') or row.get('TERMINAL_ID', '')
            if not terminal_id:
                continue
            
            node_id = f"TERMINAL_{terminal_id}"
            # Try port_code first, then fall back to numeric portId
            port_code = row.get('port_code') or row.get('portCode', '')
            port_id = row.get('port_id') or row.get('portId', '')
            
            self._add_node(
                node_id,
                NodeType.TERMINAL,
                terminal_id=terminal_id,
                terminal_name=row.get('terminal_name') or row.get('terminalName', ''),
                terminal_type=row.get('terminal_type') or row.get('terminalType', ''),
                port_code=port_code,
                port_id=port_id,
                operator_name=row.get('operator_name') or row.get('operatorName', ''),
                total_berths=self._safe_int(row.get('total_berths') or row.get('totalBerths', 0)),
                max_loa=self._safe_float(row.get('max_loa') or row.get('maxLOA', 0)),
                max_draft=self._safe_float(row.get('max_draft') or row.get('maxDraft', 0)),
            )
            self._terminal_index[terminal_id] = node_id
            # Also index by string terminal_id
            self._terminal_index[str(terminal_id)] = node_id
            
            # Create edge: PORT -> TERMINAL
            # Try port_code first, then numeric port_id
            port_node_id = None
            if port_code and port_code in self._port_index:
                port_node_id = self._port_index[port_code]
            elif port_id and str(port_id) in self._port_index:
                port_node_id = self._port_index[str(port_id)]
            
            if port_node_id:
                self._add_edge(
                    port_node_id,
                    node_id,
                    EdgeType.HAS_TERMINAL
                )
        
        logger.info(f"  Loaded {len([k for k in self._terminal_index if not k.isdigit()])} terminals")
    
    def _load_berths(self):
        """Load berth data"""
        rows = self._read_csv("SmartBerth_AI_Berth_Parameters_Training_Data.csv")
        
        vessel_types_seen = set()
        linked_to_terminal = 0
        linked_to_port = 0
        
        for row in rows:
            berth_id = row.get('berth_id') or row.get('berthId') or row.get('BERTH_ID', '')
            if not berth_id:
                continue
            
            node_id = f"BERTH_{berth_id}"
            terminal_id = row.get('terminal_id') or row.get('terminalId', '')
            port_code = row.get('port_code') or row.get('portCode', '')
            port_id = row.get('port_id') or row.get('portId', '')
            berth_type = row.get('berth_type') or row.get('berthType', '')
            
            # Also handle different column names for dimensions
            berth_length = self._safe_float(row.get('berth_length') or row.get('berthLength') or row.get('length', 0))
            berth_depth = self._safe_float(row.get('berth_depth') or row.get('berthDepth') or row.get('depth', 0))
            
            self._add_node(
                node_id,
                NodeType.BERTH,
                berth_id=berth_id,
                berth_name=row.get('berth_name') or row.get('berthName', ''),
                berth_code=row.get('berth_code') or row.get('berthCode', ''),
                berth_type=berth_type,
                terminal_id=terminal_id,
                port_code=port_code,
                port_id=port_id,
                berth_length=berth_length,
                berth_depth=berth_depth,
                max_loa=self._safe_float(row.get('max_loa') or row.get('maxLOA', 0)),
                max_beam=self._safe_float(row.get('max_beam') or row.get('maxBeam', 0)),
                max_draft=self._safe_float(row.get('max_draft') or row.get('maxDraft', 0)),
                has_crane=row.get('has_crane', '').lower() in ('true', '1', 'yes'),
                has_shore_power=row.get('has_shore_power', '').lower() in ('true', '1', 'yes'),
            )
            self._berth_index[berth_id] = node_id
            self._berth_index[str(berth_id)] = node_id
            
            # Create edge: TERMINAL -> BERTH
            terminal_node_id = None
            if terminal_id and str(terminal_id) in self._terminal_index:
                terminal_node_id = self._terminal_index[str(terminal_id)]
            
            if terminal_node_id:
                self._add_edge(
                    terminal_node_id,
                    node_id,
                    EdgeType.HAS_BERTH
                )
                linked_to_terminal += 1
            else:
                # Fallback: PORT -> BERTH if no terminal link
                port_node_id = None
                if port_code and port_code in self._port_index:
                    port_node_id = self._port_index[port_code]
                elif port_id and str(port_id) in self._port_index:
                    port_node_id = self._port_index[str(port_id)]
                
                if port_node_id:
                    self._add_edge(
                        port_node_id,
                        node_id,
                        EdgeType.HAS_BERTH
                    )
                    linked_to_port += 1
            
            # Create vessel type nodes and edges
            if berth_type and berth_type not in vessel_types_seen:
                type_node_id = f"VESSEL_TYPE_{berth_type.upper().replace(' ', '_')}"
                if type_node_id not in self.graph:
                    self._add_node(
                        type_node_id,
                        NodeType.VESSEL_TYPE,
                        type_name=berth_type
                    )
                vessel_types_seen.add(berth_type)
            
            # Berth supports vessel type
            if berth_type:
                type_node_id = f"VESSEL_TYPE_{berth_type.upper().replace(' ', '_')}"
                if type_node_id in self.graph:
                    self._add_edge(node_id, type_node_id, EdgeType.SUPPORTS_TYPE)
        
        logger.info(f"  Loaded {len([k for k in self._berth_index if not k.isdigit()])} berths, {len(vessel_types_seen)} vessel types")
        logger.info(f"    {linked_to_terminal} berths linked to terminals, {linked_to_port} linked directly to ports")
    
    def _load_channels(self):
        """Load channel data"""
        rows = self._read_csv("SmartBerth_AI_Channel_Parameters_Training_Data.csv")
        
        channel_count = 0
        for row in rows:
            channel_id = row.get('channel_id') or row.get('channelId') or f"CH_{channel_count}"
            port_code = row.get('port_code') or row.get('portCode', '')
            
            node_id = f"CHANNEL_{channel_id}"
            
            self._add_node(
                node_id,
                NodeType.CHANNEL,
                channel_id=channel_id,
                channel_name=row.get('channel_name') or row.get('channelName', ''),
                port_code=port_code,
                channel_depth=self._safe_float(row.get('channel_depth') or row.get('channelDepth', 0)),
                channel_width=self._safe_float(row.get('channel_width') or row.get('channelWidth', 0)),
                max_vessel_loa=self._safe_float(row.get('max_vessel_loa') or row.get('maxVesselLOA', 0)),
                max_vessel_beam=self._safe_float(row.get('max_vessel_beam') or row.get('maxVesselBeam', 0)),
                one_way=row.get('one_way', '').lower() in ('true', '1', 'yes'),
            )
            
            # Create edge: PORT -> CHANNEL
            if port_code and port_code in self._port_index:
                self._add_edge(
                    self._port_index[port_code],
                    node_id,
                    EdgeType.HAS_CHANNEL
                )
            
            channel_count += 1
        
        logger.info(f"  Loaded {channel_count} channels")
    
    def _load_anchorages(self):
        """Load anchorage data"""
        rows = self._read_csv("SmartBerth_AI_Anchorage_Parameters_Training_Data.csv")
        
        anchorage_count = 0
        for row in rows:
            anchorage_id = row.get('anchorage_id') or row.get('anchorageId') or f"ANC_{anchorage_count}"
            port_code = row.get('port_code') or row.get('portCode', '')
            
            node_id = f"ANCHORAGE_{anchorage_id}"
            
            self._add_node(
                node_id,
                NodeType.ANCHORAGE,
                anchorage_id=anchorage_id,
                anchorage_name=row.get('anchorage_name') or row.get('anchorageName', ''),
                port_code=port_code,
                anchorage_type=row.get('anchorage_type') or row.get('anchorageType', ''),
                max_vessels=self._safe_int(row.get('max_vessels') or row.get('maxVessels', 0)),
                max_draft=self._safe_float(row.get('max_draft') or row.get('maxDraft', 0)),
                avg_waiting_time=self._safe_float(row.get('avg_waiting_time') or row.get('avgWaitingTime', 0)),
            )
            
            # Create edge: PORT -> ANCHORAGE
            if port_code and port_code in self._port_index:
                self._add_edge(
                    self._port_index[port_code],
                    node_id,
                    EdgeType.HAS_ANCHORAGE
                )
            
            anchorage_count += 1
        
        logger.info(f"  Loaded {anchorage_count} anchorages")
    
    def _load_vessels(self):
        """Load vessel data"""
        rows = self._read_csv("SmartBerth_AI_Vessel_Parameters_Training_Data.csv")
        
        for row in rows:
            imo = row.get('imo_number') or row.get('imoNumber') or row.get('IMO_NUMBER', '')
            vessel_id = row.get('vessel_id') or row.get('vesselId') or imo
            if not vessel_id:
                continue
            
            node_id = f"VESSEL_{vessel_id}"
            vessel_name = row.get('vessel_name') or row.get('vesselName', '')
            vessel_type = row.get('vessel_type') or row.get('vesselType', '')
            
            self._add_node(
                node_id,
                NodeType.VESSEL,
                vessel_id=vessel_id,
                imo_number=imo,
                vessel_name=vessel_name,
                vessel_type=vessel_type,
                flag_state=row.get('flag_state') or row.get('flagState', ''),
                loa=self._safe_float(row.get('loa') or row.get('LOA', 0)),
                beam=self._safe_float(row.get('beam', 0)),
                draft=self._safe_float(row.get('draft', 0)),
                gross_tonnage=self._safe_float(row.get('gross_tonnage') or row.get('grossTonnage', 0)),
                dwt=self._safe_float(row.get('dwt') or row.get('DWT', 0)),
                year_built=self._safe_int(row.get('year_built') or row.get('yearBuilt', 0)),
            )
            
            if imo:
                self._vessel_index[imo] = node_id
            if vessel_name:
                self._vessel_name_index[vessel_name.upper()] = node_id
            
            # Create edge: VESSEL -> VESSEL_TYPE
            if vessel_type:
                type_node_id = f"VESSEL_TYPE_{vessel_type.upper().replace(' ', '_')}"
                if type_node_id not in self.graph:
                    self._add_node(
                        type_node_id,
                        NodeType.VESSEL_TYPE,
                        type_name=vessel_type
                    )
                self._add_edge(node_id, type_node_id, EdgeType.IS_TYPE)
        
        logger.info(f"  Loaded {len(self._vessel_index)} vessels")
    
    def _load_pilots(self):
        """Load pilot data"""
        rows = self._read_csv("SmartBerth_AI_Pilotage_Parameters_Training_Data.csv")
        
        pilot_count = 0
        for row in rows:
            pilot_id = row.get('pilot_id') or row.get('pilotId') or f"PLT_{pilot_count}"
            port_code = row.get('port_code') or row.get('portCode', '')
            
            node_id = f"PILOT_{pilot_id}"
            
            self._add_node(
                node_id,
                NodeType.PILOT,
                pilot_id=pilot_id,
                pilot_name=row.get('pilot_name') or row.get('pilotName', ''),
                port_code=port_code,
                pilot_type=row.get('pilot_type') or row.get('pilotType', ''),
                certification_level=row.get('certification_level') or row.get('certificationLevel', ''),
                max_vessel_loa=self._safe_float(row.get('max_vessel_loa') or row.get('maxVesselLOA', 0)),
                max_vessel_draft=self._safe_float(row.get('max_vessel_draft') or row.get('maxVesselDraft', 0)),
                night_operations=row.get('night_operations', '').lower() in ('true', '1', 'yes'),
                status=row.get('status', 'active'),
            )
            
            # Create edge: PORT -> PILOT
            if port_code and port_code in self._port_index:
                self._add_edge(
                    self._port_index[port_code],
                    node_id,
                    EdgeType.HAS_PILOT
                )
            
            pilot_count += 1
        
        logger.info(f"  Loaded {pilot_count} pilots")
        self._stats.pilots = pilot_count
    
    def _load_tugboats(self):
        """Load tugboat data"""
        rows = self._read_csv("SmartBerth_AI_Tugboat_Parameters_Training_Data.csv")
        
        tug_count = 0
        for row in rows:
            tug_id = row.get('tug_id') or row.get('tugId') or f"TUG_{tug_count}"
            port_code = row.get('port_code') or row.get('portCode', '')
            
            node_id = f"TUG_{tug_id}"
            
            self._add_node(
                node_id,
                NodeType.TUGBOAT,
                tug_id=tug_id,
                tug_name=row.get('tug_name') or row.get('tugName', ''),
                port_code=port_code,
                tug_type=row.get('tug_type') or row.get('tugType', ''),
                bollard_pull=self._safe_float(row.get('bollard_pull') or row.get('bollardPull', 0)),
                engine_power=self._safe_float(row.get('engine_power') or row.get('enginePower', 0)),
                status=row.get('status', 'active'),
            )
            
            # Create edge: PORT -> TUGBOAT
            if port_code and port_code in self._port_index:
                self._add_edge(
                    self._port_index[port_code],
                    node_id,
                    EdgeType.HAS_TUG
                )
            
            tug_count += 1
        
        logger.info(f"  Loaded {tug_count} tugboats")
        self._stats.tugboats = tug_count
    
    def _load_vessel_calls(self):
        """Load vessel call/berth assignment data"""
        rows = self._read_csv("SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv")
        
        call_count = 0
        for row in rows:
            call_id = row.get('call_id') or row.get('callId') or f"CALL_{call_count}"
            
            node_id = f"VESSEL_CALL_{call_id}"
            vessel_name = row.get('vessel_name') or row.get('vesselName', '')
            imo = row.get('imo_number') or row.get('imoNumber', '')
            berth_id = row.get('berth') or row.get('berthId', '')
            port_code = row.get('port_code') or row.get('portCode', '')
            
            self._add_node(
                node_id,
                NodeType.VESSEL_CALL,
                call_id=call_id,
                vessel_name=vessel_name,
                imo_number=imo,
                port_code=port_code,
                berth_id=berth_id,
                eta=row.get('eta') or row.get('ETA', ''),
                etd=row.get('etd') or row.get('ETD', ''),
                ata=row.get('ata') or row.get('ATA', ''),
                atd=row.get('atd') or row.get('ATD', ''),
                waiting_time_hours=self._safe_float(row.get('waiting_time_hours') or row.get('waitingTimeHours', 0)),
                dwell_time_hours=self._safe_float(row.get('dwell_time_hours') or row.get('dwellTimeHours', 0)),
                cargo_type=row.get('cargo_type') or row.get('cargoType', ''),
            )
            
            # VESSEL -> MADE_CALL -> VESSEL_CALL
            vessel_node = None
            if imo and imo in self._vessel_index:
                vessel_node = self._vessel_index[imo]
            elif vessel_name and vessel_name.upper() in self._vessel_name_index:
                vessel_node = self._vessel_name_index[vessel_name.upper()]
            
            if vessel_node:
                self._add_edge(vessel_node, node_id, EdgeType.MADE_CALL)
            
            # VESSEL_CALL -> AT_BERTH -> BERTH
            if berth_id:
                berth_node = self._berth_index.get(berth_id)
                if not berth_node:
                    # Try to find berth by partial match
                    for bid, bnode in self._berth_index.items():
                        if berth_id in bid or bid in berth_id:
                            berth_node = bnode
                            break
                
                if berth_node:
                    self._add_edge(node_id, berth_node, EdgeType.AT_BERTH)
            
            # VESSEL_CALL -> AT_PORT -> PORT
            if port_code and port_code in self._port_index:
                self._add_edge(node_id, self._port_index[port_code], EdgeType.AT_PORT)
            
            call_count += 1
        
        logger.info(f"  Loaded {call_count} vessel calls")
        self._stats.vessel_calls = call_count
    
    def _load_ukc_data(self):
        """Load UKC calculation data"""
        rows = self._read_csv("SmartBerth_AI_UKC_Training_Data.csv")
        
        # Store as aggregated statistics rather than individual nodes
        ukc_count = len(rows)
        logger.info(f"  Loaded {ukc_count} UKC records (stored as reference data)")
    
    def _load_weather_data(self):
        """Load weather data"""
        rows = self._read_csv("SmartBerth_AI_Weather_Parameters_Training_Data.csv")
        
        weather_count = len(rows)
        logger.info(f"  Loaded {weather_count} weather records (stored as reference data)")
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _safe_float(self, value) -> float:
        """Safely convert to float"""
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value) -> int:
        """Safely convert to int"""
        try:
            return int(float(value)) if value else 0
        except (ValueError, TypeError):
            return 0
    
    def _update_stats(self):
        """Update graph statistics"""
        self._stats.total_nodes = self.graph.number_of_nodes()
        self._stats.total_edges = self.graph.number_of_edges()
        
        # Count by type
        self._stats.nodes_by_type = defaultdict(int)
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'UNKNOWN')
            self._stats.nodes_by_type[node_type] += 1
        
        self._stats.edges_by_type = defaultdict(int)
        for u, v, data in self.graph.edges(data=True):
            edge_type = data.get('edge_type', 'UNKNOWN')
            self._stats.edges_by_type[edge_type] += 1
        
        self._stats.ports = len(self._port_index)
        self._stats.terminals = len(self._terminal_index)
        self._stats.berths = len(self._berth_index)
        self._stats.vessels = len(self._vessel_index)
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            "status": "loaded" if self._loaded else "not_loaded",
            "total_nodes": self._stats.total_nodes,
            "total_edges": self._stats.total_edges,
            "nodes_by_type": dict(self._stats.nodes_by_type),
            "edges_by_type": dict(self._stats.edges_by_type),
            "counts": {
                "ports": self._stats.ports,
                "terminals": self._stats.terminals,
                "berths": self._stats.berths,
                "vessels": self._stats.vessels,
                "vessel_calls": self._stats.vessel_calls,
                "pilots": self._stats.pilots,
                "tugboats": self._stats.tugboats,
            }
        }
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get a node by ID"""
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None
    
    def get_nodes_by_type(self, node_type: NodeType) -> List[Dict]:
        """Get all nodes of a specific type"""
        results = []
        for node, data in self.graph.nodes(data=True):
            if data.get('node_type') == node_type.value:
                results.append({'id': node, **data})
        return results
    
    def get_neighbors(
        self,
        node_id: str,
        edge_type: EdgeType = None,
        direction: str = "out"  # "out", "in", or "both"
    ) -> List[Dict]:
        """Get neighbors of a node"""
        if node_id not in self.graph:
            return []
        
        neighbors = []
        
        if direction in ("out", "both"):
            for _, target, data in self.graph.out_edges(node_id, data=True):
                if edge_type is None or data.get('edge_type') == edge_type.value:
                    neighbors.append({
                        'id': target,
                        'edge_type': data.get('edge_type'),
                        **self.graph.nodes[target]
                    })
        
        if direction in ("in", "both"):
            for source, _, data in self.graph.in_edges(node_id, data=True):
                if edge_type is None or data.get('edge_type') == edge_type.value:
                    neighbors.append({
                        'id': source,
                        'edge_type': data.get('edge_type'),
                        **self.graph.nodes[source]
                    })
        
        return neighbors
    
    def find_compatible_berths(
        self,
        vessel_type: str = None,
        min_loa: float = None,
        min_depth: float = None,
        port_code: str = None
    ) -> List[Dict]:
        """
        Find berths compatible with vessel requirements.
        
        Args:
            vessel_type: Type of vessel (Container, Tanker, etc.)
            min_loa: Minimum LOA capacity needed
            min_depth: Minimum depth needed
            port_code: Filter by port code
            
        Returns:
            List of compatible berth data
        """
        results = []
        
        for berth_id, node_id in self._berth_index.items():
            data = self.graph.nodes[node_id]
            
            # Port filter
            if port_code and data.get('port_code') != port_code:
                continue
            
            # Vessel type filter
            if vessel_type:
                berth_type = data.get('berth_type', '').lower()
                if vessel_type.lower() not in berth_type and berth_type not in vessel_type.lower():
                    # Also check if berth supports this type via edges
                    supported = False
                    for _, target, edge_data in self.graph.out_edges(node_id, data=True):
                        if edge_data.get('edge_type') == EdgeType.SUPPORTS_TYPE.value:
                            type_data = self.graph.nodes.get(target, {})
                            if vessel_type.lower() in type_data.get('type_name', '').lower():
                                supported = True
                                break
                    if not supported:
                        continue
            
            # LOA filter
            if min_loa:
                max_loa = data.get('max_loa', 0)
                if max_loa and max_loa < min_loa:
                    continue
            
            # Depth filter
            if min_depth:
                max_depth = data.get('berth_depth', 0) or data.get('max_draft', 0)
                if max_depth and max_depth < min_depth:
                    continue
            
            results.append({
                'berth_id': berth_id,
                'berth_name': data.get('berth_name'),
                'berth_type': data.get('berth_type'),
                'port_code': data.get('port_code'),
                'terminal_id': data.get('terminal_id'),
                'max_loa': data.get('max_loa'),
                'max_draft': data.get('max_draft'),
                'berth_depth': data.get('berth_depth'),
                'berth_length': data.get('berth_length'),
            })
        
        return results
    
    def get_port_resources(self, port_code: str) -> Dict[str, Any]:
        """
        Get all resources available at a port.
        
        Returns terminals, berths, pilots, tugboats, channels, anchorages.
        """
        if port_code not in self._port_index:
            return {}
        
        port_node = self._port_index[port_code]
        port_data = self.graph.nodes[port_node]
        
        # Get terminals
        terminals = []
        for neighbor in self.get_neighbors(port_node, EdgeType.HAS_TERMINAL, "out"):
            terminals.append({
                'terminal_id': neighbor.get('terminal_id'),
                'terminal_name': neighbor.get('terminal_name'),
                'terminal_type': neighbor.get('terminal_type'),
            })
        
        # Get berths (direct or via terminals)
        berths = []
        visited_berths = set()
        
        # Direct berths
        for neighbor in self.get_neighbors(port_node, EdgeType.HAS_BERTH, "out"):
            berth_id = neighbor.get('berth_id')
            if berth_id not in visited_berths:
                berths.append({
                    'berth_id': berth_id,
                    'berth_name': neighbor.get('berth_name'),
                    'berth_type': neighbor.get('berth_type'),
                    'max_loa': neighbor.get('max_loa'),
                    'max_draft': neighbor.get('max_draft'),
                })
                visited_berths.add(berth_id)
        
        # Berths via terminals
        for terminal in terminals:
            term_node = self._terminal_index.get(terminal['terminal_id'])
            if term_node:
                for neighbor in self.get_neighbors(term_node, EdgeType.HAS_BERTH, "out"):
                    berth_id = neighbor.get('berth_id')
                    if berth_id not in visited_berths:
                        berths.append({
                            'berth_id': berth_id,
                            'berth_name': neighbor.get('berth_name'),
                            'berth_type': neighbor.get('berth_type'),
                            'terminal_id': terminal['terminal_id'],
                            'max_loa': neighbor.get('max_loa'),
                            'max_draft': neighbor.get('max_draft'),
                        })
                        visited_berths.add(berth_id)
        
        # Get pilots
        pilots = []
        for neighbor in self.get_neighbors(port_node, EdgeType.HAS_PILOT, "out"):
            pilots.append({
                'pilot_id': neighbor.get('pilot_id'),
                'pilot_name': neighbor.get('pilot_name'),
                'pilot_type': neighbor.get('pilot_type'),
                'certification_level': neighbor.get('certification_level'),
                'status': neighbor.get('status'),
            })
        
        # Get tugboats
        tugboats = []
        for neighbor in self.get_neighbors(port_node, EdgeType.HAS_TUG, "out"):
            tugboats.append({
                'tug_id': neighbor.get('tug_id'),
                'tug_name': neighbor.get('tug_name'),
                'tug_type': neighbor.get('tug_type'),
                'bollard_pull': neighbor.get('bollard_pull'),
                'status': neighbor.get('status'),
            })
        
        # Get channels
        channels = []
        for neighbor in self.get_neighbors(port_node, EdgeType.HAS_CHANNEL, "out"):
            channels.append({
                'channel_id': neighbor.get('channel_id'),
                'channel_name': neighbor.get('channel_name'),
                'channel_depth': neighbor.get('channel_depth'),
                'max_vessel_loa': neighbor.get('max_vessel_loa'),
            })
        
        # Get anchorages
        anchorages = []
        for neighbor in self.get_neighbors(port_node, EdgeType.HAS_ANCHORAGE, "out"):
            anchorages.append({
                'anchorage_id': neighbor.get('anchorage_id'),
                'anchorage_name': neighbor.get('anchorage_name'),
                'anchorage_type': neighbor.get('anchorage_type'),
                'max_vessels': neighbor.get('max_vessels'),
            })
        
        return {
            'port_code': port_code,
            'port_name': port_data.get('port_name'),
            'country': port_data.get('country'),
            'terminals': terminals,
            'berths': berths,
            'pilots': pilots,
            'tugboats': tugboats,
            'channels': channels,
            'anchorages': anchorages,
            'summary': {
                'total_terminals': len(terminals),
                'total_berths': len(berths),
                'total_pilots': len(pilots),
                'total_tugboats': len(tugboats),
                'total_channels': len(channels),
                'total_anchorages': len(anchorages),
            }
        }
    
    def find_vessel_history(
        self,
        vessel_name: str = None,
        imo_number: str = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Find vessel call history.
        
        Args:
            vessel_name: Vessel name (partial match)
            imo_number: IMO number
            limit: Maximum results
            
        Returns:
            List of vessel call records
        """
        results = []
        
        # Find vessel node
        vessel_node = None
        if imo_number and imo_number in self._vessel_index:
            vessel_node = self._vessel_index[imo_number]
        elif vessel_name:
            vessel_upper = vessel_name.upper()
            if vessel_upper in self._vessel_name_index:
                vessel_node = self._vessel_name_index[vessel_upper]
            else:
                # Partial match
                for name, node in self._vessel_name_index.items():
                    if vessel_upper in name or name in vessel_upper:
                        vessel_node = node
                        break
        
        if vessel_node:
            # Get vessel info
            vessel_data = self.graph.nodes[vessel_node]
            
            # Get all calls
            for neighbor in self.get_neighbors(vessel_node, EdgeType.MADE_CALL, "out"):
                call_data = {
                    'vessel_name': vessel_data.get('vessel_name'),
                    'imo_number': vessel_data.get('imo_number'),
                    'vessel_type': vessel_data.get('vessel_type'),
                    'call_id': neighbor.get('call_id'),
                    'port_code': neighbor.get('port_code'),
                    'berth_id': neighbor.get('berth_id'),
                    'eta': neighbor.get('eta'),
                    'etd': neighbor.get('etd'),
                    'waiting_time_hours': neighbor.get('waiting_time_hours'),
                    'dwell_time_hours': neighbor.get('dwell_time_hours'),
                }
                results.append(call_data)
                
                if len(results) >= limit:
                    break
        else:
            # Search by vessel_name in calls directly
            for node, data in self.graph.nodes(data=True):
                if data.get('node_type') != NodeType.VESSEL_CALL.value:
                    continue
                
                call_vessel = data.get('vessel_name', '').upper()
                call_imo = data.get('imo_number', '')
                
                match = False
                if vessel_name and vessel_name.upper() in call_vessel:
                    match = True
                if imo_number and call_imo == imo_number:
                    match = True
                
                if match:
                    results.append({
                        'vessel_name': data.get('vessel_name'),
                        'imo_number': data.get('imo_number'),
                        'call_id': data.get('call_id'),
                        'port_code': data.get('port_code'),
                        'berth_id': data.get('berth_id'),
                        'eta': data.get('eta'),
                        'etd': data.get('etd'),
                        'waiting_time_hours': data.get('waiting_time_hours'),
                        'dwell_time_hours': data.get('dwell_time_hours'),
                    })
                    
                    if len(results) >= limit:
                        break
        
        return results
    
    def get_port_hierarchy(self, port_code: str) -> Dict[str, Any]:
        """
        Get full port hierarchy: Port -> Terminals -> Berths
        
        Returns a nested structure showing the port organization.
        """
        if port_code not in self._port_index:
            return {}
        
        port_node = self._port_index[port_code]
        port_data = self.graph.nodes[port_node]
        
        hierarchy = {
            'port': {
                'port_code': port_code,
                'port_name': port_data.get('port_name'),
                'country': port_data.get('country'),
            },
            'terminals': []
        }
        
        # Get terminals
        for term_neighbor in self.get_neighbors(port_node, EdgeType.HAS_TERMINAL, "out"):
            terminal_data = {
                'terminal_id': term_neighbor.get('terminal_id'),
                'terminal_name': term_neighbor.get('terminal_name'),
                'terminal_type': term_neighbor.get('terminal_type'),
                'berths': []
            }
            
            # Get berths for this terminal
            term_node = term_neighbor.get('id')
            for berth_neighbor in self.get_neighbors(term_node, EdgeType.HAS_BERTH, "out"):
                terminal_data['berths'].append({
                    'berth_id': berth_neighbor.get('berth_id'),
                    'berth_name': berth_neighbor.get('berth_name'),
                    'berth_type': berth_neighbor.get('berth_type'),
                    'max_loa': berth_neighbor.get('max_loa'),
                    'max_draft': berth_neighbor.get('max_draft'),
                })
            
            hierarchy['terminals'].append(terminal_data)
        
        return hierarchy
    
    def traverse_path(
        self,
        start_node_type: NodeType,
        end_node_type: NodeType,
        start_filter: Dict = None,
        max_depth: int = 5
    ) -> List[List[Dict]]:
        """
        Find all paths between node types.
        
        Useful for queries like "Find all berths connected to a vessel type"
        """
        paths = []
        
        # Find start nodes
        start_nodes = []
        for node, data in self.graph.nodes(data=True):
            if data.get('node_type') != start_node_type.value:
                continue
            
            if start_filter:
                match = all(
                    data.get(k) == v or (v in str(data.get(k, '')))
                    for k, v in start_filter.items()
                )
                if not match:
                    continue
            
            start_nodes.append(node)
        
        # Find paths from each start node
        for start in start_nodes[:10]:  # Limit for performance
            for node, data in self.graph.nodes(data=True):
                if data.get('node_type') != end_node_type.value:
                    continue
                
                try:
                    for path in nx.all_simple_paths(self.graph, start, node, cutoff=max_depth):
                        path_data = []
                        for p in path:
                            path_data.append({
                                'id': p,
                                **self.graph.nodes[p]
                            })
                        paths.append(path_data)
                        
                        if len(paths) >= 50:  # Limit results
                            return paths
                except nx.NetworkXNoPath:
                    continue
        
        return paths
    
    def get_graph_context(self, query: str, max_nodes: int = 20) -> str:
        """
        Get graph context relevant to a natural language query.
        
        Extracts entity mentions and returns relevant graph information.
        """
        context_parts = []
        query_lower = query.lower()
        
        # Check for port mentions
        for port_code in self._port_index.keys():
            if port_code.lower() in query_lower:
                resources = self.get_port_resources(port_code)
                context_parts.append(f"Port {port_code}: {resources.get('summary')}")
                break
        
        # Check for vessel mentions
        for vessel_name, node_id in list(self._vessel_name_index.items())[:100]:
            if vessel_name.lower() in query_lower:
                vessel_data = self.graph.nodes[node_id]
                context_parts.append(
                    f"Vessel {vessel_name}: Type={vessel_data.get('vessel_type')}, "
                    f"LOA={vessel_data.get('loa')}m, Draft={vessel_data.get('draft')}m"
                )
                break
        
        # Check for berth queries
        if 'berth' in query_lower:
            if 'container' in query_lower:
                berths = self.find_compatible_berths(vessel_type='Container')[:5]
                context_parts.append(f"Container berths available: {len(berths)}")
            elif 'tanker' in query_lower:
                berths = self.find_compatible_berths(vessel_type='Tanker')[:5]
                context_parts.append(f"Tanker berths available: {len(berths)}")
        
        # Add general stats if no specific context found
        if not context_parts:
            stats = self.get_stats()
            context_parts.append(
                f"Graph contains: {stats['counts']['ports']} ports, "
                f"{stats['counts']['terminals']} terminals, "
                f"{stats['counts']['berths']} berths, "
                f"{stats['counts']['vessels']} vessels"
            )
        
        return "\n".join(context_parts)
    
    def is_loaded(self) -> bool:
        """Check if graph is loaded"""
        return self._loaded


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_graph_instance: Optional[InMemoryKnowledgeGraph] = None


def get_knowledge_graph(training_data_dir: str = None) -> InMemoryKnowledgeGraph:
    """Get or create the in-memory knowledge graph"""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = InMemoryKnowledgeGraph(training_data_dir)
    return _graph_instance


def initialize_graph() -> bool:
    """Initialize and load the knowledge graph"""
    graph = get_knowledge_graph()
    return graph.load()
