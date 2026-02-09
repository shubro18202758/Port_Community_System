"""
Weather Update Service
Main orchestrator for hourly weather data updates
Fetches weather for port + 5 waypoints along vessel route
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pyodbc

from config import get_settings
from weather_api_client import WeatherAPIClient
from weather_cache import WeatherCache, WeatherClusterOptimizer
from weather_waypoints import WaypointCalculator

logger = logging.getLogger(__name__)


class WeatherUpdateService:
    """
    Orchestrates weather updates for active vessels
    Implements smart caching and clustering to minimize API calls
    """

    def __init__(self):
        self.settings = get_settings()
        self.api_client = None  # Initialized async
        self.cache = WeatherCache(
            proximity_threshold_nm=self.settings.weather_proximity_threshold_nm,
            cache_duration_hours=self.settings.weather_cache_duration_hours
        )
        self.waypoint_calculator = WaypointCalculator()

    async def initialize(self):
        """Initialize async components"""
        if not self.api_client:
            self.api_client = WeatherAPIClient(self.settings.weather_api_key)
            logger.info("Weather API client initialized")

    async def close(self):
        """Clean up resources"""
        if self.api_client:
            await self.api_client.close()

    async def update_all_active_vessels(self) -> Dict:
        """
        Update weather for all active vessels
        Main entry point for hourly scheduled updates

        Returns:
            Statistics dict
        """
        logger.info("=== Starting hourly weather update ===")

        try:
            # Ensure API client is initialized
            await self.initialize()

            # Get active vessels from database
            active_vessels = self._get_active_vessels()

            if not active_vessels:
                logger.info("No active vessels to update")
                return {
                    "vessels_processed": 0,
                    "api_calls_made": 0,
                    "cache_hits": 0,
                    "errors": 0,
                    "duration_seconds": 0
                }

            logger.info(f"Found {len(active_vessels)} active vessels")

            start_time = datetime.utcnow()
            stats = {
                "vessels_processed": 0,
                "api_calls_made": 0,
                "cache_hits": 0,
                "errors": 0
            }

            # Process each vessel
            for vessel_data in active_vessels:
                try:
                    vessel_stats = await self._update_vessel_weather(vessel_data)
                    stats["vessels_processed"] += 1
                    stats["api_calls_made"] += vessel_stats["api_calls"]
                    stats["cache_hits"] += vessel_stats["cache_hits"]
                except Exception as e:
                    logger.error(f"Failed to update vessel {vessel_data['VesselName']}: {e}")
                    stats["errors"] += 1

            end_time = datetime.utcnow()
            stats["duration_seconds"] = (end_time - start_time).total_seconds()

            logger.info(
                f"=== Weather update complete ===\n"
                f"Vessels processed: {stats['vessels_processed']}\n"
                f"API calls made: {stats['api_calls_made']}\n"
                f"Cache hits: {stats['cache_hits']}\n"
                f"Errors: {stats['errors']}\n"
                f"Duration: {stats['duration_seconds']:.2f}s"
            )

            return stats

        except Exception as e:
            logger.error(f"Weather update failed: {e}", exc_info=True)
            return {
                "vessels_processed": 0,
                "api_calls_made": 0,
                "cache_hits": 0,
                "errors": 1,
                "duration_seconds": 0
            }

    async def _update_vessel_weather(self, vessel_data: Dict) -> Dict:
        """
        Update weather for a single vessel
        Fetches port weather + 5 waypoint forecasts

        Args:
            vessel_data: Dict with vessel, schedule, AIS position data

        Returns:
            Statistics dict
        """
        vessel_id = vessel_data["VesselId"]
        schedule_id = vessel_data["ScheduleId"]
        vessel_name = vessel_data["VesselName"]

        logger.info(f"Updating weather for {vessel_name} (Schedule: {schedule_id})")

        stats = {"api_calls": 0, "cache_hits": 0}

        # Convert DB decimal.Decimal values to float for math operations
        port_lat = float(vessel_data["PortLatitude"])
        port_lon = float(vessel_data["PortLongitude"])

        # 1. Update port weather
        port_weather_stats = await self._update_port_weather(
            vessel_data["PortCode"],
            port_lat,
            port_lon,
            vessel_id,
            schedule_id
        )
        stats["api_calls"] += port_weather_stats["api_calls"]
        stats["cache_hits"] += port_weather_stats["cache_hits"]

        # 2. Calculate route waypoints (if vessel has current position)
        if vessel_data["CurrentLatitude"] and vessel_data["CurrentLongitude"]:
            current_lat = float(vessel_data["CurrentLatitude"])
            current_lon = float(vessel_data["CurrentLongitude"])
            waypoint_stats = await self._update_waypoint_weather(
                vessel_id,
                schedule_id,
                current_lat,
                current_lon,
                port_lat,
                port_lon
            )
            stats["api_calls"] += waypoint_stats["api_calls"]
            stats["cache_hits"] += waypoint_stats["cache_hits"]
        else:
            logger.warning(f"No AIS position for {vessel_name}, skipping waypoint weather")

        return stats

    async def _update_port_weather(
        self,
        port_code: str,
        port_lat: float,
        port_lon: float,
        vessel_id: int,
        schedule_id: int
    ) -> Dict:
        """
        Update weather for port location

        Returns:
            Statistics dict with api_calls and cache_hits
        """
        # Check cache first
        cached = self.cache.get_cached_weather(port_lat, port_lon, location_type="PORT")

        if cached:
            # Use cached data
            await self._store_weather_forecast(
                location_type="PORT",
                location_name=port_code,
                latitude=port_lat,
                longitude=port_lon,
                vessel_id=vessel_id,
                schedule_id=schedule_id,
                waypoint_sequence=None,
                weather_data=cached.weather_data,
                impact_factor=cached.impact_factor,
                alert_level=cached.alert_level
            )
            return {"api_calls": 0, "cache_hits": 1}

        # Fetch from API
        weather_data = await self.api_client.get_current_and_forecast(port_lat, port_lon)

        if not weather_data:
            logger.error(f"Failed to fetch weather for port {port_code}")
            return {"api_calls": 1, "cache_hits": 0}

        # Calculate impact metrics
        impact_factor = self.api_client.calculate_weather_impact_factor(weather_data)
        alert_level = self.api_client.determine_alert_level(weather_data)

        # Store in cache
        self.cache.store_weather(
            port_lat, port_lon,
            weather_data,
            location_type="PORT",
            impact_factor=impact_factor,
            alert_level=alert_level
        )

        # Store in database
        await self._store_weather_forecast(
            location_type="PORT",
            location_name=port_code,
            latitude=port_lat,
            longitude=port_lon,
            vessel_id=vessel_id,
            schedule_id=schedule_id,
            waypoint_sequence=None,
            weather_data=weather_data,
            impact_factor=impact_factor,
            alert_level=alert_level
        )

        # Log API usage
        await self._log_api_usage(port_lat, port_lon, 200, cache_hit=False)

        return {"api_calls": 1, "cache_hits": 0}

    async def _update_waypoint_weather(
        self,
        vessel_id: int,
        schedule_id: int,
        vessel_lat: float,
        vessel_lon: float,
        port_lat: float,
        port_lon: float,
        num_waypoints: int = 5
    ) -> Dict:
        """
        Update weather for route waypoints

        Returns:
            Statistics dict
        """
        # Calculate waypoints
        waypoints = self.waypoint_calculator.calculate_waypoints(
            vessel_lat, vessel_lon,
            port_lat, port_lon,
            num_waypoints
        )

        stats = {"api_calls": 0, "cache_hits": 0}

        for waypoint in waypoints:
            # Check cache
            cached = self.cache.get_cached_weather(
                waypoint.latitude,
                waypoint.longitude,
                location_type="WAYPOINT"
            )

            if cached:
                # Use cached data
                await self._store_weather_forecast(
                    location_type="WAYPOINT",
                    location_name=f"Waypoint_{waypoint.sequence}",
                    latitude=waypoint.latitude,
                    longitude=waypoint.longitude,
                    vessel_id=vessel_id,
                    schedule_id=schedule_id,
                    waypoint_sequence=waypoint.sequence,
                    weather_data=cached.weather_data,
                    impact_factor=cached.impact_factor,
                    alert_level=cached.alert_level
                )
                stats["cache_hits"] += 1
                continue

            # Fetch from API
            weather_data = await self.api_client.get_current_and_forecast(
                waypoint.latitude,
                waypoint.longitude
            )

            if not weather_data:
                logger.error(f"Failed to fetch weather for Waypoint {waypoint.sequence}")
                continue

            # Calculate impact metrics
            impact_factor = self.api_client.calculate_weather_impact_factor(weather_data)
            alert_level = self.api_client.determine_alert_level(weather_data)

            # Store in cache
            self.cache.store_weather(
                waypoint.latitude, waypoint.longitude,
                weather_data,
                location_type="WAYPOINT",
                impact_factor=impact_factor,
                alert_level=alert_level
            )

            # Store in database
            await self._store_weather_forecast(
                location_type="WAYPOINT",
                location_name=f"Waypoint_{waypoint.sequence}",
                latitude=waypoint.latitude,
                longitude=waypoint.longitude,
                vessel_id=vessel_id,
                schedule_id=schedule_id,
                waypoint_sequence=waypoint.sequence,
                weather_data=weather_data,
                impact_factor=impact_factor,
                alert_level=alert_level
            )

            # Log API usage
            await self._log_api_usage(waypoint.latitude, waypoint.longitude, 200, cache_hit=False)

            stats["api_calls"] += 1

        return stats

    async def _store_weather_forecast(
        self,
        location_type: str,
        location_name: str,
        latitude: float,
        longitude: float,
        vessel_id: int,
        schedule_id: int,
        waypoint_sequence: Optional[int],
        weather_data: Dict,
        impact_factor: float,
        alert_level: str
    ):
        """Store weather forecast in database"""
        try:
            current = weather_data.get("current", {})

            conn = pyodbc.connect(self.settings.db_connection_string)
            cursor = conn.cursor()

            # Forecast for current time
            forecast_for = datetime.utcnow()
            expires_at = forecast_for + timedelta(hours=self.settings.weather_cache_duration_hours)

            sql = """
                INSERT INTO WEATHER_FORECAST (
                    LocationType, LocationName, Latitude, Longitude,
                    VesselId, ScheduleId, WaypointSequence,
                    ForecastFor, ExpiresAt,
                    WindSpeed, WindDirection, WindGust, Visibility,
                    WaveHeight, Temperature, Precipitation, WeatherCondition,
                    WeatherImpactFactor, IsOperationalAlert, AlertLevel
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            cursor.execute(sql, (
                location_type,
                location_name,
                latitude,
                longitude,
                vessel_id,
                schedule_id,
                waypoint_sequence,
                forecast_for,
                expires_at,
                current.get("wind_speed_kts"),
                current.get("wind_direction_deg"),
                current.get("wind_gust_kts"),
                current.get("visibility_nm"),
                current.get("wave_height_m"),
                current.get("temperature_c"),
                current.get("precipitation_mm"),
                current.get("weather_condition"),
                impact_factor,
                1 if alert_level in ["WARNING", "CRITICAL"] else 0,
                alert_level
            ))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store weather forecast: {e}")

    async def _log_api_usage(
        self,
        latitude: float,
        longitude: float,
        response_status: int,
        cache_hit: bool = False
    ):
        """Log API usage for monitoring"""
        try:
            conn = pyodbc.connect(self.settings.db_connection_string)
            cursor = conn.cursor()

            sql = """
                INSERT INTO WEATHER_API_USAGE (ApiProvider, Latitude, Longitude, ResponseStatus, CacheHit)
                VALUES (?, ?, ?, ?, ?)
            """

            cursor.execute(sql, (
                self.settings.weather_api_provider,
                latitude,
                longitude,
                response_status,
                1 if cache_hit else 0
            ))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to log API usage: {e}")

    def _get_active_vessels(self) -> List[Dict]:
        """Get active vessels from database using stored procedure"""
        try:
            conn = pyodbc.connect(self.settings.db_connection_string)
            cursor = conn.cursor()

            cursor.execute("EXEC dbo.usp_GetActiveVesselsForWeatherUpdate")

            columns = [column[0] for column in cursor.description]
            vessels = []

            for row in cursor.fetchall():
                vessel_dict = dict(zip(columns, row))
                vessels.append(vessel_dict)

            cursor.close()
            conn.close()

            return vessels

        except Exception as e:
            logger.error(f"Failed to get active vessels: {e}")
            return []


# Global instance
_weather_service: Optional[WeatherUpdateService] = None


async def get_weather_service() -> WeatherUpdateService:
    """Get global weather service instance"""
    global _weather_service

    if _weather_service is None:
        _weather_service = WeatherUpdateService()
        await _weather_service.initialize()

    return _weather_service
