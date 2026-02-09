"""
Waypoint Calculator for Weather Route Planning
Generates evenly-spaced waypoints along great circle route
from vessel's current position to destination port
"""

import math
from dataclasses import dataclass
from typing import List


@dataclass
class Waypoint:
    """Represents a point along a vessel's route"""
    sequence: int
    latitude: float
    longitude: float
    distance_from_vessel_nm: float
    distance_to_port_nm: float
    total_route_distance_nm: float


class WaypointCalculator:
    """
    Calculate waypoints along a great circle route using SLERP
    (Spherical Linear Interpolation)
    """

    EARTH_RADIUS_NM = 3440.065  # Nautical miles

    def calculate_waypoints(
        self,
        vessel_lat: float,
        vessel_lon: float,
        port_lat: float,
        port_lon: float,
        num_waypoints: int = 5
    ) -> List[Waypoint]:
        """
        Generate evenly-spaced waypoints from vessel to port

        Args:
            vessel_lat: Vessel current latitude (degrees)
            vessel_lon: Vessel current longitude (degrees)
            port_lat: Destination port latitude (degrees)
            port_lon: Destination port longitude (degrees)
            num_waypoints: Number of intermediate waypoints (default 5)

        Returns:
            List of Waypoint objects
        """
        total_distance = self.haversine_distance(
            vessel_lat, vessel_lon, port_lat, port_lon
        )

        if total_distance < 1.0:
            # Vessel is essentially at port
            return []

        waypoints = []

        for i in range(1, num_waypoints + 1):
            fraction = i / (num_waypoints + 1)

            # SLERP interpolation
            lat, lon = self._slerp_interpolate(
                vessel_lat, vessel_lon,
                port_lat, port_lon,
                fraction
            )

            distance_from_vessel = total_distance * fraction
            distance_to_port = total_distance * (1 - fraction)

            waypoints.append(Waypoint(
                sequence=i,
                latitude=round(lat, 7),
                longitude=round(lon, 7),
                distance_from_vessel_nm=round(distance_from_vessel, 1),
                distance_to_port_nm=round(distance_to_port, 1),
                total_route_distance_nm=round(total_distance, 1)
            ))

        return waypoints

    def _slerp_interpolate(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float,
        fraction: float
    ) -> tuple:
        """
        Spherical Linear Interpolation between two points

        Args:
            lat1, lon1: Start point (degrees)
            lat2, lon2: End point (degrees)
            fraction: Interpolation fraction (0.0 to 1.0)

        Returns:
            Tuple of (latitude, longitude) in degrees
        """
        lat1_r = math.radians(lat1)
        lon1_r = math.radians(lon1)
        lat2_r = math.radians(lat2)
        lon2_r = math.radians(lon2)

        # Angular distance
        d = 2 * math.asin(math.sqrt(
            math.sin((lat2_r - lat1_r) / 2) ** 2 +
            math.cos(lat1_r) * math.cos(lat2_r) *
            math.sin((lon2_r - lon1_r) / 2) ** 2
        ))

        if d < 1e-10:
            return lat1, lon1

        a = math.sin((1 - fraction) * d) / math.sin(d)
        b = math.sin(fraction * d) / math.sin(d)

        x = a * math.cos(lat1_r) * math.cos(lon1_r) + b * math.cos(lat2_r) * math.cos(lon2_r)
        y = a * math.cos(lat1_r) * math.sin(lon1_r) + b * math.cos(lat2_r) * math.sin(lon2_r)
        z = a * math.sin(lat1_r) + b * math.sin(lat2_r)

        lat = math.degrees(math.atan2(z, math.sqrt(x ** 2 + y ** 2)))
        lon = math.degrees(math.atan2(y, x))

        return lat, lon

    def haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate great circle distance between two points

        Args:
            lat1, lon1: Point 1 (degrees)
            lat2, lon2: Point 2 (degrees)

        Returns:
            Distance in nautical miles
        """
        lat1_r = math.radians(lat1)
        lat2_r = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_r) * math.cos(lat2_r) *
             math.sin(dlon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return self.EARTH_RADIUS_NM * c

    def calculate_initial_bearing(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate initial bearing from point 1 to point 2

        Returns:
            Bearing in degrees (0-360)
        """
        lat1_r = math.radians(lat1)
        lat2_r = math.radians(lat2)
        dlon = math.radians(lon2 - lon1)

        x = math.sin(dlon) * math.cos(lat2_r)
        y = (math.cos(lat1_r) * math.sin(lat2_r) -
             math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon))

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360
