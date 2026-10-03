const busInput = document.getElementById("busNumber");
const searchBtn = document.getElementById("searchBtn");
const errorMsg = document.getElementById("errorMsg");
const resultCard = document.getElementById("resultCard");

const busNumberOut = document.getElementById("busNumberOut");
const routeOut = document.getElementById("routeOut");
const videoFeed = document.getElementById("videoFeed");
const cameraOverlay = document.getElementById("cameraOverlay");
const passengersOut = document.getElementById("passengersOut");
const capacityOut = document.getElementById("capacityOut");
const occupancyOut = document.getElementById("occupancyOut");
const crowdOut = document.getElementById("crowdOut");
const cameraStatusOut = document.getElementById("cameraStatusOut");
const loadingSpinner = document.getElementById("loadingSpinner");
const lastUpdatedOut = document.getElementById("lastUpdatedOut");
const normalizedPreview = document.getElementById("normalizedPreview");
const routeQuery = document.getElementById("routeQuery");
const routeSearchBtn = document.getElementById("routeSearchBtn");
const routeResults = document.getElementById("routeResults");
const locationOut = document.getElementById("locationOut");

let normalizeTimer = null;
busInput.addEventListener("input", () => {
  clearTimeout(normalizeTimer);
  const value = busInput.value.trim();
  if (!value) {
    normalizedPreview.textContent = "";
    return;
  }
  normalizeTimer = setTimeout(async () => {
    try {
      const res = await fetch("/api/normalize/" + encodeURIComponent(value));
      const data = await res.json();
      normalizedPreview.textContent = "Will search: " + data.normalized;
      normalizedPreview.classList.toggle(
        "match",
        data.normalized !== value.trim().toUpperCase()
      );
    } catch (e) {
      normalizedPreview.textContent = "";
    }
  }, 250);
});

let currentBus = null;      // bus number currently displayed
let pollTimer = null;

function showError(message) {
  errorMsg.textContent = message;
  errorMsg.classList.remove("hidden");
  resultCard.classList.add("hidden");
}

function clearError() {
  errorMsg.classList.add("hidden");
}

function crowdClass(level) {
  return "crowd-" + level.replace(/\s+/g, "_");
}

function renderBus(data) {
  clearError();
  resultCard.classList.remove("hidden");

  busNumberOut.textContent = "BUS: " + data.bus_number;
  routeOut.textContent = "ROUTE: " + data.route;
  capacityOut.textContent = data.capacity;
  passengersOut.textContent = data.passengers;
  occupancyOut.textContent = data.occupancy_percent + "%";

  crowdOut.textContent = data.crowd_level;
  crowdOut.className = crowdClass(data.crowd_level);

  const isLive = data.camera_status === "LIVE";
  cameraStatusOut.innerHTML = isLive
    ? '<span class="live-dot"></span>LIVE'
    : "🔴 OFFLINE";
  cameraOverlay.classList.toggle("hidden", isLive);

  if (isLive) {
    loadingSpinner.classList.remove("hidden");
    // cache-bust so the browser opens a fresh MJPEG stream
    videoFeed.src = "/api/video_feed?t=" + Date.now();
  } else {
    videoFeed.src = "";
    loadingSpinner.classList.add("hidden");
  }

  lastUpdatedOut.textContent = data.last_updated || "--";
  renderLocation(data);
}

videoFeed.addEventListener("load", () => {
  loadingSpinner.classList.add("hidden");
});
videoFeed.addEventListener("error", () => {
  loadingSpinner.classList.add("hidden");
});

async function fetchBus(busNumber) {
  try {
    const res = await fetch("/api/bus/" + encodeURIComponent(busNumber));
    const data = await res.json();
    if (!res.ok) {
      showError(data.detail || "Bus not found. Please check the bus number.");
      stopPolling();
      return;
    }
    renderBus(data);
  } catch (e) {
    showError("Could not reach the server. Is the backend running?");
    stopPolling();
  }
}

