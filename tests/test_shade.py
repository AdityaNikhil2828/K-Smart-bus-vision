"""
Phase 16: Test the shade-side suggestion logic with made-up scenarios.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from shade import suggest_shade_side  # noqa: E402

# Aluva, Kerala coordinates (one of our real routes)
LAT, LNG = 10.1075, 76.3516

print("Current real result for Aluva, with different headings:\n")
for heading, label in [(0, "North"), (90, "East"), (180, "South"), (270, "West")]:
    result = suggest_shade_side(LAT, LNG, heading)
    print(f"Heading {heading:>3}° ({label:<5}): {result}")

print("\nMissing data test:")
print(suggest_shade_side(None, None, None))