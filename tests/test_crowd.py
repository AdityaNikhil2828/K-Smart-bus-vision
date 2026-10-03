"""
Phase 4a: Test crowd logic without the camera.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from crowd import CountSmoother, calculate_occupancy, classify_crowd  # noqa: E402

CAPACITY = 40

print(f"Capacity = {CAPACITY}")
for people in [0, 10, 16, 25, 27, 28, 36, 40, 50]:
    occ = calculate_occupancy(people, CAPACITY)
    label, color = classify_crowd(occ)
    print(f"{people:3d} people -> {occ:6.1f}%  {label:<13} ({color})")

print("\nSmoothing test (one bad frame of 0 in the middle):")
smoother = CountSmoother(window=5)
for raw in [3, 3, 3, 0, 3, 3, 4]:
    print(f"  raw={raw}  smoothed={smoother.update(raw)}")