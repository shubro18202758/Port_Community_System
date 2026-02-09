"""
Weather Cache Manager
Spatial-temporal caching to minimize API calls
Clusters vessels by proximity to share weather data
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class CachedWeather:
    """Cached weather data with expiry"""
    latitude: float
    longitude: float
    weather_data: Dict
    fetched_at: datetime
    expires_at: datetime
    location_type: str  # 'PORT' or 'WAYPOINT'
    impact_factor: float
    alert_level: str


class WeatherCache:
    """
    Spatial-temporal weather cache
    - Proximity threshold: 10 nautical miles
    - Time threshold: 1 hour
    """

    def __init__(
        self,
        proximity_threshold_nm: float = 10.0,
        cache_duration_hours: int = 1
    ):
        """
        Initialize weather cache

        Args:
            proximity_threshold_nm: Distance threshold for cache hits (nautical miles)
            cache_duration_hours: Cache expiry time (hours)
        """
        self.proximity_threshold_nm = proximity_threshold_nm
        self.cache_duration_hours = cache_duration_hours
        self._cache: List[CachedWeather] = []

    def get_cached_weather(
        self,
        lat: float,
        lon: float,
        location_type: str = "WAYPOINT"
    ) -> Optional[CachedWeather]:
        """
        Get weather from cache if available and not expired

        Args:
            lat: Latitude
            lon: Longitude
            location_type: 'PORT' or 'WAYPOINT'

        Returns:
            CachedWeather if found and valid, None otherwise
        """
        now = datetime.utcnow()

        # Find closest cached entry within threshold
        closest_entry = None
        min_distance = float('inf')

        for entry in self._cache:
            # Check if expired
            if entry.expires_at < now:
                continue

            # Calculate distance
            distance_nm = self._haversine_distance(
                lat, lon,
                entry.latitude, entry.longitude
            )

            # Check if within threshold
            if distance_nm <= self.proximity_threshold_nm:
                if distance_nm < min_distance:
                    min_distance = distance_nm
                    closest_entry = entry

        if closest_entry:
            logger.info(
                f"Cache HIT: {location_type} at ({lat:.4f}, {lon:.4f}), "
                f"distance: {min_distance:.2f}nm"
            )
            return closest_entry
        else:
            logger.debug(
                f"Cache MISS: {location_type} at ({lat:.4f}, {lon:.4f})"
            )
            return None

    def store_weather(
        self,
        lat: float,
        lon: float,
        weather_data: Dict,
        location_type: str = "WAYPOINT",
        impact_factor: float = 1.0,
        alert_level: str = "NORMAL"
    ) -> CachedWeather:
        """
        Store weather data in cache

        Args:
            lat: Latitude
            lon: Longitude
            weather_data: Normalized weather data
            location_type: 'PORT' or 'WAYPOINT'
            impact_factor: Weather impact factor (0.5-1.0)
            alert_level: 'NORMAL', 'WARNING', or 'CRITICAL'

        Returns:
            CachedWeather entry
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.cache_duration_hours)

        entry = CachedWeather(
            latitude=lat,
            longitude=lon,
            weather_data=weather_data,
            fetched_at=now,
            expires_at=expires_at,
            location_type=location_type,
            impact_factor=impact_factor,
            alert_level=alert_level
        )

        self._cache.append(entry)

        # Cleanup expired entries
        self._cleanup_expired()

        logger.debug(
            f"Cached weather for {location_type} at ({lat:.4f}, {lon:.4f}), "
            f"expires: {expires_at.isoformat()}"
        )

        return entry

    def cluster_vessels_by_proximity(
        self,
        vessel_locations: List[Dict]
    ) -> List[List[Dict]]:
        """
        Cluster vessels within proximity threshold
        Vessels in same cluster can share weather data

        Args:
            vessel_locations: List of dicts with 'vessel_id', 'lat', 'lon'

        Returns:
            List of vessel clusters
        """
        if not vessel_locations:
            return []

        clusters = []
        unclustered = vessel_locations.copy()

        while unclustered:
            # Start new cluster with first unclustered vessel
            seed = unclustered.pop(0)
            cluster = [seed]

            # Find all vessels within threshold of seed
            i = 0
            while i < len(unclustered):
                vessel = unclustered[i]
                distance_nm = self._haversine_distance(
                    seed['lat'], seed['lon'],
                    vessel['lat'], vessel['lon']
                )

                if distance_nm <= self.proximity_threshold_nm:
                    cluster.append(vessel)
                    unclustered.pop(i)
                else:
                    i += 1

            clusters.append(cluster)

        logger.info(
            f"Clustered {len(vessel_locations)} vessels into {len(clusters)} groups "
            f"(avg cluster size: {len(vessel_locations)/len(clusters):.1f})"
        )

        return clusters

    def _cleanup_expired(self):
        """Remove expired cache entries"""
        now = datetime.utcnow()
        original_count = len(self._cache)

        self._cache = [
            entry for entry in self._cache
            if entry.expires_at >= now
        ]

        removed_count = original_count - len(self._cache)
        if removed_count > 0:
            logger.debug(f"Removed {removed_count} expired cache entries")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        now = datetime.utcnow()

        active_entries = [e for e in self._cache if e.expires_at >= now]
        port_entries = [e for e in active_entries if e.location_type == 'PORT']
        waypoint_entries = [e for e in active_entries if e.location_type == 'WAYPOINT']

        return {
            "total_entries": len(active_entries),
            "port_entries": len(port_entries),
            "waypoint_entries": len(waypoint_entries),
            "expired_entries": len(self._cache) - len(active_entries),
            "oldest_entry": min(
                [e.fetched_at for e in active_entries],
                default=None
            ),
            "newest_entry": max(
                [e.fetched_at for e in active_entries],
                default=None
            )
        }

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula

        Args:
            lat1, lon1: First point (degrees)
            lat2, lon2: Second point (degrees)

        Returns:
            Distance in nautical miles
        """
        # Earth radius in nautical miles
        R = 3440.065

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def clear_cache(self):
        """Clear all cache entries"""
        self._cache.clear()
        logger.info("Weather cache cleared")


class WeatherClusterOptimizer:
    """
    Optimizes weather API calls by clustering locations
    """

    @staticmethod
    def optimize_waypoint_fetch_order(
        waypoints: List[Dict],
        cache: WeatherCache
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Separate waypoints into cached vs need-to-fetch

        Args:
            waypoints: List of waypoint dicts with 'lat', 'lon'
            cache: WeatherCache instance

        Returns:
            Tuple of (waypoints_to_fetch, cached_waypoints)
        """
        to_fetch = []
        cached = []

        for waypoint in waypoints:
            cached_entry = cache.get_cached_weather(
                waypoint['lat'],
                waypoint['lon'],
                location_type='WAYPOINT'
            )

            if cached_entry:
                cached.append({
                    **waypoint,
                    'cached_weather': cached_entry
                })
            else:
                to_fetch.append(waypoint)

        cache_hit_rate = len(cached) / len(waypoints) if waypoints else 0

        logger.info(
            f"Waypoint cache hit rate: {cache_hit_rate:.1%} "
            f"({len(cached)}/{len(waypoints)} cached)"
        )

        return to_fetch, cached

    @staticmethod
    def estimate_api_calls_saved(
        total_locations: int,
        clustered_groups: int,
        cache_hit_rate: float = 0.4
    ) -> Dict:
        """
        Estimate API call savings from clustering + caching

        Args:
            total_locations: Total waypoints/ports to fetch
            clustered_groups: Number of clusters after grouping
            cache_hit_rate: Expected cache hit rate (0.0-1.0)

        Returns:
            Statistics dict
        """
        # Without optimization
        baseline_calls = total_locations

        # With clustering
        clustered_calls = clustered_groups

        # With caching
        cached_calls = int(clustered_calls * (1 - cache_hit_rate))

        savings_from_clustering = baseline_calls - clustered_calls
        savings_from_caching = clustered_calls - cached_calls
        total_savings = baseline_calls - cached_calls

        return {
            "baseline_api_calls": baseline_calls,
            "calls_after_clustering": clustered_calls,
            "calls_after_caching": cached_calls,
            "savings_from_clustering": savings_from_clustering,
            "savings_from_caching": savings_from_caching,
            "total_api_calls_saved": total_savings,
            "reduction_percentage": (total_savings / baseline_calls * 100) if baseline_calls > 0 else 0
        }
