"""
shade.py
Suggests which side of the bus (LEFT or RIGHT) is shadier, based on:
  - the bus's current position (lat/lng)
  - the bus's direction of travel (heading, from location.py)
  - the sun's real position in the sky right now

This is a geometric heuristic based on a straight-line heading, not a
precise GPS-verified recommendation -- the UI is worded to reflect that.
"""

from datetime import datetime, timezone

from astral import Observer
from astral.sun import azimuth, elevation

# Below this elevation (degrees), the sun is at/below the horizon and
# there's no meaningful shade difference between sides.
MIN_SUN_ELEVATION = 5.0

# Within this many degrees of straight ahead/behind, the sun is roughly
# in front of or behind the bus rather than clearly to one side.
FRONT_BACK_TOLERANCE = 20.0


def suggest_shade_side(lat: float, lng: float, heading: float):
    """
    Returns a dict:
        sun_azimuth     : float, degrees
        sun_elevation   : float, degrees
        relative_angle  : float, degrees (sun position relative to heading)
        side            : "LEFT" | "RIGHT" | "NEUTRAL" | "UNAVAILABLE"
        message         : human-readable suggestion
    """
    if lat is None or lng is None or heading is None:
        return {
            "sun_azimuth": None,
            "sun_elevation": None,
            "relative_angle": None,
            "side": "UNAVAILABLE",
            "message": "Position or heading not available yet.",
        }

    now = datetime.now(timezone.utc)
    observer = Observer(latitude=lat, longitude=lng, elevation=0)

    sun_az = azimuth(observer, now)
    sun_el = elevation(observer, now)

    if sun_el < MIN_SUN_ELEVATION:
        return {
            "sun_azimuth": round(sun_az, 1),
            "sun_elevation": round(sun_el, 1),
            "relative_angle": None,
            "side": "NEUTRAL",
            "message": "Sun is low or below the horizon — no real shade difference right now.",
        }

    relative = (sun_az - heading) % 360

    if relative <= FRONT_BACK_TOLERANCE or relative >= (360 - FRONT_BACK_TOLERANCE):
        side = "NEUTRAL"
        message = "Sun is roughly ahead of the bus — both sides get similar light."
    elif abs(relative - 180) <= FRONT_BACK_TOLERANCE:
        side = "NEUTRAL"
        message = "Sun is roughly behind the bus — both sides get similar light."
    elif relative < 180:
        # sun is on the right -> sit left for shade
        side = "LEFT"
        message = "☀️ Sun is on the right — sit on the LEFT side for shade."
    else:
        # sun is on the left -> sit right for shade
        side = "RIGHT"
        message = "☀️ Sun is on the left — sit on the RIGHT side for shade."

    return {
        "sun_azimuth": round(sun_az, 1),
        "sun_elevation": round(sun_el, 1),
        "relative_angle": round(relative, 1),
        "side": side,
        "message": message,
    }