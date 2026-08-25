# 🖥️ Web Dashboard Reference Guide

The Web Dashboard is the **single control point** for the entire robot system. It is a Flask + Three.js application running at `http://localhost:5050` inside the DevContainer. You do NOT need to use the command line for normal operations — everything from starting SLAM to saving maps is accessible from the browser.

---

## Table of Contents

1. [Architecture & Design](#architecture--design)
2. [Starting the Dashboard](#starting-the-dashboard)
3. [UI Sections and Buttons](#ui-sections-and-buttons)
4. [Full REST API Reference](#full-rest-api-reference)
5. [Server-Sent Events (SSE) Telemetry Stream](#server-sent-events-sse-telemetry-stream)
6. [PID Singleton — Process Lifecycle](#pid-singleton--process-lifecycle)
7. [Defensive REST Rules](#defensive-rest-rules)
8. [Troubleshooting Dashboard Issues](#troubleshooting-dashboard-issues)

---

## Architecture & Design

```
Browser (http://localhost:5050)
         │
         │  HTTP REST + SSE stream
         ▼
┌────────────────────────────────────────────────────────────┐
│  Flask app.py  (Port 5050)                                  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ROS Listener Thread (non-blocking, background)      │   │
│  │  Subscribes: /imu/data, /scan, /tf                   │   │
│  │  Writes to: shared telemetry dict (thread-safe)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  Flask Routes → subprocess/SSH → ROS nodes / Uno Q          │
└────────────────────────────────────────────────────────────┘
```

**Key design principles:**
- The ROS listener thread runs in the background and **never blocks Flask routes**
- Flask routes are non-blocking — button clicks return within milliseconds
- The SSE stream at `/api/stream` pushes live telemetry to the browser without polling
- A PID lockfile prevents duplicate dashboard instances

---

## Starting the Dashboard

### Method 1: From host machine (recommended)

```bash
cd ~/my_robot_ws
./start_dashboard.sh
```

`start_dashboard.sh` automatically:
- Detects whether you are inside the DevContainer or on the host
- Kills any previous dashboard instance via the PID lockfile
- Sets all required environment variables (ROS_DOMAIN_ID=42, RMW_IMPLEMENTATION, CYCLONEDDS_URI)
- Runs `python3 src/my_robot_dashboard/app.py` in the correct context

You should see:
```
=========================================================
  STARTING DISTRIBUTED ROS 2 ROBOT CONTROL HUB
  Web UI: http://localhost:5050
=========================================================
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5050
```

### Method 2: Directly inside the DevContainer

```bash
cd /home/ros/my_robot_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
export PORT=5050
python3 src/my_robot_dashboard/app.py
```

### Method 3: Verify it's running

```bash
curl -s http://localhost:5050/ | head -5
# Should return the first few lines of the HTML dashboard
```

---

## UI Sections and Buttons

### Header Bar

- **System status indicator** — green = connected to ROS, red = no ROS data
- **Uno Q IP address field** — editable, defaults to `192.168.1.17`
- **"Shutdown All & Exit"** button — emergency full system shutdown

---

### System Configuration Panel

**"Set Uno Q IP"** — Updates the IP the dashboard uses to SSH into the edge board.  
Use this if the Uno Q's IP changes after a router restart.

```bash
curl -X POST http://localhost:5050/api/config/ip \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.17"}'
```

---

### Sensor Controls Panel

These buttons SSH into the Uno Q and control the sensor Docker container.

| Button | What it does | CLI equivalent |
|--------|-------------|----------------|
| **Start LiDAR** | Runs `bash /home/arduino/start_rplidar.sh` on Uno Q | `curl -X POST http://localhost:5050/api/sensors/lidar/start -H "Content-Type: application/json" -d '{}'` |
| **Stop LiDAR** | `sudo docker stop rplidar` on Uno Q | `curl -X POST http://localhost:5050/api/sensors/lidar/stop -H "Content-Type: application/json" -d '{}'` |
| **Start IMU** | Starts/restarts `imu_publisher.py` in the container | `curl -X POST http://localhost:5050/api/sensors/imu/start -H "Content-Type: application/json" -d '{}'` |
| **Stop IMU** | Kills `imu_publisher.py` | `curl -X POST http://localhost:5050/api/sensors/imu/stop -H "Content-Type: application/json" -d '{}'` |
| **Restart Router** | `sudo systemctl restart arduino-router` on Uno Q | `curl -X POST http://localhost:5050/api/sensors/router/restart -H "Content-Type: application/json" -d '{}'` |
| **Reboot Uno Q** | `sudo reboot` on Uno Q | `curl -X POST http://localhost:5050/api/sensors/unoq/reboot -H "Content-Type: application/json" -d '{}'` |

---

### SLAM & Mapping Panel

#### "Start SLAM" button

**What it does, step by step:**
1. Launches `qos_relay.py` as a background subprocess:
   - Publishes `odom → base_link` dynamic TF at 50 Hz
   - Subscribes to `/imu/data` to get orientation
   - Computes tilt = sqrt(roll² + pitch²). If tilt > 7.5°, filters out laser rays where |r × sin(θ)| > 0.40 m (removes floor/ceiling hits during handheld movement)
   - Re-publishes filtered scan as `/scan_reliable` with RELIABLE QoS for SLAM
2. Waits 1 second for TF tree to stabilize
3. Launches `slam_toolbox` via `imu_slam.launch.py`
4. Waits 3.5 seconds for the lifecycle node to configure → activate
5. Opens RViz2 with the SLAM display configuration

**CLI:**
```bash
curl -X POST http://localhost:5050/api/slam/start \
  -H "Content-Type: application/json" -d '{}'

# Response:
# {"status": "ok", "message": "SLAM pipeline started"}
```

#### "Stop SLAM" button

Kills `qos_relay.py` and `slam_toolbox`. Does NOT kill RViz2.

```bash
curl -X POST http://localhost:5050/api/slam/stop \
  -H "Content-Type: application/json" -d '{}'
```

#### "Save Map" button

Calls `ros2 run nav2_map_server map_saver_cli` to save the current live map.

**Output files** (written to `src/my_robot_nav/maps/`):
- `<timestamp>_map.pgm` — grayscale occupancy image (white=free, black=wall, grey=unknown)
- `<timestamp>_map.yaml` — metadata file:
  ```yaml
  image: my_map.pgm
  resolution: 0.05      # 5 cm per pixel
  origin: [-5.0, -5.0, 0.0]
  negate: 0
  occupied_thresh: 0.65
  free_thresh: 0.25
  ```

```bash
# Save with auto timestamp filename
curl -X POST http://localhost:5050/api/slam/save_map \
  -H "Content-Type: application/json" -d '{}'

# Save with custom name
curl -X POST http://localhost:5050/api/slam/save_map \
  -H "Content-Type: application/json" \
  -d '{"filename": "office_floor1"}'
```

#### "Snap to 90° Boxy Walls" button

Runs `map_regularizer.py` on the most recently saved map to produce clean orthogonal walls.

**Processing pipeline inside `map_regularizer.py`:**
1. Load `.pgm` occupancy grid image
2. Binary threshold to isolate wall pixels
3. Morphological closing (`cv2.morphologyEx`) to fill small wall gaps
4. Probabilistic Hough Line Transform (`cv2.HoughLinesP`) to detect wall segments
5. Build weighted angle histogram of all detected line orientations
6. Find dominant building orientation **θ_dom** (peak of histogram)
7. Snap every line segment to nearest: θ_dom, θ_dom+90°, θ_dom+180°, θ_dom+270°
8. Re-draw snapped walls on clean occupancy grid
9. Export three files:
   - `<map>_regularized.pgm` — clean raster map with orthogonal walls
   - `<map>_regularized.yaml` — identical metadata to original
   - `<map>_regularized.svg` — vector SVG for CAD / architectural import

```bash
curl -X POST http://localhost:5050/api/slam/regularize_map \
  -H "Content-Type: application/json" -d '{}'
```

---

### RViz2 Controls Panel

| Button | What it does |
|--------|-------------|
| **Launch RViz2 (scan)** | Opens RViz2 showing live `/scan` — for testing LiDAR alone |
| **Launch RViz2 (SLAM)** | Opens RViz2 with map + scan + TF — use during mapping |
| **Launch RViz2 (IMU)** | Opens RViz2 with IMU orientation visualization |
| **Stop RViz2** | Kills the RViz2 process |

```bash
# Launch in SLAM mode (most common)
curl -X POST http://localhost:5050/api/rviz/launch/slam \
  -H "Content-Type: application/json" -d '{}'

# Launch in LiDAR-only mode
curl -X POST http://localhost:5050/api/rviz/launch/scan \
  -H "Content-Type: application/json" -d '{}'

# Stop RViz2
curl -X POST http://localhost:5050/api/rviz/stop \
  -H "Content-Type: application/json" -d '{}'
```

---

### System Operations Panel

#### "Reset Nodes" button — **Soft Reset**

Kills all ROS 2 processes (SLAM, qos_relay, RViz2, sensor nodes) but **keeps the Flask dashboard running**. Use this when something is stuck and you want to restart SLAM without restarting the web interface.

```bash
curl -X POST http://localhost:5050/api/system/kill_all \
  -H "Content-Type: application/json" -d '{}'

# Response:
# {"status": "ok", "message": "All ROS activity killed"}
```

#### "Shutdown All & Exit" button — **Full Shutdown**

Kills all ROS nodes **AND exits `app.py`**. Port 5050 is fully released. Use when ending the session or when the dashboard itself needs to be restarted.

```bash
curl -X POST http://localhost:5050/api/system/shutdown_all \
  -H "Content-Type: application/json" -d '{}'
```

After this, restart with: `./start_dashboard.sh`

---

### Telemetry Stream Panel

The telemetry panel shows live data pushed from the Flask server via SSE:

| Field | What it shows |
|-------|--------------|
| **IMU Quaternion W/X/Y/Z** | Raw quaternion from BNO086 Game Rotation Vector |
| **Roll / Pitch / Yaw** | Euler angles in degrees, derived from quaternion |
| **Scan Hz** | Live laser scan frequency (should be ~10 Hz) |
| **Tilt Guard** | "Active" (red) when tilt > 7.5° — scan rays are being filtered |
| **TF Status** | Whether `odom → base_link` transform is being published |

```bash
# Raw SSE stream from terminal
curl -N http://localhost:5050/api/stream

# Sample output:
# data: {"imu": {"w": 0.998, "x": 0.001, "y": 0.004, "z": -0.012, "roll": 0.45, "pitch": 0.23, "yaw": 12.1}, "scan_hz": 10.003, "tilt_deg": 0.51}
# data: {"imu": {"w": 0.997, ...}, "scan_hz": 9.998, "tilt_deg": 0.49}
```

---

### Map Gallery Panel

Shows all maps in `src/my_robot_nav/maps/`. Each entry shows:
- Map name and creation timestamp
- File size
- **"Boxy 90°" badge** if a `_regularized.pgm` counterpart exists

```bash
# Get map list as JSON
curl http://localhost:5050/api/slam/list_maps

# Sample response:
# {
#   "maps": [
#     {
#       "name": "20260825_120000_map",
#       "pgm": "20260825_120000_map.pgm",
#       "yaml": "20260825_120000_map.yaml",
#       "has_regularized": true,
#       "size_kb": 234
#     }
#   ]
# }
```

---

## Full REST API Reference

All POST endpoints accept an empty `{}` body (no required fields unless noted). All responses are JSON.

```bash
# ── SLAM CONTROL ──────────────────────────────────────────────────────────

# Start SLAM pipeline (qos_relay + slam_toolbox + RViz2)
curl -X POST http://localhost:5050/api/slam/start \
  -H "Content-Type: application/json" -d '{}'

# Stop SLAM (kills qos_relay and slam_toolbox)
curl -X POST http://localhost:5050/api/slam/stop \
  -H "Content-Type: application/json" -d '{}'

# Save current map (optional: {"filename": "my_name"})
curl -X POST http://localhost:5050/api/slam/save_map \
  -H "Content-Type: application/json" -d '{}'

# Snap walls to 90° orthogonal (Manhattan regularizer)
curl -X POST http://localhost:5050/api/slam/regularize_map \
  -H "Content-Type: application/json" -d '{}'

# List saved maps
curl http://localhost:5050/api/slam/list_maps

# ── SENSOR CONTROL (SSH → Uno Q) ──────────────────────────────────────────

curl -X POST http://localhost:5050/api/sensors/lidar/start   -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:5050/api/sensors/lidar/stop    -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:5050/api/sensors/imu/start     -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:5050/api/sensors/imu/stop      -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:5050/api/sensors/router/restart -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:5050/api/sensors/unoq/reboot   -H "Content-Type: application/json" -d '{}'

# ── RVIZ2 ─────────────────────────────────────────────────────────────────

curl -X POST http://localhost:5050/api/rviz/launch/slam  -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:5050/api/rviz/launch/scan  -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:5050/api/rviz/launch/imu   -H "Content-Type: application/json" -d '{}'
curl -X POST http://localhost:5050/api/rviz/stop         -H "Content-Type: application/json" -d '{}'

# ── SYSTEM ────────────────────────────────────────────────────────────────

# Soft reset — kill ROS nodes, keep dashboard running
curl -X POST http://localhost:5050/api/system/kill_all \
  -H "Content-Type: application/json" -d '{}'

# Full shutdown — kill nodes AND exit app.py
curl -X POST http://localhost:5050/api/system/shutdown_all \
  -H "Content-Type: application/json" -d '{}'

# ── TELEMETRY ─────────────────────────────────────────────────────────────

# JSON snapshot of latest telemetry
curl http://localhost:5050/api/telemetry

# Live SSE stream (Ctrl+C to stop)
curl -N http://localhost:5050/api/stream

# ── CONFIG ────────────────────────────────────────────────────────────────

# Update Uno Q IP address
curl -X POST http://localhost:5050/api/config/ip \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.17"}'
```

---

## Server-Sent Events (SSE) Telemetry Stream

The `/api/stream` endpoint keeps an HTTP connection open and pushes events continuously.

**From JavaScript (in browser):**
```javascript
const evtSource = new EventSource('/api/stream');
evtSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    document.getElementById('yaw').innerText = data.imu.yaw.toFixed(1) + '°';
    document.getElementById('scan-hz').innerText = data.scan_hz.toFixed(1) + ' Hz';
};
```

**From curl (terminal):**
```bash
curl -N http://localhost:5050/api/stream
# Output (one line per event, ~10 Hz):
# data: {"imu": {"w": 0.998, "x": 0.001, "y": 0.004, "z": -0.012, "roll": 0.45, "pitch": 0.23, "yaw": 12.1}, "scan_hz": 10.003, "tilt_deg": 0.51}
```

---

## PID Singleton — Process Lifecycle

To prevent duplicate instances (which cause port conflicts and DDS collisions), `app.py` uses a PID lockfile.

**Lockfile location:** `/tmp/my_robot_dashboard.pid`

**Startup sequence:**
1. Check for `/tmp/my_robot_dashboard.pid`
2. If PID exists and process is alive → send `SIGTERM`, wait up to 2.0s for port 5050 to free
3. Write new PID to lockfile
4. Bind to port 5050, start Flask

**Manual cleanup if stuck:**
```bash
# See current lockfile PID
cat /tmp/my_robot_dashboard.pid

# Kill it
kill -9 $(cat /tmp/my_robot_dashboard.pid)

# Remove stale lockfile
rm -f /tmp/my_robot_dashboard.pid

# Kill anything still on port 5050
kill -9 $(lsof -ti:5050)

# Now start fresh
./start_dashboard.sh
```

---

## Defensive REST Rules

These rules MUST be followed when adding new endpoints to `app.py` or modifying `app.js`.

### Backend — `app.py`

**Always use `get_json(silent=True)`:**
```python
# CORRECT — handles empty body, missing Content-Type, malformed JSON
req_data = request.get_json(silent=True) or {}
filename = req_data.get('filename', 'default_name')

# WRONG — throws HTTP 400 if body is empty or Content-Type is missing
req_data = request.json  # ← Never use this
```

**Why:** When a browser sends a POST with an empty `{}` body and no explicit Content-Type, Flask's `request.json` property raises Werkzeug's `400 Bad Request` internally, before your view function even runs. Using `get_json(silent=True)` suppresses this and returns `None`, which the `or {}` converts to a safe empty dict.

### Frontend — `app.js`

**Always serialize body and parse text safely:**
```javascript
// CORRECT
const res = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload || {})   // Always send valid JSON, even for empty calls
});
const text = await res.text();            // Read as text first
try {
    return JSON.parse(text);              // Try to parse
} catch (e) {
    console.error('Server returned non-JSON:', text);
    return {error: text};
}

// WRONG — throws SyntaxError when server returns an HTML error page
const data = await res.json();  // ← Never call this directly
```

### Cache Busting

After every change to `static/js/app.js`, bump the version in `templates/index.html`:
```html
<!-- Change ?v=5.0 to ?v=5.1 or whatever the next version is -->
<script src="/static/js/app.js?v=5.0"></script>
```

This forces the browser to download the new file instead of serving the cached old one.

---

## Troubleshooting Dashboard Issues

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| **"Connection refused" on http://localhost:5050** | Dashboard not running | `./start_dashboard.sh` from workspace root |
| **404 on API endpoints** | Wrong URL format | All paths are `/api/...` — double-check spelling |
| **400 Bad Request** | Route using `request.json` instead of `get_json(silent=True)` | Audit `app.py` — every POST route must use `request.get_json(silent=True) or {}` |
| **`SyntaxError: JSON.parse` in browser console** | Stale cached `app.js` | Hard-refresh: **Ctrl+Shift+R**. Bump `?v=X.X` in `index.html` |
| **Port 5050 already in use** | Old instance still running | `kill -9 $(lsof -ti:5050)` then `./start_dashboard.sh` |
| **Two dashboard windows fighting** | Two `app.py` processes started | Kill both: `pkill -9 -f app.py` then restart |
| **Buttons do nothing after clicking** | ROS env not sourced in app.py context | Check terminal for env errors. Start via `./start_dashboard.sh` which sets all env vars |
| **Telemetry shows zeros** | ROS listener thread can't subscribe | Ensure ROS 2 is available in the container. Check that `/imu/data` is being published: `ros2 topic hz /imu/data` |
| **SSE stream disconnects every ~30s** | Corporate proxy buffering / timeout | Disable proxy for localhost, or access via `http://127.0.0.1:5050` instead |
