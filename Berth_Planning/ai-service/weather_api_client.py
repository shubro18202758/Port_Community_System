"""
Weather API Client
Integrates with WeatherAPI.com for real-time weather data
Supports current weather + 5-day forecast
"""

import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class WeatherAPIClient:
    """
    Client for WeatherAPI.com free tier (1M calls/month)
    Provides current weather + 5-day forecast
    """

    BASE_URL = "http://api.weatherapi.com/v1"

    def __init__(self, api_key: str):
        """
        Initialize WeatherAPI client

        Args:
            api_key: WeatherAPI.com API key
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def get_current_and_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Get current weather + multi-day forecast for a location

        Args:
            lat: Latitude
            lon: Longitude
            days: Number of forecast days (1-10, free tier max: 3)

        Returns:
            Normalized weather data dict or None on error
        """
        try:
            # Free tier supports up to 3 days forecast
            days = min(days, 3)

            url = f"{self.BASE_URL}/forecast.json"
            params = {
                "key": self.api_key,
                "q": f"{lat},{lon}",
                "days": days,
                "aqi": "no",  # No air quality (save bandwidth)
                "alerts": "yes"  # Get weather alerts
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return self._normalize_weather_data(data)

        except httpx.HTTPStatusError as e:
            logger.error(f"WeatherAPI HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"WeatherAPI request failed: {e}")
            return None

    def _normalize_weather_data(self, raw_data: Dict) -> Dict[str, Any]:
        """
        Normalize WeatherAPI response to internal format
        Converts units: mph -> knots, miles -> nautical miles
        """
        current = raw_data.get("current", {})
        location = raw_data.get("location", {})
        forecast_days = raw_data.get("forecast", {}).get("forecastday", [])
        alerts = raw_data.get("alerts", {}).get("alert", [])

        # Current weather
        wind_mph = current.get("wind_mph", 0)
        wind_kts = self._mph_to_knots(wind_mph)

        gust_mph = current.get("gust_mph", wind_mph * 1.5)  # Estimate if not provided
        gust_kts = self._mph_to_knots(gust_mph)

        visibility_miles = current.get("vis_miles", 10)
        visibility_nm = self._miles_to_nautical_miles(visibility_miles)

        # Estimate wave height from wind speed (empirical formula)
        wave_height_m = self._estimate_wave_height(wind_kts)

        normalized = {
            "current": {
                "timestamp": datetime.fromisoformat(current.get("last_updated", "")),
                "wind_speed_kts": round(wind_kts, 2),
                "wind_direction_deg": current.get("wind_degree", 0),
                "wind_gust_kts": round(gust_kts, 2),
                "visibility_nm": round(visibility_nm, 2),
                "wave_height_m": round(wave_height_m, 2),
                "temperature_c": current.get("temp_c", 25),
                "precipitation_mm": current.get("precip_mm", 0),
                "weather_condition": current.get("condition", {}).get("text", "Clear"),
                "is_day": current.get("is_day", 1) == 1
            },
            "forecast": [],
            "alerts": [],
            "location": {
                "name": location.get("name", ""),
                "region": location.get("region", ""),
                "country": location.get("country", ""),
                "lat": location.get("lat", 0),
                "lon": location.get("lon", 0),
                "tz_id": location.get("tz_id", "UTC")
            }
        }

        # Forecast data
        for day in forecast_days:
            day_data = day.get("day", {})
            date_str = day.get("date", "")

            avg_wind_mph = day_data.get("maxwind_mph", 10)
            avg_wind_kts = self._mph_to_knots(avg_wind_mph)

            avg_vis_miles = day_data.get("avgvis_miles", 10)
            avg_vis_nm = self._miles_to_nautical_miles(avg_vis_miles)

            wave_height_m = self._estimate_wave_height(avg_wind_kts)

            normalized["forecast"].append({
                "date": datetime.strptime(date_str, "%Y-%m-%d").date(),
                "max_wind_kts": round(avg_wind_kts, 2),
                "avg_visibility_nm": round(avg_vis_nm, 2),
                "total_precip_mm": day_data.get("totalprecip_mm", 0),
                "avg_temp_c": day_data.get("avgtemp_c", 25),
                "condition": day_data.get("condition", {}).get("text", ""),
                "wave_height_m": round(wave_height_m, 2)
            })

        # Weather alerts
        for alert in alerts:
            normalized["alerts"].append({
                "headline": alert.get("headline", ""),
                "severity": alert.get("severity", ""),
                "event": alert.get("event", ""),
                "effective": alert.get("effective", ""),
                "expires": alert.get("expires", ""),
                "description": alert.get("desc", "")
            })

        return normalized

    @staticmethod
    def _mph_to_knots(mph: float) -> float:
        """Convert miles per hour to knots"""
        return mph * 0.868976

    @staticmethod
    def _miles_to_nautical_miles(miles: float) -> float:
        """Convert statute miles to nautical miles"""
        return miles * 0.868976

    @staticmethod
    def _estimate_wave_height(wind_speed_kts: float) -> float:
        """
        Estimate significant wave height from wind speed
        Uses simplified empirical formula (Bretschneider)

        Note: This is an approximation. For production, use marine-specific APIs.
        """
        # Beaufort scale approximation
        # H_s (meters) ≈ 0.025 * (wind_kts)^1.5 for open ocean
        if wind_speed_kts < 1:
            return 0.0
        elif wind_speed_kts < 7:
            return 0.1  # Calm
        elif wind_speed_kts < 17:
            return 0.5  # Moderate
        elif wind_speed_kts < 27:
            return 2.0  # Rough
        elif wind_speed_kts < 40:
            return 4.0  # Very rough
        else:
            return 6.0  # High/Very high

    def calculate_weather_impact_factor(self, weather_data: Dict) -> float:
        """
        Calculate speed impact factor based on weather conditions
        Returns multiplier: 0.5 (severe slowdown) to 1.0 (no impact)

        Args:
            weather_data: Normalized weather data

        Returns:
            Impact factor (0.5-1.0)
        """
        current = weather_data.get("current", {})

        wind_kts = current.get("wind_speed_kts", 0)
        wave_height_m = current.get("wave_height_m", 0)
        visibility_nm = current.get("visibility_nm", 10)
        precip_mm = current.get("precipitation_mm", 0)

        impact_factor = 1.0

        # Wind impact (major factor)
        if wind_kts > 40:  # Storm force
            impact_factor *= 0.6
        elif wind_kts > 30:  # Gale
            impact_factor *= 0.75
        elif wind_kts > 20:  # Strong breeze
            impact_factor *= 0.90

        # Wave height impact
        if wave_height_m > 4:
            impact_factor *= 0.75
        elif wave_height_m > 2.5:
            impact_factor *= 0.85
        elif wave_height_m > 1.5:
            impact_factor *= 0.95

        # Visibility impact
        if visibility_nm < 0.5:  # Fog
            impact_factor *= 0.70
        elif visibility_nm < 2:
            impact_factor *= 0.85
        elif visibility_nm < 5:
            impact_factor *= 0.95

        # Precipitation impact (minor)
        if precip_mm > 10:  # Heavy rain
            impact_factor *= 0.95
        elif precip_mm > 5:  # Moderate rain
            impact_factor *= 0.98

        # Ensure minimum 0.5, maximum 1.0
        return max(0.5, min(1.0, round(impact_factor, 4)))

    def determine_alert_level(self, weather_data: Dict) -> str:
        """
        Determine operational alert level

        Returns:
            'NORMAL', 'WARNING', or 'CRITICAL'
        """
        current = weather_data.get("current", {})
        alerts = weather_data.get("alerts", [])

        wind_kts = current.get("wind_speed_kts", 0)
        wave_height_m = current.get("wave_height_m", 0)
        visibility_nm = current.get("visibility_nm", 10)

        # Critical conditions
        if wind_kts > 40 or wave_height_m > 4 or visibility_nm < 0.5:
            return "CRITICAL"

        # Warning conditions
        if wind_kts > 25 or wave_height_m > 2.5 or visibility_nm < 2:
            return "WARNING"

        # Check API alerts
        if any(alert.get("severity", "").lower() in ["extreme", "severe"] for alert in alerts):
            return "CRITICAL"
        if any(alert.get("severity", "").lower() == "moderate" for alert in alerts):
            return "WARNING"

        return "NORMAL"


class WeatherAPIClientSync:
    """Synchronous wrapper for testing/simple use cases"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_current_and_forecast(
        self,
        lat: float,
        lon: float,
        days: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Synchronous weather fetch"""
        import asyncio

        async def _fetch():
            client = WeatherAPIClient(self.api_key)
            try:
                return await client.get_current_and_forecast(lat, lon, days)
            finally:
                await client.close()

        return asyncio.run(_fetch())
