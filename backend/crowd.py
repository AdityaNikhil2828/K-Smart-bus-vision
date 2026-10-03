"""
crowd.py
Turns a person count into occupancy % and a crowd level.
Thresholds are configurable at the top of this file.
"""

from collections import deque
from statistics import median

# (upper limit in %, label, color name) - checked in order, first match wins.
# Anything above the last limit falls into the final entry.
CROWD_LEVELS = [
    (40, "LOW", "green"),
    (70, "MODERATE", "yellow"),
    (90, "CROWDED", "orange"),
    (float("inf"), "VERY CROWDED", "red"),
]

SMOOTHING_WINDOW = 15  # number of recent frames to take the median over


def calculate_occupancy(person_count: int, capacity: int) -> float:
    """Occupancy as a percentage. Can exceed 100 if over capacity."""
    if capacity <= 0:
        return 0.0
    return round(person_count / capacity * 100, 1)


def classify_crowd(occupancy_percent: float):
    """Returns (label, color) for an occupancy percentage."""
    for upper_limit, label, color in CROWD_LEVELS:
        if occupancy_percent < upper_limit:
            return label, color
    return CROWD_LEVELS[-1][1], CROWD_LEVELS[-1][2]


class CountSmoother:
    """Keeps the last N counts and returns their median."""

    def __init__(self, window: int = SMOOTHING_WINDOW):
        self.history = deque(maxlen=window)

    def update(self, count: int) -> int:
        self.history.append(count)
        return int(round(median(self.history)))