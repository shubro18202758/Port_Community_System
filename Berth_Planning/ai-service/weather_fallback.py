"""
Weather Fallback Handler
Provides fallback weather data when API fails
Uses cached data, historical averages, or safe defaults
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import pyodbc

from config import get_settings

logger = logging.getLogger(__name__)


class WeatherFallbackHandler:
    """
    Handles weather API failures with multi-tier fallback strategy
    Priority: Recent Cache > Historical Average > Default Safe Values
    """

    def __init__(self):
        self.settings = get_settings()

    def get_fallback_weather(
        self,
        lat: float,
        lon: float,
        location_type: str = "WAYPOINT"
    ) -> Optional[Dict]:
        """
        Get fallback weather data when API fails

        Fallback strategy:
        1. Recent cache (up to 6 hours old)
        2. Historical average for location (last 30 days)
        3. Default safe values

        Args:
            lat: Latitude
            lon: Longitude
            location_type: 'PORT' or 'WAYPOINT'

        Returns:
            Normalized weather data dict
        """
        logger.warning(f"Attempting fallback weather for ({lat:.4f}, {lon:.4f})")

        # Strategy 1: Recent cache (extended to 6 hours)
        recent_cache = self._get_recent_cache(lat, lon, hours_back=6)
        if recent_cache:
            logger.info(f"Fallback: Using recent cache data (age: {recent_cache['age_hours']:.1f}h)")
            return recent_cache["weather_data"]

        # Strategy 2: Historical average
        historical_avg = self._get_historical_average(lat, lon)
        if historical_avg:
            logger.info("Fallback: Using historical average weather")
            return historical_avg

        # Strategy 3: Default safe values
        logger.warning("Fallback: Using default safe weather values")
        return self._get_default_safe_values(lat, lon)

    def _get_recent_cache(
        self,
        lat: float,
        lon: float,
        hours_back: int = 6
    ) -> Optional[Dict]:
        """
        Get recent cached weather (within extended time window)

        Args:
            lat, lon: Location coordinates
            hours_back: How far back to look (hours)

        Returns:
            Dict with weather_data and age_hours, or None
        """
        try:
            conn = pyodbc.connect(self.settings.db_connection_string)
            cursor = conn.cursor()

            # Find closest cached entry within last N hours
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

            sql = """
                SELECT TOP 1
                    WindSpeed, WindDirection, WindGust, Visibility,
                    WaveHeight, Temperature, Precipitation, WeatherCondition,
                    WeatherImpactFactor, AlertLevel, FetchedAt
                FROM WEATHER_FORECAST
                WHERE FetchedAt >= ?
                  AND ABS(Latitude - ?) < 0.5
                  AND ABS(Longitude - ?) < 0.5
                ORDER BY
                    SQRT(POWER(Latitude - ?, 2) + POWER(Longitude - ?, 2)) ASC,
                    FetchedAt DESC
            """

            cursor.execute(sql, (cutoff_time, lat, lon, lat, lon))
            row = cursor.fetchone()

            cursor.close()
            conn.close()

            if row:
                age_hours = (datetime.utcnow() - row[10]).total_seconds() / 3600

                weather_data = {
                    "current": {
                        "timestamp": datetime.utcnow(),
                        "wind_speed_kts": float(row[0]) if row[0] else 15.0,
                        "wind_direction_deg": int(row[1]) if row[1] else 0,
                        "wind_gust_kts": float(row[2]) if row[2] else 20.0,
                        "visibility_nm": float(row[3]) if row[3] else 10.0,
                        "wave_height_m": float(row[4]) if row[4] else 1.0,
                        "temperature_c": float(row[5]) if row[5] else 25.0,
                        "precipitation_mm": float(row[6]) if row[6] else 0.0,
                        "weather_condition": row[7] if row[7] else "Clear",
                        "is_day": True
                    },
                    "forecast": [],
                    "alerts": [],
                    "location": {
                        "lat": lat,
                        "lon": lon,
                        "fallback_source": "recent_cache"
                    }
                }

                return {
                    "weather_data": weather_data,
                    "age_hours": age_hours
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get recent cache: {e}")
            return None

    def _get_historical_average(
        self,
        lat: float,
        lon: float,
        days_back: int = 30
    ) -> Optional[Dict]:
        """
        Get historical average weather for location

        Args:
            lat, lon: Location coordinates
            days_back: Number of days to average over

        Returns:
            Normalized weather data dict with averages
        """
        try:
            conn = pyodbc.connect(self.settings.db_connection_string)
            cursor = conn.cursor()

            cutoff_time = datetime.utcnow() - timedelta(days=days_back)

            sql = """
                SELECT
                    AVG(WindSpeed) AS AvgWindSpeed,
                    AVG(WindGust) AS AvgWindGust,
                    AVG(Visibility) AS AvgVisibility,
                    AVG(WaveHeight) AS AvgWaveHeight,
                    AVG(Temperature) AS AvgTemperature,
                    AVG(Precipitation) AS AvgPrecipitation,
                    AVG(WeatherImpactFactor) AS AvgImpactFactor
                FROM WEATHER_FORECAST
                WHERE FetchedAt >= ?
                  AND ABS(Latitude - ?) < 1.0
                  AND ABS(Longitude - ?) < 1.0
                HAVING COUNT(*) >= 5
            """

            cursor.execute(sql, (cutoff_time, lat, lon))
            row = cursor.fetchone()

            cursor.close()
            conn.close()

            if row and row[0] is not None:
                weather_data = {
                    "current": {
                        "timestamp": datetime.utcnow(),
                        "wind_speed_kts": float(row[0]),
                        "wind_direction_deg": 0,  # No average for direction
                        "wind_gust_kts": float(row[1]) if row[1] else float(row[0]) * 1.5,
                        "visibility_nm": float(row[2]) if row[2] else 10.0,
                        "wave_height_m": float(row[3]) if row[3] else 1.0,
                        "temperature_c": float(row[4]) if row[4] else 25.0,
                        "precipitation_mm": float(row[5]) if row[5] else 0.0,
                        "weather_condition": "Historical Average",
                        "is_day": True
                    },
                    "forecast": [],
                    "alerts": [{
                        "headline": "Using Historical Weather Data",
                        "severity": "Minor",
                        "event": "Weather API Unavailable",
                        "description": f"Using {days_back}-day average weather data"
                    }],
                    "location": {
                        "lat": lat,
                        "lon": lon,
                        "fallback_source": "historical_average"
                    }
                }

                return weather_data

            return None

        except Exception as e:
            logger.error(f"Failed to get historical average: {e}")
            return None

    def _get_default_safe_values(self, lat: float, lon: float) -> Dict:
        """
        Return conservative default weather values
        Assumes moderate conditions to avoid over-optimistic ETAs

        Returns:
            Normalized weather data dict with safe defaults
        """
        weather_data = {
            "current": {
                "timestamp": datetime.utcnow(),
                "wind_speed_kts": 15.0,  # Moderate breeze
                "wind_direction_deg": 0,
                "wind_gust_kts": 20.0,
                "visibility_nm": 5.0,  # Reduced visibility
                "wave_height_m": 1.0,  # Slight sea
                "temperature_c": 25.0,
                "precipitation_mm": 0.0,
                "weather_condition": "Default Safe Values",
                "is_day": True
            },
            "forecast": [],
            "alerts": [{
                "headline": "Using Default Weather Values",
                "severity": "Moderate",
                "event": "Weather Data Unavailable",
                "description": "Using conservative default weather values. Check actual conditions."
            }],
            "location": {
                "lat": lat,
                "lon": lon,
                "fallback_source": "default_safe_values"
            }
        }

        return weather_data

    async def create_fallback_alert(
        self,
        vessel_id: int,
        schedule_id: int,
        fallback_source: str,
        reason: str
    ):
        """
        Create alert in database when fallback is used

        Args:
            vessel_id: Vessel ID
            schedule_id: Schedule ID
            fallback_source: 'recent_cache', 'historical_average', or 'default_safe_values'
            reason: Reason for fallback (e.g., "API timeout")
        """
        try:
            conn = pyodbc.connect(self.settings.db_connection_string)
            cursor = conn.cursor()

            severity = {
                "recent_cache": "Low",
                "historical_average": "Medium",
                "default_safe_values": "High"
            }.get(fallback_source, "Medium")

            sql = """
                INSERT INTO ALERTS_NOTIFICATIONS (
                    VesselId, ScheduleId, AlertType, Severity,
                    Description, IsResolved, CreatedAt
                ) VALUES (?, ?, ?, ?, ?, 0, GETUTCDATE())
            """

            description = (
                f"Weather API unavailable ({reason}). "
                f"Using fallback: {fallback_source}. "
                f"Verify weather conditions manually."
            )

            cursor.execute(sql, (
                vessel_id,
                schedule_id,
                "Weather Data Fallback",
                severity,
                description
            ))

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Created fallback alert for vessel {vessel_id}, schedule {schedule_id}")

        except Exception as e:
            logger.error(f"Failed to create fallback alert: {e}")

    def calculate_fallback_impact_factor(self, weather_data: Dict) -> float:
        """
        Calculate impact factor from fallback weather data
        More conservative than API-based calculation

        Returns:
            Impact factor (0.5-1.0), conservatively estimated
        """
        current = weather_data.get("current", {})
        fallback_source = weather_data.get("location", {}).get("fallback_source", "")

        wind_kts = current.get("wind_speed_kts", 15)
        visibility_nm = current.get("visibility_nm", 10)

        impact_factor = 1.0

        # Apply conservative impact
        if wind_kts > 25:
            impact_factor *= 0.75
        elif wind_kts > 15:
            impact_factor *= 0.90

        if visibility_nm < 2:
            impact_factor *= 0.85
        elif visibility_nm < 5:
            impact_factor *= 0.95

        # Additional penalty for using fallback (conservatism)
        if fallback_source == "default_safe_values":
            impact_factor *= 0.95
        elif fallback_source == "historical_average":
            impact_factor *= 0.98

        return max(0.5, min(1.0, round(impact_factor, 4)))

    def determine_fallback_alert_level(self, weather_data: Dict) -> str:
        """
        Determine alert level from fallback data
        More conservative thresholds

        Returns:
            'NORMAL', 'WARNING', or 'CRITICAL'
        """
        current = weather_data.get("current", {})
        fallback_source = weather_data.get("location", {}).get("fallback_source", "")

        wind_kts = current.get("wind_speed_kts", 15)
        visibility_nm = current.get("visibility_nm", 10)

        # More conservative thresholds for fallback data
        if wind_kts > 30 or visibility_nm < 1 or fallback_source == "default_safe_values":
            return "WARNING"  # Escalate due to uncertainty

        if wind_kts > 20 or visibility_nm < 3:
            return "WARNING"

        return "NORMAL"
