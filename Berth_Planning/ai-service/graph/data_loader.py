"""
SmartBerth AI - Neo4j Data Loader
Loads vessel, berth, schedule data from SQL Server into Neo4j graph database
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from functools import lru_cache

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j package not installed. Install with: pip install neo4j")

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    print("Warning: pyodbc package not installed. Install with: pip install pyodbc")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration"""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "smartberth123"
    database: str = "neo4j"


@dataclass
class SQLServerConfig:
    """SQL Server connection configuration"""
    server: str = "(localdb)\\MSSQLLocalDB"
    database: str = "BerthPlanning"
    driver: str = "{ODBC Driver 17 for SQL Server}"


class Neo4jDataLoader:
    """
    Loads data from SQL Server into Neo4j graph database.
    Creates nodes and relationships for berth planning domain.
    """
    
    def __init__(
        self, 
        neo4j_config: Optional[Neo4jConfig] = None,
        sql_config: Optional[SQLServerConfig] = None
    ):
        self.neo4j_config = neo4j_config or Neo4jConfig()
        self.sql_config = sql_config or SQLServerConfig()
        self._driver: Optional[Driver] = None
        self._sql_conn = None
        
    @property
    def driver(self) -> Optional[Driver]:
        """Lazy initialization of Neo4j driver"""
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j driver not available")
            return None
            
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.neo4j_config.uri,
                    auth=(self.neo4j_config.username, self.neo4j_config.password)
                )
                # Test connection
                self._driver.verify_connectivity()
                logger.info(f"Connected to Neo4j at {self.neo4j_config.uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                self._driver = None
        return self._driver
    
    @property
    def sql_connection(self):
        """Lazy initialization of SQL Server connection"""
        if not PYODBC_AVAILABLE:
            logger.error("pyodbc not available")
            return None
            
        if self._sql_conn is None:
            try:
                conn_str = (
                    f"DRIVER={self.sql_config.driver};"
                    f"SERVER={self.sql_config.server};"
                    f"DATABASE={self.sql_config.database};"
                    "Trusted_Connection=yes;"
                )
                self._sql_conn = pyodbc.connect(conn_str)
                logger.info(f"Connected to SQL Server: {self.sql_config.server}")
            except Exception as e:
                logger.error(f"Failed to connect to SQL Server: {e}")
                self._sql_conn = None
        return self._sql_conn
    
    def close(self):
        """Close all connections"""
        if self._driver:
            self._driver.close()
            self._driver = None
        if self._sql_conn:
            self._sql_conn.close()
            self._sql_conn = None
    
    def clear_graph(self):
        """Clear all nodes and relationships from the graph"""
        if not self.driver:
            return False
            
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared all nodes and relationships from graph")
        return True
    
    def create_constraints(self):
        """Create unique constraints for node IDs"""
        if not self.driver:
            return False
            
        constraints = [
            "CREATE CONSTRAINT vessel_id IF NOT EXISTS FOR (v:Vessel) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT berth_id IF NOT EXISTS FOR (b:Berth) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT terminal_id IF NOT EXISTS FOR (t:Terminal) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT port_id IF NOT EXISTS FOR (p:Port) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT schedule_id IF NOT EXISTS FOR (s:Schedule) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT pilot_id IF NOT EXISTS FOR (p:Pilot) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT tugboat_id IF NOT EXISTS FOR (t:Tugboat) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT channel_id IF NOT EXISTS FOR (c:Channel) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT anchorage_id IF NOT EXISTS FOR (a:Anchorage) REQUIRE a.id IS UNIQUE",
        ]
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {e}")
        
        logger.info("Created graph constraints")
        return True
    
    def _fetch_sql_data(self, query: str) -> List[Dict[str, Any]]:
        """Fetch data from SQL Server"""
        if not self.sql_connection:
            return []
            
        cursor = self.sql_connection.cursor()
        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def load_ports(self) -> int:
        """Load Port nodes"""
        query = """
        SELECT Port_ID, Port_Name, Port_Code, Country, Latitude, Longitude,
               Time_Zone, Port_Type, Operational_Status
        FROM Ports
        """
        ports = self._fetch_sql_data(query)
        
        if not self.driver or not ports:
            return 0
            
        cypher = """
        UNWIND $ports AS port
        MERGE (p:Port {id: port.Port_ID})
        SET p.name = port.Port_Name,
            p.code = port.Port_Code,
            p.country = port.Country,
            p.latitude = port.Latitude,
            p.longitude = port.Longitude,
            p.timezone = port.Time_Zone,
            p.type = port.Port_Type,
            p.status = port.Operational_Status
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, ports=ports)
        
        logger.info(f"Loaded {len(ports)} Port nodes")
        return len(ports)
    
    def load_terminals(self) -> int:
        """Load Terminal nodes and relationships to Ports"""
        query = """
        SELECT Terminal_ID, Terminal_Name, Port_ID, Terminal_Type,
               Operational_Status, Max_Vessel_LOA, Max_Vessel_Beam,
               Max_Vessel_Draft, Has_Container_Cranes, Has_Bulk_Equipment,
               Has_Tanker_Equipment
        FROM Terminals
        """
        terminals = self._fetch_sql_data(query)
        
        if not self.driver or not terminals:
            return 0
            
        cypher = """
        UNWIND $terminals AS t
        MERGE (term:Terminal {id: t.Terminal_ID})
        SET term.name = t.Terminal_Name,
            term.type = t.Terminal_Type,
            term.status = t.Operational_Status,
            term.max_loa = t.Max_Vessel_LOA,
            term.max_beam = t.Max_Vessel_Beam,
            term.max_draft = t.Max_Vessel_Draft,
            term.has_container_cranes = t.Has_Container_Cranes,
            term.has_bulk_equipment = t.Has_Bulk_Equipment,
            term.has_tanker_equipment = t.Has_Tanker_Equipment
        WITH term, t
        MATCH (p:Port {id: t.Port_ID})
        MERGE (term)-[:LOCATED_AT]->(p)
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, terminals=terminals)
        
        logger.info(f"Loaded {len(terminals)} Terminal nodes")
        return len(terminals)
    
    def load_berths(self) -> int:
        """Load Berth nodes and relationships to Terminals"""
        query = """
        SELECT Berth_ID, Berth_Name, Terminal_ID, Berth_Type,
               Berth_Length, Max_Vessel_LOA, Max_Vessel_Beam,
               Water_Depth, Max_Draft, Status,
               Has_Shore_Power, Has_Fresh_Water, Has_Bunkering,
               Cargo_Types_Handled
        FROM Berths
        """
        berths = self._fetch_sql_data(query)
        
        if not self.driver or not berths:
            return 0
            
        cypher = """
        UNWIND $berths AS b
        MERGE (berth:Berth {id: b.Berth_ID})
        SET berth.name = b.Berth_Name,
            berth.type = b.Berth_Type,
            berth.length = b.Berth_Length,
            berth.max_loa = b.Max_Vessel_LOA,
            berth.max_beam = b.Max_Vessel_Beam,
            berth.water_depth = b.Water_Depth,
            berth.max_draft = b.Max_Draft,
            berth.status = b.Status,
            berth.has_shore_power = b.Has_Shore_Power,
            berth.has_fresh_water = b.Has_Fresh_Water,
            berth.has_bunkering = b.Has_Bunkering,
            berth.cargo_types = b.Cargo_Types_Handled
        WITH berth, b
        MATCH (t:Terminal {id: b.Terminal_ID})
        MERGE (berth)-[:BELONGS_TO]->(t)
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, berths=berths)
        
        logger.info(f"Loaded {len(berths)} Berth nodes")
        return len(berths)
    
    def load_vessels(self) -> int:
        """Load Vessel nodes"""
        query = """
        SELECT Vessel_ID, IMO_Number, Vessel_Name, Vessel_Type,
               Flag_State, LOA, Beam, Max_Draft, Gross_Tonnage,
               DWT, Year_Built, Call_Sign, MMSI
        FROM Vessels
        """
        vessels = self._fetch_sql_data(query)
        
        if not self.driver or not vessels:
            return 0
            
        cypher = """
        UNWIND $vessels AS v
        MERGE (vessel:Vessel {id: v.Vessel_ID})
        SET vessel.imo = v.IMO_Number,
            vessel.name = v.Vessel_Name,
            vessel.type = v.Vessel_Type,
            vessel.flag = v.Flag_State,
            vessel.loa = v.LOA,
            vessel.beam = v.Beam,
            vessel.draft = v.Max_Draft,
            vessel.gross_tonnage = v.Gross_Tonnage,
            vessel.dwt = v.DWT,
            vessel.year_built = v.Year_Built,
            vessel.call_sign = v.Call_Sign,
            vessel.mmsi = v.MMSI
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, vessels=vessels)
        
        logger.info(f"Loaded {len(vessels)} Vessel nodes")
        return len(vessels)
    
    def load_schedules(self) -> int:
        """Load Schedule nodes and relationships"""
        query = """
        SELECT Schedule_ID, Vessel_ID, Berth_ID, Port_ID,
               ETA, ETD, ATA, ATD, Status,
               Cargo_Type, Cargo_Quantity, Priority_Level
        FROM Vessel_Schedule
        """
        schedules = self._fetch_sql_data(query)
        
        if not self.driver or not schedules:
            return 0
        
        # Convert datetime objects to strings for Neo4j
        for s in schedules:
            for key in ['ETA', 'ETD', 'ATA', 'ATD']:
                if s.get(key) and isinstance(s[key], datetime):
                    s[key] = s[key].isoformat()
            
        cypher = """
        UNWIND $schedules AS s
        MERGE (schedule:Schedule {id: s.Schedule_ID})
        SET schedule.eta = s.ETA,
            schedule.etd = s.ETD,
            schedule.ata = s.ATA,
            schedule.atd = s.ATD,
            schedule.status = s.Status,
            schedule.cargo_type = s.Cargo_Type,
            schedule.cargo_quantity = s.Cargo_Quantity,
            schedule.priority = s.Priority_Level
        WITH schedule, s
        MATCH (v:Vessel {id: s.Vessel_ID})
        MERGE (v)-[:SCHEDULED_FOR]->(schedule)
        WITH schedule, s
        MATCH (b:Berth {id: s.Berth_ID})
        MERGE (schedule)-[:ASSIGNED_TO]->(b)
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, schedules=schedules)
        
        logger.info(f"Loaded {len(schedules)} Schedule nodes")
        return len(schedules)
    
    def load_pilots(self) -> int:
        """Load Pilot nodes"""
        query = """
        SELECT Pilot_ID, Pilot_Name, License_Number, Port_ID,
               Certification_Level, Max_Vessel_LOA, Max_Vessel_Beam,
               Max_Vessel_Draft, Status, Languages
        FROM Pilots
        """
        pilots = self._fetch_sql_data(query)
        
        if not self.driver or not pilots:
            return 0
            
        cypher = """
        UNWIND $pilots AS p
        MERGE (pilot:Pilot {id: p.Pilot_ID})
        SET pilot.name = p.Pilot_Name,
            pilot.license = p.License_Number,
            pilot.certification = p.Certification_Level,
            pilot.max_loa = p.Max_Vessel_LOA,
            pilot.max_beam = p.Max_Vessel_Beam,
            pilot.max_draft = p.Max_Vessel_Draft,
            pilot.status = p.Status,
            pilot.languages = p.Languages
        WITH pilot, p
        MATCH (port:Port {id: p.Port_ID})
        MERGE (pilot)-[:OPERATES_AT]->(port)
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, pilots=pilots)
        
        logger.info(f"Loaded {len(pilots)} Pilot nodes")
        return len(pilots)
    
    def load_tugboats(self) -> int:
        """Load Tugboat nodes"""
        query = """
        SELECT Tugboat_ID, Tugboat_Name, Port_ID, Bollard_Pull,
               Horsepower, Type, Status, Max_Vessel_Size
        FROM Tugboats
        """
        tugboats = self._fetch_sql_data(query)
        
        if not self.driver or not tugboats:
            return 0
            
        cypher = """
        UNWIND $tugboats AS t
        MERGE (tug:Tugboat {id: t.Tugboat_ID})
        SET tug.name = t.Tugboat_Name,
            tug.bollard_pull = t.Bollard_Pull,
            tug.horsepower = t.Horsepower,
            tug.type = t.Type,
            tug.status = t.Status,
            tug.max_vessel_size = t.Max_Vessel_Size
        WITH tug, t
        MATCH (port:Port {id: t.Port_ID})
        MERGE (tug)-[:BASED_AT]->(port)
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, tugboats=tugboats)
        
        logger.info(f"Loaded {len(tugboats)} Tugboat nodes")
        return len(tugboats)
    
    def load_channels(self) -> int:
        """Load Channel nodes"""
        query = """
        SELECT Channel_ID, Channel_Name, Port_ID, Channel_Type,
               Length_NM, Width_M, Depth_M, Max_Vessel_LOA,
               Max_Vessel_Beam, Max_Vessel_Draft, One_Way_Traffic
        FROM Channels
        """
        channels = self._fetch_sql_data(query)
        
        if not self.driver or not channels:
            return 0
            
        cypher = """
        UNWIND $channels AS c
        MERGE (channel:Channel {id: c.Channel_ID})
        SET channel.name = c.Channel_Name,
            channel.type = c.Channel_Type,
            channel.length_nm = c.Length_NM,
            channel.width_m = c.Width_M,
            channel.depth_m = c.Depth_M,
            channel.max_loa = c.Max_Vessel_LOA,
            channel.max_beam = c.Max_Vessel_Beam,
            channel.max_draft = c.Max_Vessel_Draft,
            channel.one_way = c.One_Way_Traffic
        WITH channel, c
        MATCH (port:Port {id: c.Port_ID})
        MERGE (channel)-[:CONNECTS]->(port)
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, channels=channels)
        
        logger.info(f"Loaded {len(channels)} Channel nodes")
        return len(channels)
    
    def load_anchorages(self) -> int:
        """Load Anchorage nodes"""
        query = """
        SELECT Anchorage_ID, Anchorage_Name, Port_ID, Anchorage_Type,
               Latitude, Longitude, Depth_M, Capacity,
               Max_Vessel_LOA, Max_Vessel_Draft, Holding_Ground_Type
        FROM Anchorages
        """
        anchorages = self._fetch_sql_data(query)
        
        if not self.driver or not anchorages:
            return 0
            
        cypher = """
        UNWIND $anchorages AS a
        MERGE (anch:Anchorage {id: a.Anchorage_ID})
        SET anch.name = a.Anchorage_Name,
            anch.type = a.Anchorage_Type,
            anch.latitude = a.Latitude,
            anch.longitude = a.Longitude,
            anch.depth = a.Depth_M,
            anch.capacity = a.Capacity,
            anch.max_loa = a.Max_Vessel_LOA,
            anch.max_draft = a.Max_Vessel_Draft,
            anch.holding_ground = a.Holding_Ground_Type
        WITH anch, a
        MATCH (port:Port {id: a.Port_ID})
        MERGE (anch)-[:SERVES]->(port)
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, anchorages=anchorages)
        
        logger.info(f"Loaded {len(anchorages)} Anchorage nodes")
        return len(anchorages)
    
    def create_vessel_berth_compatibility(self):
        """Create COMPATIBLE_WITH relationships based on physical constraints"""
        if not self.driver:
            return 0
            
        cypher = """
        MATCH (v:Vessel), (b:Berth)
        WHERE v.loa <= b.max_loa 
          AND v.beam <= b.max_beam 
          AND v.draft <= b.max_draft
          AND b.status = 'Active'
        MERGE (v)-[r:COMPATIBLE_WITH]->(b)
        SET r.loa_margin = b.max_loa - v.loa,
            r.beam_margin = b.max_beam - v.beam,
            r.draft_margin = b.max_draft - v.draft
        RETURN count(r) as count
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            result = session.run(cypher)
            count = result.single()["count"]
        
        logger.info(f"Created {count} COMPATIBLE_WITH relationships")
        return count
    
    def create_historical_preference(self):
        """Create HISTORICALLY_USED relationships from vessel history"""
        query = """
        SELECT vh.Vessel_ID, vh.Berth_ID, COUNT(*) as visit_count,
               MAX(vh.Visit_Date) as last_visit
        FROM Vessel_History vh
        GROUP BY vh.Vessel_ID, vh.Berth_ID
        """
        history = self._fetch_sql_data(query)
        
        if not self.driver or not history:
            return 0
        
        # Convert datetime
        for h in history:
            if h.get('last_visit') and isinstance(h['last_visit'], datetime):
                h['last_visit'] = h['last_visit'].isoformat()
            
        cypher = """
        UNWIND $history AS h
        MATCH (v:Vessel {id: h.Vessel_ID})
        MATCH (b:Berth {id: h.Berth_ID})
        MERGE (v)-[r:HISTORICALLY_USED]->(b)
        SET r.visit_count = h.visit_count,
            r.last_visit = h.last_visit
        """
        
        with self.driver.session(database=self.neo4j_config.database) as session:
            session.run(cypher, history=history)
        
        logger.info(f"Created {len(history)} HISTORICALLY_USED relationships")
        return len(history)
    
    def load_all(self, clear_first: bool = True) -> Dict[str, int]:
        """Load all data from SQL Server into Neo4j"""
        results = {}
        
        if clear_first:
            self.clear_graph()
        
        self.create_constraints()
        
        # Load nodes
        results['ports'] = self.load_ports()
        results['terminals'] = self.load_terminals()
        results['berths'] = self.load_berths()
        results['vessels'] = self.load_vessels()
        results['schedules'] = self.load_schedules()
        results['pilots'] = self.load_pilots()
        results['tugboats'] = self.load_tugboats()
        results['channels'] = self.load_channels()
        results['anchorages'] = self.load_anchorages()
        
        # Create relationships
        results['compatibility'] = self.create_vessel_berth_compatibility()
        results['history'] = self.create_historical_preference()
        
        total = sum(results.values())
        logger.info(f"Loaded {total} total items into Neo4j")
        
        return results
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph"""
        if not self.driver:
            return {"error": "Neo4j not connected"}
            
        stats = {}
        
        # Count nodes by label
        node_query = """
        CALL db.labels() YIELD label
        CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as count', {})
        YIELD value
        RETURN label, value.count as count
        """
        
        # Fallback if APOC not available
        simple_query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(*) as count
        GROUP BY labels(n)[0]
        """
        
        try:
            with self.driver.session(database=self.neo4j_config.database) as session:
                result = session.run(simple_query)
                stats['nodes'] = {r['label']: r['count'] for r in result}
                
                # Count relationships
                rel_query = "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count"
                result = session.run(rel_query)
                stats['relationships'] = {r['type']: r['count'] for r in result}
                
                # Total counts
                stats['total_nodes'] = sum(stats['nodes'].values())
                stats['total_relationships'] = sum(stats['relationships'].values())
        except Exception as e:
            stats['error'] = str(e)
        
        return stats


