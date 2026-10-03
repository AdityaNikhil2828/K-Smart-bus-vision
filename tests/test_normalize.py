"""
Phase 13: Test smart bus number normalization.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import normalize_bus_number  # noqa: E402

test_cases = [
    "KL-15-1234",
    "kl151234",
    "KL 15 1234",
    "  kl-15-1234  ",
    "kl_15_1234",
    "Kl-07-5678",
    "kl019999",
    "not-a-plate",
]

for raw in test_cases:
    print(f"{raw!r:20} -> {normalize_bus_number(raw)!r}")