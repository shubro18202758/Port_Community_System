"""
SmartBerth AI Service - Database Connection
Handles SQL Server database operations
"""

import pyodbc
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from config import get_settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """SQL Server database service for SmartBerth AI"""
    
    def __init__(self):
        self.settings = get_settings()
        self._connection_string = self.settings.db_connection_string
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = pyodbc.connect(self._connection_string)
            yield conn
        except pyodbc.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
    
    def execute_scalar(self, query: str, params: tuple = ()) -> Any:
        """Execute query and return single value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row[0] if row else None
    
    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    # ==================== VESSEL OPERATIONS ====================
    
    def get_all_vessels(self) -> List[Dict[str, Any]]:
        """Get all vessels"""
        query = """
            SELECT VesselId, VesselName, IMO, MMSI, VesselType, 
                   LOA, Beam, Draft, GrossTonnage, CargoType, 
                   CargoVolume, Priority, CreatedAt, UpdatedAt
            FROM VESSELS
            ORDER BY VesselName
        """
        return self.execute_query(query)
    
    def get_vessel_by_id(self, vessel_id: int) -> Optional[Dict[str, Any]]:
        """Get vessel by ID"""
        query = """
            SELECT VesselId, VesselName, IMO, MMSI, VesselType, 
                   LOA, Beam, Draft, GrossTonnage, CargoType, 
                   CargoVolume, Priority, CreatedAt, UpdatedAt
            FROM VESSELS WHERE VesselId = ?
        """
        results = self.execute_query(query, (vessel_id,))
        return results[0] if results else None
    
    def get_vessels_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get vessels by schedule status"""
        query = """
            SELECT v.VesselId, v.VesselName, v.IMO, v.MMSI, v.VesselType,
                   v.LOA, v.Beam, v.Draft, vs.Status, vs.ETA, vs.PredictedETA,
                   vs.BerthId, b.BerthName
            FROM VESSELS v
            INNER JOIN VESSEL_SCHEDULE vs ON v.VesselId = vs.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.Status = ?
            ORDER BY vs.ETA
        """
        return self.execute_query(query, (status,))
    
    # ==================== BERTH OPERATIONS ====================
    
    def get_all_berths(self) -> List[Dict[str, Any]]:
        """Get all berths with terminal info"""
        query = """
            SELECT b.BerthId, b.BerthName, b.BerthCode, b.TerminalId,
                   t.TerminalName, b.Length AS MaxLOA, b.Depth AS MaxBeam,
                   b.MaxDraft, b.BerthType, 
                   CONCAT('Cranes: ', b.NumberOfCranes, ', Bollards: ', b.BollardCount) AS Equipment,
                   b.IsActive, b.Latitude, b.Longitude
            FROM BERTHS b
            INNER JOIN TERMINALS t ON b.TerminalId = t.TerminalId
            ORDER BY t.TerminalName, b.BerthName
        """
        return self.execute_query(query)
    
    def get_available_berths(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """Get berths available in a time window"""
        query = """
            SELECT b.BerthId, b.BerthName, b.BerthCode, b.Length AS MaxLOA, 
                   b.Depth AS MaxBeam, b.MaxDraft, b.BerthType, t.TerminalName
            FROM BERTHS b
            INNER JOIN TERMINALS t ON b.TerminalId = t.TerminalId
            WHERE b.IsActive = 1
            AND b.BerthId NOT IN (
                SELECT vs.BerthId FROM VESSEL_SCHEDULE vs
                WHERE vs.BerthId IS NOT NULL
                AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
                AND (
                    (vs.ETA <= ? AND COALESCE(vs.ATD, vs.ETD) >= ?)
                    OR (vs.ETA <= ? AND COALESCE(vs.ATD, vs.ETD) >= ?)
                    OR (vs.ETA >= ? AND COALESCE(vs.ATD, vs.ETD) <= ?)
                )
            )
            ORDER BY t.TerminalName, b.BerthName
        """
        return self.execute_query(query, (end_time, start_time, start_time, start_time, start_time, end_time))
    
    # ==================== SCHEDULE OPERATIONS ====================
    
    def get_vessel_schedule(self, vessel_id: int) -> Optional[Dict[str, Any]]:
        """Get the current/latest schedule for a vessel"""
        query = """
            SELECT TOP 1 vs.ScheduleId, vs.VesselId, v.VesselName, v.VesselType,
                   vs.BerthId, b.BerthName, vs.ETA, vs.PredictedETA, vs.ATA,
                   vs.ETD, vs.ATD, vs.Status, v.Priority,
                   v.LOA, v.Beam, v.Draft, v.CargoType, v.CargoVolume,
                   vs.DwellTime, vs.WaitingTime, vs.OptimizationScore
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.VesselId = ?
            ORDER BY vs.ETA DESC
        """
        results = self.execute_query(query, (vessel_id,))
        return results[0] if results else None
    
    def get_schedules_in_range(self, start_time: str, end_time: str) -> List[Dict[str, Any]]:
        """Get all schedules within a time range"""
        query = """
            SELECT vs.ScheduleId, vs.VesselId, v.VesselName, v.VesselType,
                   vs.BerthId, b.BerthName, vs.ETA, vs.PredictedETA, vs.ATA,
                   vs.ETD, vs.ATD, vs.Status, v.Priority,
                   v.LOA, v.Beam, v.Draft, v.CargoType
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.ETA BETWEEN ? AND ?
               OR (vs.ETA <= ? AND COALESCE(vs.ATD, vs.ETD) >= ?)
            ORDER BY vs.ETA
        """
        return self.execute_query(query, (start_time, end_time, end_time, start_time))
    
    def get_active_schedules(self) -> List[Dict[str, Any]]:
        """Get all active vessel schedules"""
        query = """
            SELECT vs.ScheduleId, vs.VesselId, v.VesselName, v.VesselType,
                   vs.BerthId, b.BerthName, vs.ETA, vs.PredictedETA, vs.ATA,
                   vs.ETD, vs.ATD, vs.Status, v.Priority,
                   v.LOA, v.Beam, v.Draft, v.CargoType,
                   vs.DwellTime, vs.WaitingTime, vs.OptimizationScore
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
            ORDER BY vs.ETA
        """
        return self.execute_query(query)
    
    def get_schedule_by_id(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """Get schedule by ID with full details"""
        query = """
            SELECT vs.ScheduleId, vs.VesselId, v.VesselName, v.VesselType,
                   vs.BerthId, b.BerthName, b.Length AS MaxLOA, b.Depth AS MaxBeam, b.MaxDraft,
                   vs.ETA, vs.PredictedETA, vs.ATA, vs.ETD, vs.ATD, 
                   vs.Status, v.Priority, v.LOA, v.Beam, v.Draft,
                   v.CargoType, v.CargoVolume, t.TerminalName
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            LEFT JOIN TERMINALS t ON b.TerminalId = t.TerminalId
            WHERE vs.ScheduleId = ?
        """
        results = self.execute_query(query, (schedule_id,))
        return results[0] if results else None
    
    # ==================== AIS DATA ====================
    
    def get_latest_ais_for_vessel(self, vessel_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get latest AIS positions for a vessel"""
        query = f"""
            SELECT TOP {limit} AISId, VesselId, MMSI, Latitude, Longitude,
                   Speed, Course, Heading, NavigationStatus, RecordedAt
            FROM AIS_DATA
            WHERE VesselId = ?
            ORDER BY RecordedAt DESC
        """
        return self.execute_query(query, (vessel_id,))
    
    # ==================== WEATHER & TIDAL ====================
    
    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """Get current weather conditions"""
        query = """
            SELECT TOP 1 WeatherId, WindSpeed, WindDirection, Visibility,
                   WaveHeight, Temperature, WeatherCondition AS Conditions, 
                   Precipitation, IsAlert, RecordedAt
            FROM WEATHER_DATA
            ORDER BY RecordedAt DESC
        """
        results = self.execute_query(query)
        return results[0] if results else None
    
    def get_tidal_windows(self, from_time: str, until_time: str) -> List[Dict[str, Any]]:
        """Get tidal data for a time range"""
        query = """
            SELECT TidalId, TideType, Height AS TideHeight, TideTime, 
                   CreatedAt AS RecordedAt
            FROM TIDAL_DATA
            WHERE TideTime BETWEEN ? AND ?
            ORDER BY TideTime
        """
        return self.execute_query(query, (from_time, until_time))
    
    # ==================== RESOURCES ====================
    
    def get_available_resources(self, resource_type: str, at_time: str) -> List[Dict[str, Any]]:
        """Get available resources of a type at a given time"""
        query = """
            SELECT r.ResourceId, r.ResourceName, r.ResourceType, 
                   r.Capacity, r.IsAvailable
            FROM RESOURCES r
            WHERE r.ResourceType = ?
            AND r.IsAvailable = 1
            AND r.ResourceId NOT IN (
                SELECT ra.ResourceId FROM RESOURCE_ALLOCATION ra
                WHERE ra.AllocatedFrom <= ? AND ra.AllocatedTo >= ?
            )
        """
        return self.execute_query(query, (resource_type, at_time, at_time))
    
    # ==================== CONFLICTS ====================
    
    def get_active_conflicts(self) -> List[Dict[str, Any]]:
        """Get all unresolved conflicts"""
        query = """
            SELECT c.ConflictId, c.ConflictType, c.Severity, c.Description,
                   c.ScheduleId1, c.ScheduleId2, c.DetectedAt, c.Status,
                   vs1.VesselId as Vessel1Id, v1.VesselName as Vessel1Name,
                   vs2.VesselId as Vessel2Id, v2.VesselName as Vessel2Name
            FROM CONFLICTS c
            LEFT JOIN VESSEL_SCHEDULE vs1 ON c.ScheduleId1 = vs1.ScheduleId
            LEFT JOIN VESSELS v1 ON vs1.VesselId = v1.VesselId
            LEFT JOIN VESSEL_SCHEDULE vs2 ON c.ScheduleId2 = vs2.ScheduleId
            LEFT JOIN VESSELS v2 ON vs2.VesselId = v2.VesselId
            WHERE c.Status = 'Detected'
            ORDER BY c.Severity DESC, c.DetectedAt
        """
        return self.execute_query(query)
    
    # ==================== KNOWLEDGE BASE ====================
    
    def get_knowledge_base_entries(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get knowledge base entries for RAG"""
        if category:
            query = """
                SELECT KnowledgeId, Title, Content, DocumentType, Metadata, CreatedAt
                FROM KNOWLEDGE_BASE
                WHERE DocumentType = ?
                ORDER BY Title
            """
            return self.execute_query(query, (category,))
        else:
            query = """
                SELECT KnowledgeId, Title, Content, DocumentType, Metadata, CreatedAt
                FROM KNOWLEDGE_BASE
                ORDER BY DocumentType, Title
            """
            return self.execute_query(query)

    # ==================== WEATHER OPERATIONS ====================

    def get_weather_for_vessel_route(
        self,
        vessel_id: int,
        schedule_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all weather forecasts along vessel route (port + waypoints)

        Args:
            vessel_id: Vessel ID
            schedule_id: Schedule ID

        Returns:
            List of weather forecasts ordered by waypoint sequence
        """
        query = """
            SELECT
                ForecastId,
                LocationType,
                LocationName,
                Latitude,
                Longitude,
                WaypointSequence,
                ForecastFor,
                FetchedAt,
                WindSpeed,
                WindDirection,
                WindGust,
                Visibility,
                WaveHeight,
                Temperature,
                Precipitation,
                WeatherCondition,
                WeatherImpactFactor,
                IsOperationalAlert,
                AlertLevel
            FROM WEATHER_FORECAST
            WHERE VesselId = ?
              AND ScheduleId = ?
              AND ExpiresAt > GETUTCDATE()
              AND IsActive = 1
            ORDER BY
                CASE WHEN LocationType = 'PORT' THEN 999 ELSE WaypointSequence END
        """
        return self.execute_query(query, (vessel_id, schedule_id))

    def get_port_weather_forecast(
        self,
        port_id: int,
        hours_ahead: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get weather forecast for a port location

        Args:
            port_id: Port ID
            hours_ahead: Number of hours to forecast (default: 24)

        Returns:
            List of weather forecasts
        """
        query = """
            SELECT TOP 1
                wf.ForecastId,
                wf.LocationType,
                wf.LocationName,
                wf.Latitude,
                wf.Longitude,
                wf.ForecastFor,
                wf.FetchedAt,
                wf.WindSpeed,
                wf.WindDirection,
                wf.WindGust,
                wf.Visibility,
                wf.WaveHeight,
                wf.Temperature,
                wf.Precipitation,
                wf.WeatherCondition,
                wf.WeatherImpactFactor,
                wf.IsOperationalAlert,
                wf.AlertLevel
            FROM WEATHER_FORECAST wf
            INNER JOIN PORTS p ON wf.LocationId = p.PortId
            WHERE wf.LocationType = 'PORT'
              AND p.PortId = ?
              AND wf.ExpiresAt > GETUTCDATE()
              AND wf.IsActive = 1
            ORDER BY wf.FetchedAt DESC
        """
        return self.execute_query(query, (port_id,))

    def get_route_weather_impact_factor(
        self,
        vessel_id: int,
        schedule_id: int
    ) -> float:
        """
        Calculate average weather impact factor across entire vessel route

        Args:
            vessel_id: Vessel ID
            schedule_id: Schedule ID

        Returns:
            Average impact factor (0.5-1.0)
        """
        query = """
            SELECT AVG(WeatherImpactFactor) as AvgImpactFactor
            FROM WEATHER_FORECAST
            WHERE VesselId = ?
              AND ScheduleId = ?
              AND ExpiresAt > GETUTCDATE()
              AND IsActive = 1
              AND WeatherImpactFactor IS NOT NULL
        """
        result = self.execute_scalar(query, (vessel_id, schedule_id))
        return float(result) if result else 1.0

    def check_weather_alerts_for_vessel(
        self,
        vessel_id: int,
        schedule_id: int
    ) -> Dict[str, Any]:
        """
        Check if vessel has any weather-related alerts

        Args:
            vessel_id: Vessel ID
            schedule_id: Schedule ID

        Returns:
            Dict with alert information
        """
        query = """
            SELECT
                MAX(CASE WHEN AlertLevel = 'CRITICAL' THEN 1 ELSE 0 END) as HasCriticalAlert,
                MAX(CASE WHEN AlertLevel = 'WARNING' THEN 1 ELSE 0 END) as HasWarningAlert,
                COUNT(*) as TotalForecasts,
                AVG(WeatherImpactFactor) as AvgImpactFactor,
                MAX(FetchedAt) as LastUpdate
            FROM WEATHER_FORECAST
            WHERE VesselId = ?
              AND ScheduleId = ?
              AND ExpiresAt > GETUTCDATE()
              AND IsActive = 1
        """
        results = self.execute_query(query, (vessel_id, schedule_id))
        return results[0] if results else {
            "HasCriticalAlert": 0,
            "HasWarningAlert": 0,
            "TotalForecasts": 0,
            "AvgImpactFactor": 1.0,
            "LastUpdate": None
        }
# Global database service instance
db_service = DatabaseService()


def get_db_service() -> DatabaseService:
    """Get the global database service instance"""
    return db_service
