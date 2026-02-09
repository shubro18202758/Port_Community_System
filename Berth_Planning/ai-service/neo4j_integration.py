"""
SmartBerth AI - Neo4j Training Data Integration
================================================

This module loads the training database into Neo4j for graph-enhanced retrieval.
Creates a knowledge graph with:
- Port → Terminal → Berth hierarchy
- Vessel profiles and types
- Resource networks (Pilots, Tugboats)
- Channel and Anchorage connections
- Historical vessel call relationships

Milestone 3: Integrate Neo4j for real graph operations
"""

import os
import csv
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("Neo4j driver not available. Install with: pip install neo4j")


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration"""
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username: str = os.getenv("NEO4J_USERNAME", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "smartberth123")
    database: str = os.getenv("NEO4J_DATABASE", "neo4j")


class TrainingDataGraphLoader:
    """
    Loads SmartBerth training CSV data into Neo4j graph database.
    Creates comprehensive port operations knowledge graph.
    """
    
    def __init__(
        self,
        training_data_path: str,
        neo4j_config: Optional[Neo4jConfig] = None
    ):
        self.training_data_path = training_data_path
        self.config = neo4j_config or Neo4jConfig()
        self._driver: Optional[Driver] = None
        
        # Statistics
        self.stats = {
            "ports": 0,
            "terminals": 0,
            "berths": 0,
            "vessels": 0,
            "pilots": 0,
            "tugboats": 0,
            "channels": 0,
            "anchorages": 0,
            "vessel_calls": 0,
            "relationships": 0
        }
    
    @property
    def driver(self) -> Optional[Driver]:
        """Lazy initialization of Neo4j driver"""
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j driver not available")
            return None
        
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.config.uri,
                    auth=(self.config.username, self.config.password)
                )
                self._driver.verify_connectivity()
                logger.info(f"✓ Connected to Neo4j at {self.config.uri}")
            except Exception as e:
                logger.error(f"✗ Failed to connect to Neo4j: {e}")
                logger.info("  Make sure Neo4j is running and credentials are correct")
                self._driver = None
        
        return self._driver
    
    def close(self):
        """Close Neo4j connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def _read_csv(self, filename: str, max_rows: int = None) -> List[Dict]:
        """Read CSV file from training data folder"""
        filepath = os.path.join(self.training_data_path, filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return []
        
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if max_rows and i >= max_rows:
                    break
                data.append(row)
        
        return data
    
    def _execute_cypher(self, cypher: str, params: Dict = None) -> int:
        """Execute Cypher query and return count of affected items"""
        if not self.driver:
            return 0
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(cypher, **(params or {}))
            summary = result.consume()
            return summary.counters.nodes_created + summary.counters.relationships_created
    
    def _execute_batch(self, cypher: str, data: List[Dict], batch_param: str = "batch") -> int:
        """Execute Cypher in batches"""
        if not self.driver or not data:
            return 0
        
        total = 0
        batch_size = 500
        
        with self.driver.session(database=self.config.database) as session:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                result = session.run(cypher, **{batch_param: batch})
                summary = result.consume()
                total += summary.counters.nodes_created + summary.counters.relationships_created
        
        return total
    
    def clear_graph(self):
        """Clear all data from the graph"""
        if not self.driver:
            return False
        
        logger.info("Clearing existing graph data...")
        with self.driver.session(database=self.config.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        logger.info("  ✓ Graph cleared")
        return True
    
    def create_constraints(self):
        """Create unique constraints and indexes"""
        if not self.driver:
            return False
        
        logger.info("Creating constraints and indexes...")
        
        constraints = [
            ("Port", "portId"),
            ("Terminal", "terminalId"),
            ("Berth", "berthId"),
            ("Vessel", "vesselId"),
            ("VesselType", "name"),
            ("Pilot", "pilotId"),
            ("Tugboat", "tugId"),
            ("Channel", "channelId"),
            ("Anchorage", "anchorageId"),
            ("CargoType", "name"),
            ("VesselCall", "callId"),
        ]
        
        with self.driver.session(database=self.config.database) as session:
            for label, prop in constraints:
                try:
                    session.run(f"""
                        CREATE CONSTRAINT {label.lower()}_{prop} IF NOT EXISTS
                        FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE
                    """)
                except Exception as e:
                    logger.debug(f"Constraint may exist: {e}")
            
            # Create indexes for common lookups
            indexes = [
                "CREATE INDEX port_code IF NOT EXISTS FOR (p:Port) ON (p.portCode)",
                "CREATE INDEX vessel_imo IF NOT EXISTS FOR (v:Vessel) ON (v.imoNumber)",
                "CREATE INDEX vessel_type_index IF NOT EXISTS FOR (v:Vessel) ON (v.vesselType)",
            ]
            for idx in indexes:
                try:
                    session.run(idx)
                except:
                    pass
        
        logger.info("  ✓ Constraints created")
        return True
    
    def load_ports(self) -> int:
        """Load Port nodes"""
        data = self._read_csv("SmartBerth_AI_Port_Parameters_Training_Data.csv")
        if not data:
            return 0
        
        logger.info(f"Loading {len(data)} ports...")
        
        cypher = """
        UNWIND $batch AS row
        MERGE (p:Port {portId: toInteger(row.portId)})
        SET p.portCode = row.portCode,
            p.portName = row.portName,
            p.country = row.country,
            p.city = row.city,
            p.timezone = row.timezone,
            p.latitude = toFloat(row.latitude),
            p.longitude = toFloat(row.longitude),
            p.contactEmail = row.contactEmail,
            p.contactPhone = row.contactPhone,
            p.isActive = row.isActive = 'TRUE'
        """
        
        count = self._execute_batch(cypher, data)
        self.stats["ports"] = len(data)
        logger.info(f"  ✓ Loaded {len(data)} ports")
        return count
    
    def load_terminals(self) -> int:
        """Load Terminal nodes and connect to Ports"""
        data = self._read_csv("SmartBerth_AI_Terminal_Parameters_Training_Data.csv")
        if not data:
            return 0
        
        logger.info(f"Loading {len(data)} terminals...")
        
        cypher = """
        UNWIND $batch AS row
        MERGE (t:Terminal {terminalId: toInteger(row.terminalId)})
        SET t.terminalCode = row.terminalCode,
            t.terminalName = row.terminalName,
            t.terminalType = row.terminalType,
            t.operatorName = row.operatorName,
            t.latitude = toFloat(row.latitude),
            t.longitude = toFloat(row.longitude),
            t.isActive = row.isActive = 'TRUE',
            t.totalBerths = toInteger(row.totalBerths)
        WITH t, row
        MATCH (p:Port {portId: toInteger(row.portId)})
        MERGE (t)-[:LOCATED_IN]->(p)
        
        // Also create TerminalType node for categorization
        WITH t, row
        MERGE (tt:TerminalType {name: row.terminalType})
        MERGE (t)-[:IS_TYPE]->(tt)
        """
        
        count = self._execute_batch(cypher, data)
        self.stats["terminals"] = len(data)
        self.stats["relationships"] += len(data) * 2
        logger.info(f"  ✓ Loaded {len(data)} terminals")
        return count
    
    def load_berths(self) -> int:
        """Load Berth nodes and connect to Terminals"""
        data = self._read_csv("SmartBerth_AI_Berth_Parameters_Training_Data.csv")
        if not data:
            return 0
        
        logger.info(f"Loading {len(data)} berths...")
        
        cypher = """
        UNWIND $batch AS row
        MERGE (b:Berth {berthId: toInteger(row.berthId)})
        SET b.berthCode = row.berthCode,
            b.berthType = row.berthType,
            b.length = toFloat(row.length),
            b.depth = toFloat(row.depth),
            b.maxDraft = toFloat(row.maxDraft),
            b.maxLOA = toFloat(row.maxLOA),
            b.maxBeam = toFloat(row.maxBeam),
            b.numberOfCranes = toInteger(row.numberOfCranes),
            b.latitude = toFloat(row.latitude),
            b.longitude = toFloat(row.longitude)
        WITH b, row
        MATCH (t:Terminal {terminalId: toInteger(row.terminalId)})
        MERGE (b)-[:BELONGS_TO]->(t)
        
        // Create BerthType node
        WITH b, row
        MERGE (bt:BerthType {name: row.berthType})
        MERGE (b)-[:IS_TYPE]->(bt)
        """
        
        count = self._execute_batch(cypher, data)
        self.stats["berths"] = len(data)
        self.stats["relationships"] += len(data) * 2
        logger.info(f"  ✓ Loaded {len(data)} berths")
        return count
    
    def load_vessels(self) -> int:
        """Load Vessel nodes with type classification"""
        data = self._read_csv("SmartBerth_AI_Vessel_Parameters_Training_Data.csv")
        if not data:
            return 0
        
        logger.info(f"Loading {len(data)} vessels...")
        
        cypher = """
        UNWIND $batch AS row
        MERGE (v:Vessel {vesselId: toInteger(row.vessel_id)})
        SET v.imoNumber = row.imo_number,
            v.vesselName = row.vessel_name,
            v.vesselType = row.vessel_type,
            v.flagState = row.flagState,
            v.loa = toFloat(row.loa),
            v.beam = toFloat(row.beam),
            v.draft = toFloat(row.draft),
            v.grossTonnage = toFloat(row.grossTonnage),
            v.cargoType = row.cargoType
        WITH v, row
        MERGE (vt:VesselType {name: row.vessel_type})
        MERGE (v)-[:IS_TYPE]->(vt)
        
        // Connect to cargo type
        WITH v, row
        WHERE row.cargoType IS NOT NULL AND row.cargoType <> ''
        MERGE (ct:CargoType {name: row.cargoType})
        MERGE (v)-[:CAN_CARRY]->(ct)
        """
        
        count = self._execute_batch(cypher, data)
        self.stats["vessels"] = len(data)
        self.stats["relationships"] += len(data) * 2
        logger.info(f"  ✓ Loaded {len(data)} vessels")
        return count
    
    def load_pilots(self) -> int:
        """Load Pilot nodes and connect to Ports"""
        data = self._read_csv("SmartBerth_AI_Pilotage_Parameters_Training_Data.csv")
        if not data:
            return 0
        
        logger.info(f"Loading {len(data)} pilots...")
        
        cypher = """
        UNWIND $batch AS row
        MERGE (pi:Pilot {pilotId: toInteger(row.pilotId)})
        SET pi.pilotName = row.pilotName,
            pi.pilotCode = row.pilotCode,
            pi.pilotType = row.pilotType,
            pi.pilotClass = row.pilotClass,
            pi.certificationLevel = row.certificationLevel,
            pi.experienceYears = toInteger(row.experienceYears),
            pi.maxVesselGT = row.maxVesselGT,
            pi.maxVesselLOA = row.maxVesselLOA,
            pi.nightOperations = row.nightOperations = 'TRUE',
            pi.adverseWeather = row.adverseWeather = 'TRUE',
            pi.status = row.status
        WITH pi, row
        MATCH (p:Port {portCode: row.portCode})
        MERGE (pi)-[:SERVES]->(p)
        
        // Create PilotType node
        WITH pi, row
        MERGE (pt:PilotType {name: row.pilotType})
        MERGE (pi)-[:IS_TYPE]->(pt)
        """
        
        count = self._execute_batch(cypher, data)
        self.stats["pilots"] = len(data)
        self.stats["relationships"] += len(data) * 2
        logger.info(f"  ✓ Loaded {len(data)} pilots")
        return count
    
    def load_tugboats(self) -> int:
        """Load Tugboat nodes and connect to Ports"""
        data = self._read_csv("SmartBerth_AI_Tugboat_Parameters_Training_Data.csv")
        if not data:
            return 0
        
        logger.info(f"Loading {len(data)} tugboats...")
        
        cypher = """
        UNWIND $batch AS row
        MERGE (tug:Tugboat {tugId: toInteger(row.tugId)})
        SET tug.tugName = row.tugName,
            tug.tugCode = row.tugCode,
            tug.imoNumber = row.imoNumber,
            tug.tugType = row.tugType,
            tug.tugClass = row.tugClass,
            tug.operator = row.operator,
            tug.bollardPull = toInteger(row.bollardPull),
            tug.length = toFloat(row.length),
            tug.beam = toFloat(row.beam),
            tug.draft = toFloat(row.draft),
            tug.enginePower = toInteger(row.enginePower),
            tug.maxSpeed = toFloat(row.maxSpeed),
            tug.fifiClass = row.fifiClass,
            tug.status = row.status
        WITH tug, row
        MATCH (p:Port {portCode: row.portCode})
        MERGE (tug)-[:OPERATES_FROM]->(p)
        
        // Create TugType node
        WITH tug, row
        MERGE (tt:TugType {name: row.tugType})
        MERGE (tug)-[:IS_TYPE]->(tt)
        """
        
        count = self._execute_batch(cypher, data)
        self.stats["tugboats"] = len(data)
        self.stats["relationships"] += len(data) * 2
        logger.info(f"  ✓ Loaded {len(data)} tugboats")
        return count
    
    def load_channels(self) -> int:
        """Load Channel nodes and connect to Ports"""
        data = self._read_csv("SmartBerth_AI_Channel_Parameters_Training_Data.csv")
        if not data:
            return 0
        
        logger.info(f"Loading {len(data)} channels...")
        
        cypher = """
        UNWIND $batch AS row
        MERGE (ch:Channel {channelId: toInteger(row.channelId)})
        SET ch.channelName = row.channelName,
            ch.channelLength = toFloat(row.channelLength),
            ch.channelWidth = toFloat(row.channelWidth),
            ch.channelDepth = toFloat(row.channelDepth),
            ch.configuration = row.oneWayOrTwoWay,
            ch.maxVesselLOA = toFloat(row.maxVesselLOA),
            ch.maxVesselBeam = toFloat(row.maxVesselBeam),
            ch.maxVesselDraft = toFloat(row.maxVesselDraft),
            ch.speedLimit = toInteger(row.speedLimit),
            ch.tidalWindowRequired = row.tidalWindowRequired = 'TRUE',
            ch.pilotageCompulsory = row.pilotageCompulsory = 'TRUE',
            ch.tugEscortRequired = row.tugEscortRequired = 'TRUE'
        WITH ch, row
        MATCH (p:Port {portId: toInteger(row.portId)})
        MERGE (ch)-[:ACCESS_TO]->(p)
        """
        
        count = self._execute_batch(cypher, data)
        self.stats["channels"] = len(data)
        self.stats["relationships"] += len(data)
        logger.info(f"  ✓ Loaded {len(data)} channels")
        return count
    
    def load_anchorages(self) -> int:
        """Load Anchorage nodes and connect to Ports"""
        data = self._read_csv("SmartBerth_AI_Anchorage_Parameters_Training_Data.csv")
        if not data:
            return 0
        
        logger.info(f"Loading {len(data)} anchorages...")
        
        cypher = """
        UNWIND $batch AS row
        MERGE (a:Anchorage {anchorageId: toInteger(row.anchorageId)})
        SET a.anchorageName = row.anchorageName,
            a.anchorageType = row.anchorageType,
            a.latitude = toFloat(row.latitude),
            a.longitude = toFloat(row.longitude),
            a.depth = toFloat(row.depth),
            a.maxVessels = toInteger(row.maxVessels),
            a.maxVesselLOA = toFloat(row.maxVesselLOA),
            a.maxVesselDraft = toFloat(row.maxVesselDraft),
            a.averageWaitingTime = toFloat(row.averageWaitingTime),
            a.stsOpsPermitted = row.stsCargOpsPermitted = 'TRUE',
            a.isQuarantine = row.quarantineAnchorage = 'TRUE'
        WITH a, row
        MATCH (p:Port {portId: toInteger(row.portId)})
        MERGE (a)-[:ANCHORAGE_FOR]->(p)
        
        // Create AnchorageType node
        WITH a, row
        MERGE (at:AnchorageType {name: row.anchorageType})
        MERGE (a)-[:IS_TYPE]->(at)
        """
        
        count = self._execute_batch(cypher, data)
        self.stats["anchorages"] = len(data)
        self.stats["relationships"] += len(data) * 2
        logger.info(f"  ✓ Loaded {len(data)} anchorages")
        return count
    
    def load_vessel_calls(self, max_rows: int = 2000) -> int:
        """Load vessel call history as relationships (sample for performance)"""
        data = self._read_csv("SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv", max_rows)
        if not data:
            return 0
        
        logger.info(f"Loading {len(data)} vessel calls (sampled)...")
        
        # Create VesselCall nodes and relationships
        cypher = """
        UNWIND $batch AS row
        MERGE (vc:VesselCall {callId: toInteger(row.callId)})
        SET vc.eta = row.eta,
            vc.ata = row.ata,
            vc.etd = row.etd,
            vc.atd = row.atd,
            vc.cargoType = row.cargoType,
            vc.cargoVolume = toFloat(row.cargoVolume),
            vc.waitingTimeHours = toFloat(row.waitingTimeHours),
            vc.dwellTimeHours = toFloat(row.dwellTimeHours),
            vc.tugsRequired = toInteger(row.tugsRequired),
            vc.pilotsRequired = toInteger(row.pilotsRequired)
        
        // Connect to Port
        WITH vc, row
        MATCH (p:Port {portCode: row.portCode})
        MERGE (vc)-[:CALLED_AT]->(p)
        
        // Connect to Berth (using berthCode if available)
        WITH vc, row
        MATCH (b:Berth {berthCode: row.berthCode})
        MERGE (vc)-[:ASSIGNED_TO]->(b)
        """
        
        count = self._execute_batch(cypher, data)
        self.stats["vessel_calls"] = len(data)
        self.stats["relationships"] += len(data) * 2
        logger.info(f"  ✓ Loaded {len(data)} vessel calls")
        return count
    
    def create_type_hierarchies(self):
        """Create type hierarchy relationships"""
        if not self.driver:
            return
        
        logger.info("Creating type hierarchies...")
        
        # Connect vessel types that can dock at specific berth types
        cypher = """
        // Container vessels to container berths
        MATCH (vt:VesselType)
        WHERE vt.name CONTAINS 'Container' OR vt.name CONTAINS 'ULCV' OR vt.name CONTAINS 'Feeder'
        MATCH (bt:BerthType)
        WHERE bt.name = 'Container'
        MERGE (vt)-[:COMPATIBLE_WITH]->(bt)
        
        // Tankers to tanker berths
        WITH 1 AS dummy
        MATCH (vt:VesselType)
        WHERE vt.name CONTAINS 'Tanker' OR vt.name CONTAINS 'VLCC' OR vt.name CONTAINS 'Suezmax' OR vt.name CONTAINS 'Aframax'
        MATCH (bt:BerthType)
        WHERE bt.name IN ['Liquid Bulk', 'Oil']
        MERGE (vt)-[:COMPATIBLE_WITH]->(bt)
        
        // Bulk carriers to bulk berths
        WITH 1 AS dummy
        MATCH (vt:VesselType)
        WHERE vt.name CONTAINS 'Bulk'
        MATCH (bt:BerthType)
        WHERE bt.name IN ['Dry Bulk', 'Bulk']
        MERGE (vt)-[:COMPATIBLE_WITH]->(bt)
        
        // LNG/LPG carriers
        WITH 1 AS dummy
        MATCH (vt:VesselType)
        WHERE vt.name CONTAINS 'LNG' OR vt.name CONTAINS 'LPG'
        MATCH (bt:BerthType)
        WHERE bt.name IN ['Gas', 'LNG', 'Liquid Bulk']
        MERGE (vt)-[:COMPATIBLE_WITH]->(bt)
        """
        
        with self.driver.session(database=self.config.database) as session:
            session.run(cypher)
        
        self.stats["relationships"] += 50  # Approximate
        logger.info("  ✓ Type hierarchies created")
    
    def load_all(self, clear_first: bool = True) -> Dict[str, int]:
        """Load all training data into Neo4j"""
        start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("SmartBerth AI - Loading Training Data to Neo4j")
        logger.info("=" * 60)
        
        if not self.driver:
            logger.error("Cannot connect to Neo4j. Aborting.")
            return self.stats
        
        if clear_first:
            self.clear_graph()
        
        self.create_constraints()
        
        # Load in dependency order
        self.load_ports()
        self.load_terminals()
        self.load_berths()
        self.load_vessels()
        self.load_pilots()
        self.load_tugboats()
        self.load_channels()
        self.load_anchorages()
        self.load_vessel_calls()
        self.create_type_hierarchies()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Graph Loading Complete!")
        logger.info(f"  Total Time: {elapsed:.2f}s")
        logger.info(f"  Nodes Created:")
        logger.info(f"    - Ports: {self.stats['ports']}")
        logger.info(f"    - Terminals: {self.stats['terminals']}")
        logger.info(f"    - Berths: {self.stats['berths']}")
        logger.info(f"    - Vessels: {self.stats['vessels']}")
        logger.info(f"    - Pilots: {self.stats['pilots']}")
        logger.info(f"    - Tugboats: {self.stats['tugboats']}")
        logger.info(f"    - Channels: {self.stats['channels']}")
        logger.info(f"    - Anchorages: {self.stats['anchorages']}")
        logger.info(f"    - Vessel Calls: {self.stats['vessel_calls']}")
        logger.info(f"  Relationships: ~{self.stats['relationships']}")
        logger.info("=" * 60)
        
        return self.stats


class Neo4jQueryEngine:
    """
    Execute graph queries for SmartBerth RAG pipeline.
    Provides common query patterns for berth planning domain.
    """
    
    def __init__(self, config: Optional[Neo4jConfig] = None):
        self.config = config or Neo4jConfig()
        self._driver: Optional[Driver] = None
    
    @property
    def driver(self) -> Optional[Driver]:
        if not NEO4J_AVAILABLE:
            return None
        
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.config.uri,
                    auth=(self.config.username, self.config.password)
                )
                self._driver.verify_connectivity()
            except Exception as e:
                logger.error(f"Neo4j connection failed: {e}")
                self._driver = None
        
        return self._driver
    
    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def find_compatible_berths(
        self,
        vessel_type: str = None,
        min_loa: float = None,
        min_depth: float = None,
        port_code: str = None
    ) -> List[Dict]:
        """Find berths compatible with vessel requirements"""
        if not self.driver:
            return []
        
        conditions = []
        params = {}
        
        if vessel_type:
            conditions.append("vt.name = $vessel_type")
            params["vessel_type"] = vessel_type
        if min_loa:
            conditions.append("b.maxLOA >= $min_loa")
            params["min_loa"] = min_loa
        if min_depth:
            conditions.append("b.depth >= $min_depth")
            params["min_depth"] = min_depth
        if port_code:
            conditions.append("p.portCode = $port_code")
            params["port_code"] = port_code
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        
        cypher = f"""
        MATCH (b:Berth)-[:BELONGS_TO]->(t:Terminal)-[:LOCATED_IN]->(p:Port)
        OPTIONAL MATCH (b)-[:IS_TYPE]->(bt:BerthType)<-[:COMPATIBLE_WITH]-(vt:VesselType)
        WHERE {where_clause}
        RETURN b.berthCode AS berthCode,
               b.berthType AS berthType,
               b.maxLOA AS maxLOA,
               b.maxDraft AS maxDraft,
               b.depth AS depth,
               t.terminalName AS terminal,
               p.portCode AS port,
               p.portName AS portName
        ORDER BY b.maxLOA DESC
        LIMIT 20
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]
    
    def get_port_resources(self, port_code: str) -> Dict:
        """Get all resources available at a port"""
        if not self.driver:
            return {}
        
        cypher = """
        MATCH (p:Port {portCode: $port_code})
        OPTIONAL MATCH (t:Terminal)-[:LOCATED_IN]->(p)
        OPTIONAL MATCH (b:Berth)-[:BELONGS_TO]->(t)
        OPTIONAL MATCH (pi:Pilot)-[:SERVES]->(p)
        OPTIONAL MATCH (tug:Tugboat)-[:OPERATES_FROM]->(p)
        OPTIONAL MATCH (ch:Channel)-[:ACCESS_TO]->(p)
        OPTIONAL MATCH (a:Anchorage)-[:ANCHORAGE_FOR]->(p)
        RETURN p.portName AS portName,
               COUNT(DISTINCT t) AS terminals,
               COUNT(DISTINCT b) AS berths,
               COUNT(DISTINCT pi) AS pilots,
               COUNT(DISTINCT tug) AS tugboats,
               COUNT(DISTINCT ch) AS channels,
               COUNT(DISTINCT a) AS anchorages
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(cypher, port_code=port_code)
            record = result.single()
            return dict(record) if record else {}
    
    def find_vessel_history(
        self,
        vessel_name: str = None,
        imo_number: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """Find vessel call history"""
        if not self.driver:
            return []
        
        if vessel_name:
            match_clause = "MATCH (v:Vessel) WHERE v.vesselName CONTAINS $search"
            params = {"search": vessel_name, "limit": limit}
        elif imo_number:
            match_clause = "MATCH (v:Vessel {imoNumber: $search})"
            params = {"search": imo_number, "limit": limit}
        else:
            return []
        
        cypher = f"""
        {match_clause}
        OPTIONAL MATCH (vc:VesselCall)-[:CALLED_AT]->(p:Port)
        WHERE vc.vesselName = v.vesselName OR vc.imoNumber = v.imoNumber
        OPTIONAL MATCH (vc)-[:ASSIGNED_TO]->(b:Berth)
        RETURN v.vesselName AS vessel,
               v.imoNumber AS imo,
               v.vesselType AS type,
               v.loa AS loa,
               p.portCode AS port,
               b.berthCode AS berth,
               vc.waitingTimeHours AS waitingTime
        ORDER BY vc.eta DESC
        LIMIT $limit
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]
    
    def get_berth_utilization(self, port_code: str = None) -> List[Dict]:
        """Get berth utilization statistics from call history"""
        if not self.driver:
            return []
        
        port_filter = "WHERE p.portCode = $port_code" if port_code else ""
        params = {"port_code": port_code} if port_code else {}
        
        cypher = f"""
        MATCH (b:Berth)-[:BELONGS_TO]->(t:Terminal)-[:LOCATED_IN]->(p:Port)
        {port_filter}
        OPTIONAL MATCH (vc:VesselCall)-[:ASSIGNED_TO]->(b)
        RETURN b.berthCode AS berthCode,
               b.berthType AS berthType,
               t.terminalName AS terminal,
               p.portCode AS port,
               COUNT(vc) AS callCount,
               AVG(vc.dwellTimeHours) AS avgDwellTime,
               AVG(vc.waitingTimeHours) AS avgWaitingTime
        ORDER BY callCount DESC
        LIMIT 50
        """
        
        with self.driver.session(database=self.config.database) as session:
            result = session.run(cypher, **params)
            return [dict(record) for record in result]
    
    def natural_language_to_cypher(self, query: str, llm_caller=None) -> Tuple[str, List[Dict]]:
        """Convert natural language query to Cypher and execute"""
        if not self.driver or not llm_caller:
            return "", []
        
        # Prompt for Cypher generation
        prompt = f"""Convert this natural language query to Neo4j Cypher.

Schema:
- (:Port {{portId, portCode, portName, country}})
- (:Terminal {{terminalId, terminalCode, terminalName, terminalType}})-[:LOCATED_IN]->(:Port)
- (:Berth {{berthId, berthCode, berthType, maxLOA, maxDraft, depth}})-[:BELONGS_TO]->(:Terminal)
- (:Vessel {{vesselId, imoNumber, vesselName, vesselType, loa, beam, draft}})
- (:Pilot {{pilotId, pilotName, pilotType}})-[:SERVES]->(:Port)
- (:Tugboat {{tugId, tugName, tugType, bollardPull}})-[:OPERATES_FROM]->(:Port)
- (:Channel {{channelId, channelName, maxVesselLOA}})-[:ACCESS_TO]->(:Port)
- (:VesselCall {{callId, eta, waitingTimeHours}})-[:CALLED_AT]->(:Port), -[:ASSIGNED_TO]->(:Berth)

Query: {query}

Output only the Cypher query, no explanation:"""
        
        cypher = llm_caller(prompt)
        
        # Clean up response
        if "```" in cypher:
            cypher = cypher.split("```")[1].strip()
            if cypher.startswith("cypher"):
                cypher = cypher[6:].strip()
        
        # Execute query
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(cypher)
                return cypher, [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Cypher execution failed: {e}")
            return cypher, []
    
    def get_graph_context(self, entity_name: str, depth: int = 2) -> str:
        """Get context around an entity for RAG"""
        if not self.driver:
            return ""
        
        cypher = """
        MATCH (n)
        WHERE any(prop IN keys(n) WHERE n[prop] CONTAINS $entity)
        CALL apoc.path.subgraphAll(n, {maxLevel: $depth})
        YIELD nodes, relationships
        UNWIND nodes AS node
        RETURN DISTINCT labels(node) AS labels, 
               node.name AS name,
               node.portCode AS portCode,
               node.berthCode AS berthCode,
               node.vesselName AS vesselName
        LIMIT 50
        """
        
        try:
            with self.driver.session(database=self.config.database) as session:
                result = session.run(cypher, entity=entity_name, depth=depth)
                records = [dict(r) for r in result]
                
                if not records:
                    return f"No graph context found for: {entity_name}"
                
                context_parts = []
                for r in records:
                    labels = r.get("labels", [])
                    name = r.get("name") or r.get("portCode") or r.get("berthCode") or r.get("vesselName")
                    if name:
                        context_parts.append(f"- {labels[0] if labels else 'Entity'}: {name}")
                
                return f"Graph context for '{entity_name}':\n" + "\n".join(context_parts)
        except Exception as e:
            logger.debug(f"Graph context query failed (APOC may not be installed): {e}")
            return f"Graph context search for: {entity_name}"


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point for loading training data to Neo4j"""
    import sys
    
    # Determine paths - relative to ai-service folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    training_data_path = os.path.join(script_dir, "Train_Database")
    
    print("SmartBerth AI - Neo4j Graph Loader")
    print("=" * 40)
    print(f"Training Data: {training_data_path}")
    print()
    
    # Check if Neo4j is available
    if not NEO4J_AVAILABLE:
        print("ERROR: Neo4j driver not installed.")
        print("Install with: pip install neo4j")
        sys.exit(1)
    
    # Load data
    loader = TrainingDataGraphLoader(training_data_path)
    
    try:
        stats = loader.load_all()
        
        if stats["ports"] == 0:
            print("\nWARNING: No data loaded. Check Neo4j connection.")
            print(f"  URI: {loader.config.uri}")
            print(f"  User: {loader.config.username}")
        else:
            print("\n✓ Graph loaded successfully!")
            
            # Test query
            print("\nTesting query engine...")
            engine = Neo4jQueryEngine()
            
            # Test compatible berths query
            berths = engine.find_compatible_berths(min_loa=200, port_code="SGSIN")
            print(f"  Found {len(berths)} berths compatible with LOA>200m at SGSIN")
            
            # Test port resources
            resources = engine.get_port_resources("SGSIN")
            if resources:
                print(f"  Port of Singapore resources: {resources}")
            
            engine.close()
            
    finally:
        loader.close()


if __name__ == "__main__":
    main()
