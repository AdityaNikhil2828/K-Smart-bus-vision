"""
Phase 7: Test the bus database.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from database import DB_PATH, get_bus, init_db, list_buses  # noqa: E402

init_db()
print(f"Database file: {DB_PATH}\n")

print("All buses:")
for bus in list_buses():
    print(f"  {bus['bus_number']}  {bus['route']:<24} cap={bus['capacity']}  {bus['camera_id']}  {bus['status']}")

print("\nLookup tests:")
for query in ["KL-15-1234", "  kl-07-5678 ", "KL-99-0000"]:
    result = get_bus(query)
    print(f"  {query!r:16} -> {result if result else 'Bus not found.'}")