@lru_cache()
def get_neo4j_loader() -> Neo4jDataLoader:
    """Get cached Neo4j data loader instance"""
    # Check for environment variables
    neo4j_config = Neo4jConfig(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "smartberth123"),
        database=os.getenv("NEO4J_DATABASE", "neo4j")
    )
    
    sql_config = SQLServerConfig(
        server=os.getenv("SQL_SERVER", "(localdb)\\MSSQLLocalDB"),
        database=os.getenv("SQL_DATABASE", "BerthPlanning")
    )
    
    return Neo4jDataLoader(neo4j_config, sql_config)


if __name__ == "__main__":
    print("=" * 60)
    print("SmartBerth AI - Neo4j Data Loader")
    print("=" * 60)
    
    loader = get_neo4j_loader()
    
    # Check connections
    print("\n📡 Testing connections...")
    
    if loader.driver:
        print("   ✓ Neo4j connected")
    else:
        print("   ✗ Neo4j not connected")
        print("   Tip: Make sure Neo4j is running on bolt://localhost:7687")
    
    if loader.sql_connection:
        print("   ✓ SQL Server connected")
    else:
        print("   ✗ SQL Server not connected")
    
    # Load data if both connected
    if loader.driver and loader.sql_connection:
        print("\n🔄 Loading data...")
        results = loader.load_all()
        
        print("\n📊 Load Results:")
        for entity, count in results.items():
            print(f"   {entity}: {count}")
        
        print("\n📈 Graph Statistics:")
        stats = loader.get_graph_stats()
        if 'nodes' in stats:
            print("   Nodes:")
            for label, count in stats['nodes'].items():
                print(f"      {label}: {count}")
            print("   Relationships:")
            for rel_type, count in stats['relationships'].items():
                print(f"      {rel_type}: {count}")
    
    loader.close()
    print("\n✅ Done")