function startPolling(busNumber) {
  stopPolling();
  currentBus = busNumber;
  fetchBus(busNumber);
  // Poll stats every 2s. The <img> tag keeps the MJPEG stream open on its own;
  // we only need to refresh text stats here, not the image.
  pollTimer = setInterval(() => {
    fetch("/api/bus/" + encodeURIComponent(busNumber))
      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        if (!ok) return; // keep showing last good state rather than flicker an error
        passengersOut.textContent = data.passengers;
        occupancyOut.textContent = data.occupancy_percent + "%";
        crowdOut.textContent = data.crowd_level;
        crowdOut.className = crowdClass(data.crowd_level);
        const isLive = data.camera_status === "LIVE";
        cameraStatusOut.innerHTML = isLive
          ? '<span class="live-dot"></span>LIVE'
          : "🔴 OFFLINE";
        cameraOverlay.classList.toggle("hidden", isLive);
                lastUpdatedOut.textContent = data.last_updated || "--";
        renderLocation(data);
      })
      .catch(() => {});
  }, 2000);
}

function stopPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = null;
  currentBus = null;
}

let map = null;
let busMarker = null;

function initMap(lat, lng) {
  if (map || lat == null || lng == null) return;
  map = L.map("busMap").setView([lat, lng], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);

  const icon = L.divIcon({
    className: "bus-marker-icon",
    html: '<div class="bus-arrow">🚌</div>',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
  busMarker = L.marker([lat, lng], { icon }).addTo(map);
}

function updateMap(lat, lng, heading) {
  if (lat == null || lng == null) return;
  if (!map) {
    initMap(lat, lng);
  } else {
    busMarker.setLatLng([lat, lng]);
    map.panTo([lat, lng]);
  }
  const arrowEl = document.querySelector(".bus-arrow");
  if (arrowEl && heading != null) {
    arrowEl.style.transform = `rotate(${heading}deg)`;
  }
}

function renderLocation(data) {
  updateMap(data.lat, data.lng, data.heading);
  if (data.location_source === "live") {
    locationOut.textContent = "🟢 Live GPS";
  } else if (data.location_source === "estimated") {
    locationOut.textContent = "📍 Estimated";
  } else {
    locationOut.textContent = "--";
  }
}

let lastSentTime = 0;
function startGeolocation() {
  if (!navigator.geolocation) {
    console.warn("Geolocation not supported by this browser.");
    return;
  }
  navigator.geolocation.watchPosition(
    (pos) => {
      const now = Date.now();
      if (now - lastSentTime < 3000) return; // throttle to once per 3s
      lastSentTime = now;
      const { latitude, longitude, heading, speed } = pos.coords;
      fetch("/api/location", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lat: latitude, lng: longitude, heading, speed }),
      }).catch(() => {});
    },
    (err) => console.warn("Geolocation error:", err.message),
    { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
  );
}

async function searchByRoute() {
  const query = routeQuery.value.trim();
  if (!query) return;

  try {
    const res = await fetch("/api/search_route/" + encodeURIComponent(query));
    const data = await res.json();

    if (!res.ok) {
      routeResults.innerHTML = `<div class="route-result-item">${data.detail}</div>`;
      routeResults.classList.remove("hidden");
      return;
    }

    routeResults.innerHTML = data
      .map(
        (bus) => `
        <div class="route-result-item" data-bus="${bus.bus_number}">
          <span class="bus-num">${bus.bus_number}</span>
          <span class="bus-route">${bus.route}</span>
        </div>`
      )
      .join("");
    routeResults.classList.remove("hidden");

    // Clicking a result loads it into the main dashboard card
    routeResults.querySelectorAll(".route-result-item[data-bus]").forEach((el) => {
      el.addEventListener("click", () => {
        const busNum = el.getAttribute("data-bus");
        busInput.value = busNum;
        normalizedPreview.textContent = "";
        routeResults.classList.add("hidden");
        startPolling(busNum);
      });
    });
  } catch (e) {
    routeResults.innerHTML = `<div class="route-result-item">Could not reach the server.</div>`;
    routeResults.classList.remove("hidden");
  }
}

routeSearchBtn.addEventListener("click", searchByRoute);
routeQuery.addEventListener("keydown", (e) => {
  if (e.key === "Enter") searchByRoute();
});

searchBtn.addEventListener("click", () => {
  const value = busInput.value.trim();
  if (!value) return;
  startPolling(value);
});

busInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") searchBtn.click();
});

// Auto-search the default bus on page load
window.addEventListener("DOMContentLoaded", () => {
  searchBtn.click();
  startGeolocation();
});