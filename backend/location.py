"""
location.py
Live position tracking using the viewer's browser (Geolocation API) as a
stand-in for a real GPS module mounted on the bus.

Only the bus matching ACTIVE_CAMERA_ID (the one with a real camera feed)
can show a "live" fix, since that's the one physical demo vehicle.
All other buses always show a route-based estimate.
"""

import math
import threading
import time

# Approximate real-world coordinates for route endpoints
CITY_COORDS = {
    "Aluva": (10.1075, 76.3516),
    "Ernakulam": (9.9816, 76.2999),
    "Angamaly": (10.1958, 76.3862),
    "Thrissur": (10.5276, 76.2144),
}

# route string (as stored in database.py) -> (origin city, destination city)
ROUTE_ENDPOINTS = {
    "Aluva → Ernakulam": ("Aluva", "Ernakulam"),
    "Angamaly → Ernakulam": ("Angamaly", "Ernakulam"),
    "Thrissur → Ernakulam": ("Thrissur", "Ernakulam"),
}

LIVE_FIX_TIMEOUT = 15  # seconds; older fixes are treated as stale


def bearing(lat1, lng1, lat2, lng2):
    """Compass bearing in degrees (0=N, 90=E, 180=S, 270=W) from point 1 to point 2."""
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlng = lng2 - lng1
    x = math.sin(dlng) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlng)
    theta = math.atan2(x, y)
    return (math.degrees(theta) + 360) % 360


def _haversine_meters(lat1, lng1, lat2, lng2):
    R = 6371000
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class LocationTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._lat = None
        self._lng = None
        self._heading = None
        self._speed = None
        self._last_fix_time = 0

    def update(self, lat, lng, heading=None, speed=None):
        with self._lock:
            if heading is None and self._lat is not None:
                # Estimate heading from movement since the last fix,
                # but ignore tiny jitter from a stationary device.
                moved = _haversine_meters(self._lat, self._lng, lat, lng)
                if moved > 3:
                    heading = bearing(self._lat, self._lng, lat, lng)
                else:
                    heading = self._heading

            self._lat, self._lng = lat, lng
            if heading is not None:
                self._heading = heading
            self._speed = speed
            self._last_fix_time = time.time()

    def get(self, route: str, allow_live: bool = True):
        """
        Returns dict with lat, lng, heading, speed, location_source
        ("live" or "estimated"). Falls back to a fixed point on the
        route when there's no recent live fix, or when allow_live=False
        (used for buses that aren't the active demo vehicle).
        """
        with self._lock:
            is_live = (
                allow_live
                and self._lat is not None
                and (time.time() - self._last_fix_time) < LIVE_FIX_TIMEOUT
            )
            if is_live:
                return {
                    "lat": self._lat,
                    "lng": self._lng,
                    "heading": self._heading,
                    "speed": self._speed,
                    "location_source": "live",
                }

        endpoints = ROUTE_ENDPOINTS.get(route)
        if not endpoints:
            return {"lat": None, "lng": None, "heading": None, "speed": None, "location_source": "unavailable"}

        origin, dest = endpoints
        olat, olng = CITY_COORDS[origin]
        dlat, dlng = CITY_COORDS[dest]
        return {
            "lat": (olat + dlat) / 2,
            "lng": (olng + dlng) / 2,
            "heading": bearing(olat, olng, dlat, dlng),
            "speed": None,
            "location_source": "estimated",
        }


location_tracker = LocationTracker()