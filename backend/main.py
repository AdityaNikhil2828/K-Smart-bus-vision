"""
main.py
FastAPI backend for Smart Bus Vision.
Phase 16: bus-number search, route search, live location, and shade suggestion.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from camera import CameraStream  # noqa: E402
from crowd import calculate_occupancy, classify_crowd  # noqa: E402
from database import get_bus, init_db, list_buses, search_by_route  # noqa: E402
from location import location_tracker  # noqa: E402
from shade import suggest_shade_side  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# This prototype has ONE physical camera. Its id is "camera_01".
# Buses whose camera_id matches this are considered to have a live feed;
# others are treated as offline, simulating a camera that isn't installed yet.
ACTIVE_CAMERA_ID = "camera_01"
class LocationUpdate(BaseModel):
    lat: float
    lng: float
    heading: float | None = None
    speed: float | None = None

camera = CameraStream()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    camera.start()
    yield
    camera._stop.set()
    camera.stop()


app = FastAPI(title="Smart Bus Vision", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/location")
def update_location(loc: LocationUpdate):
    location_tracker.update(loc.lat, loc.lng, loc.heading, loc.speed)
    return {"status": "ok"}

@app.get("/api/search_route/{query}")
def route_search(query: str):
    results = search_by_route(query)
    if not results:
        raise HTTPException(status_code=404, detail="No buses found on that route.")
    return results


@app.get("/api/buses")
def buses():
    """List all known buses. Handy for the dashboard and for debugging."""
    return list_buses()

@app.get("/api/normalize/{raw_text}")
def normalize_preview(raw_text: str):
    """Used by the frontend to show a live-corrected bus number as the user types."""
    from database import normalize_bus_number
    return {"normalized": normalize_bus_number(raw_text)}


@app.get("/api/bus/{bus_number}")

def bus_lookup(bus_number: str):
    bus = get_bus(bus_number)
    if bus is None:
        raise HTTPException(status_code=404, detail="Bus not found. Please check the bus number.")

    state = camera.get_state()
    camera_matches = bus["camera_id"] == ACTIVE_CAMERA_ID
    camera_live = camera_matches and state["camera_online"]

    passengers = state["passengers"] if camera_live else 0
    occupancy = calculate_occupancy(passengers, bus["capacity"])
    level, color = classify_crowd(occupancy)

    is_active_bus = bus["camera_id"] == ACTIVE_CAMERA_ID
    loc = location_tracker.get(bus["route"], allow_live=is_active_bus)
    shade = suggest_shade_side(loc["lat"], loc["lng"], loc["heading"])

    return {
        "bus_number": bus["bus_number"],
        "route": bus["route"],
        "capacity": bus["capacity"],
        "camera_id": bus["camera_id"],
        "bus_status": bus["status"],
        "camera_status": "LIVE" if camera_live else "OFFLINE",
        "passengers": passengers,
        "occupancy_percent": occupancy,
        "crowd_level": level,
        "crowd_color": color,
        "detector_error": state["detector_error"],
        "last_updated": state["last_updated"],
        "lat": loc["lat"],
        "lng": loc["lng"],
        "heading": loc["heading"],
        "speed": loc["speed"],
        "location_source": loc["location_source"],
        "shade_side": shade["side"],
        "shade_message": shade["message"],
        "sun_azimuth": shade["sun_azimuth"],
        "sun_elevation": shade["sun_elevation"],
    }


@app.get("/api/video_feed")
def video_feed():
    return StreamingResponse(
        camera.mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/test_page")
def test_page():
    """Temporary page to try bus lookup. Replaced by the real dashboard in Phase 9."""
    return HTMLResponse(
        """
        <h2>Phase 8 test</h2>
        <input id="busnum" value="KL-15-1234">
        <button onclick="lookup()">Search</button>
        <pre id="result"></pre>
        <img id="feed" src="" style="max-width:640px; display:none;">
        <script>
        async function lookup() {
            const num = document.getElementById('busnum').value;
            const res = await fetch('/api/bus/' + encodeURIComponent(num));
            const data = await res.json();
            document.getElementById('result').textContent = JSON.stringify(data, null, 2);
            const img = document.getElementById('feed');
            if (res.ok && data.camera_status === 'LIVE') {
                img.src = '/api/video_feed?' + Date.now();
                img.style.display = 'block';
            } else {
                img.style.display = 'none';
            }
        }
        </script>
        """
    )


@app.get("/")
def home():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Smart Bus Vision backend is running. Dashboard not created yet."}