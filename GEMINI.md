# GEMINI.md — Distributed ROS 2 Robot: Master AI Agent Memory

> **CRITICAL RULE FOR ALL AI AGENTS & MODELS**:
> Before performing ANY task — writing code, modifying config, answering questions, or debugging —
> you MUST read and internalize this entire file first. This is not optional.
> This file exists because models switch, context windows truncate, and the same mistakes keep being
> made when agents don't have full project context. Every section below was written because of a
> real failure that cost hours of debugging.

---

## ⚡ 0. MANDATORY PRE-FLIGHT CHECKLIST (RUN BEFORE EVERY TASK)

Before touching any code, run through this checklist mentally:

- [ ] Did I read ALL sections of this file?
- [ ] Do I know which file I'm editing and its exact role in the system?
- [ ] Am I about to use `request.json`? → STOP. Use `request.get_json(silent=True) or {}`.
- [ ] Am I about to call `res.json()` in JavaScript? → STOP. Use `res.text()` + try/catch.
- [ ] Am I about to start a new process? → Check for zombies first with `ps aux | grep ...`
- [ ] Am I adding a new feature? → Will it break the Web UI, sensor stream, or SLAM? (Rule 4)
- [ ] Am I declaring something "done"? → Have I verified with real terminal output? (Rule 3)
- [ ] Does this task need a GitHub issue? → Create one with `gh issue create`. (Rule 7)
- [ ] Did I bump the JS cache version in `index.html` if I touched `app.js`? (Rule 2)

---

## 🛑 SECTION 1: ANTI-MISTAKE RULES (ORDERED BY SEVERITY)

### Rule 1 — Zero Zombie / Duplicate Instances

**Past mistake:** Running multiple parallel scripts (`telemetry_bridge.py`, separate `qos_relay.py`,
duplicate `app.py`) caused competing DDS participants, port collisions (5050 → 5051), and stale
sockets. This caused 4–5 hours of debugging.

**What is enforced:**
- `app.py` uses a PID lockfile at `/tmp/my_robot_dashboard.pid`
- On startup: reads lockfile → sends `SIGTERM` to old PID → polls for port 5050 release (up to 2.0s) → writes new PID → binds port
- `start_dashboard.sh` is the ONLY way to start the dashboard — it handles all of this
- Never run `python3 app.py` from two terminals simultaneously
- Never run a standalone `qos_relay.py` when the dashboard already manages it

**Before starting anything, always check:**
```bash
ps aux | grep -E "app.py|qos_relay|slam_toolbox|rviz2" | grep -v grep
lsof -i :5050
cat /tmp/my_robot_dashboard.pid
```

**Emergency cleanup:**
```bash
pkill -9 -f "app.py|qos_relay|slam_toolbox"
rm -f /tmp/my_robot_dashboard.pid
kill -9 $(lsof -ti:5050)
```

---

### Rule 2 — Defensive REST & Frontend Serialization

**Past mistake 1:** Used `request.json` on Flask POST endpoints. When the browser sent an empty
body (0 bytes) with `Content-Type: application/json`, Werkzeug threw HTTP 400 before the view
function even ran. Symptoms: "400 Bad Request" on every button click.

**Past mistake 2:** Called `res.json()` directly in JavaScript. When the server returned an HTML
error page (due to the above 400), the browser threw `SyntaxError: JSON.parse: unexpected character
at line 1 column 1`. The actual error was invisible.

**Past mistake 3:** Browser cached old `app.js` after JS was updated. New API functions weren't
accessible because the browser served a 3-week-old cached version.

**The ONLY correct patterns:**

**Backend — every single POST route in `app.py`:**
```python
# CORRECT — always, no exceptions:
req_data = request.get_json(silent=True) or {}
filename = req_data.get('filename', 'default')

# WRONG — never use this:
req_data = request.json  # throws 400 on empty body
```

**Frontend — every single API call in `app.js`:**
```javascript
// CORRECT — always:
async function apiCall(url, payload = {}) {
    const res = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)  // always stringify, even {}
    });
    const text = await res.text();    // always read as text first
    try {
        return JSON.parse(text);      // then try to parse
    } catch (e) {
        console.error('Non-JSON response:', text);
        return {error: text};
    }
}

// WRONG — never use this:
const data = await res.json();  // explodes on HTML error responses
```

**Cache busting — every time `app.js` is modified:**
```html
<!-- In templates/index.html — bump version number every edit -->
<script src="/static/js/app.js?v=5.0"></script>
<!-- Change to ?v=5.1, ?v=6.0, etc. -->
```

---

### Rule 3 — End-to-End Verification (Never Assume "Done")

**Past mistake:** Reported SLAM was working based on code review alone, without checking that
TF frames were actually publishing, that scans were arriving at the correct rate, or that the
map appeared in RViz.

**Verification sequence that MUST pass before any task is "done":**

```bash
# Inside the DevContainer, source first:
source /opt/ros/jazzy/setup.bash
source /home/ros/my_robot_ws/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml

# 1. Sensor health (must show ~10 Hz and ~100 Hz respectively)
ros2 topic hz /scan
ros2 topic hz /imu/data

# 2. TF tree (must show map → odom → base_link → laser after SLAM starts)
ros2 run tf2_ros tf2_echo odom base_link

# 3. API health (all must return 200 with JSON body)
curl -s -o /dev/null -w "%{http_code}" http://localhost:5050/
curl -X POST http://localhost:5050/api/system/kill_all \
  -H "Content-Type: application/json" -d '{}' | python3 -m json.tool
```

---

### Rule 4 — Strict Component Isolation (No Cross-Layer Coupling)

**Past mistake:** Adding map regularizer code inside `app.py`'s sensor callback caused the
telemetry SSE stream to freeze whenever regularization ran, because OpenCV operations blocked
the ROS listener thread.

**The layered architecture — NEVER break these boundaries:**

```
Layer 1: Web UI (index.html + app.js)
    ↕ HTTP REST / SSE only
Layer 2: Flask Backend (app.py)
    - Routes call subprocess.Popen() — they NEVER block
    - ROS listener thread is SEPARATE from Flask thread pool
    - Telemetry dict is updated by ROS thread, read by Flask routes
    ↕ subprocess / SSH
Layer 3: Bridge (qos_relay.py) — standalone daemon, never imported
Layer 4: SLAM (slam_toolbox) — standalone ROS node
Layer 5: Post-processing (map_regularizer.py) — called on-demand, never in callbacks
```

**If you need to add a feature:**
- New REST endpoint? → Add a route to `app.py`, call subprocess
- New sensor processing? → Add to `qos_relay.py`, keep callback non-blocking
- New post-processing? → New script called from `app.py` route, never inline
- New UI element? → Add to `index.html` + `app.js`, never change Python for UI logic

---

### Rule 5 — Tilt-Aware Scan Gating (Do Not Remove or Loosen)

**Past mistake:** Handheld walking caused 3°–8° pitch/roll tilt. At 8° tilt, a 16m laser ray
aimed at a wall actually hits the floor at `16 × sin(8°) = 2.22m` height deviation — corrupting
the 2D SLAM map with ghost walls along the floor/ceiling plane.

**The gating logic in `qos_relay.py`:**
```python
tilt = sqrt(roll² + pitch²)
if tilt > 7.5°:
    for each range r in scan.ranges:
        height_deviation = r * sin(tilt)
        if abs(height_deviation) > 0.40:
            ranges[i] = float('inf')  # gate out this ray
```

**SLAM tuning parameters (slam_toolbox_params.yaml) — do not change without reason:**
```yaml
correlation_search_space_dimension: 0.80  # handles walking up to 0.8 m/s
loop_search_maximum_distance: 12.0        # full floor plan search radius
scan_buffer_size: 30                      # scan history for loop closure
transform_timeout: 0.25                   # must be high enough for Wi-Fi jitter
use_scan_barycenter: false                # was causing Ceres matrix crashes
use_response_expansion: false             # was causing Ceres matrix crashes
```

---

### Rule 6 — Map Regularizer Outputs Three Files (Not One)

**What `map_regularizer.py` produces from input `my_map.pgm`:**
- `my_map_regularized.pgm` — raster occupancy grid with orthogonal walls
- `my_map_regularized.yaml` — identical metadata to original
- `my_map_regularized.svg` — vector CAD export (Inkscape / AutoCAD compatible)

**The SVG is important** — it's the architectural floorplan output. Do not remove it.

**The regularizer pipeline:**
1. Load `.pgm` → binary threshold (walls = black pixels)
2. `cv2.morphologyEx(MORPH_CLOSE)` — fill small gaps in walls
3. `cv2.HoughLinesP()` — extract wall line segments
4. Build angle histogram, find θ_dom (dominant building orientation)
5. For each detected segment, snap angle to nearest: θ_dom, θ_dom+90°, θ_dom+180°, θ_dom+270°
6. Re-draw snapped segments on clean canvas
7. Save .pgm, .yaml (copy of original metadata), .svg

---

### Rule 7 — GitHub Issue Lifecycle

**For every bug, feature, or architectural change:**
```bash
# Create issue
gh issue create --title "Short description" --body "Details" --label "bug"

# Reference in commits
git commit -m "fix(component): description (#N)"

# Close with post-mortem
gh issue close N --comment "Root cause: ... Solution: ... Files changed: ..."
```

**Current issues #1–#9 are all closed. Next issue will be #10.**
Check open issues: `gh issue list --state open`


---

## 📁 SECTION 2: COMPLETE FILE MAP (WHAT EVERY FILE DOES)

Every agent must know the role of every key file before touching it.

### Root Level
| File | Role | Touch when... |
|------|------|---------------|
| `start_dashboard.sh` | Single entry point — detects host/container, cleans old instances with bash pkill, sets env vars, runs `app.py` | Changing startup behavior |
| `stop_dashboard.sh` | Full teardown — terminates all ROS nodes, bridges, RViz2, and Flask on both host and inside container | Halting all system components |
| `restart_dashboard.sh` | Clean restart — invokes stop_dashboard.sh then start_dashboard.sh | Restarting cleanly after error |
| `kill_all_ros.sh` | Soft reset — kills SLAM, TF relays, and visualizers while keeping dashboard alive | Resetting SLAM/TF state |
| `launch_all.sh` | Alternative — manually launches all ROS nodes without the web dashboard | Debugging without dashboard |
| `start_mapping.sh` | Headless SLAM only — no dashboard | Batch mapping without UI |
| `cyclonedds.xml` | CycloneDDS config — network interface name, peer IPs, multicast settings | Changing network layout |
| `GEMINI.md` / `AGENTS.md` | **This file** — AI agent memory | Any new lesson, failure, or rule |
| `AI_AGENT_CONTEXT_AND_DEVELOPMENT_LOG.md` | Full dev history — all decisions and post-mortems | After closing GitHub issues |


### `src/my_robot_dashboard/`
| File | Role | Touch when... |
|------|------|---------------|
| `app.py` | Flask backend: all REST routes, PID singleton, ROS listener thread, SSH to Uno Q, subprocess management | Adding/modifying API endpoints |
| `templates/index.html` | Web UI: HTML structure, CSS, loads `app.js`. Bump `?v=X.X` on every JS edit | Adding UI elements |
| `static/js/app.js` | Frontend: `apiCall()`, all button handlers, SSE stream consumer, map gallery renderer | Modifying UI behavior |

### `src/my_robot_nav/`
| File | Role | Touch when... |
|------|------|---------------|
| `scripts/qos_relay.py` | TF broadcaster (50 Hz odom→base_link, static base_link→laser/imu), IMU tilt gating, QoS bridge for /scan and /imu | Changing TF logic, tilt threshold, QoS |
| `scripts/map_regularizer.py` | Post-processing: Hough → θ_dom → Manhattan snap → SVG+PGM output | Improving wall regularization |
| `config/slam_toolbox_params.yaml` | SLAM tuning params — do not change without understanding each param | SLAM quality issues |
| `maps/` | Saved maps directory — `.pgm`, `.yaml`, `_regularized.pgm`, `_regularized.svg` | N/A — auto-populated |

### `src/my_robot_bringup/launch/`
| File | Role |
|------|------|
| `imu_slam.launch.py` | Launches slam_toolbox lifecycle node with 2s configure → 3.5s activate timers |

### `uno_q_firmware/BnoTest/`
| File | Role |
|------|------|
| `BnoTest.ino` | Arduino firmware for BNO086. Initializes Wire2 (A4/A5), I2C addr 0x4B. Enables: Accelerometer, Gyroscope, GameRotationVector (6-DOF, no magnetometer). Streams atomic comma-separated `imu/raw` payload to arduino-router at ~100 Hz |

### On the Arduino Uno Q (not in repo)
| File/Path | Role |
|-----------|------|
| `/home/arduino/start_rplidar.sh` | Starts the `rplidar` Docker container |
| `/var/run/arduino-router.sock` | IPC socket — BnoTest firmware → imu_publisher.py |
| `imu_publisher.py` (inside container) | Reads msgpack from arduino-router, publishes `/imu/data` @ 100 Hz |

---

## 🔌 SECTION 3: COMPLETE API SURFACE

Every REST endpoint in `app.py`. All are POST unless noted. All accept empty `{}` body.

```
GET  /                           → Serve dashboard index.html
POST /api/config/ip              → Update Uno Q IP (body: {"ip": "192.168.1.17"})
GET  /api/telemetry              → JSON snapshot of latest IMU + scan data
GET  /api/stream                 → SSE live telemetry (keeps connection open)

POST /api/slam/start             → Launch qos_relay + slam_toolbox lifecycle + RViz2
POST /api/slam/stop              → Kill qos_relay + slam_toolbox
POST /api/slam/save_map          → Save current map (body: {"filename": "optional_name"})
POST /api/slam/regularize_map    → Run map_regularizer.py on latest saved map
GET  /api/slam/list_maps         → List all maps in src/my_robot_nav/maps/

POST /api/sensors/lidar/start    → SSH → Uno Q → bash /home/arduino/start_rplidar.sh
POST /api/sensors/lidar/stop     → SSH → Uno Q → sudo docker stop rplidar
POST /api/sensors/imu/start      → SSH → Uno Q → restart imu_publisher.py in container
POST /api/sensors/imu/stop       → SSH → Uno Q → kill imu_publisher.py
POST /api/sensors/router/restart → SSH → Uno Q → sudo systemctl restart arduino-router
POST /api/sensors/unoq/reboot    → SSH → Uno Q → sudo reboot

POST /api/rviz/launch/<mode>     → Open RViz2 (mode: "scan" | "slam" | "imu")
POST /api/rviz/stop              → Kill RViz2

POST /api/system/kill_all        → pkill all ROS processes; dashboard stays running
POST /api/system/shutdown_all    → kill_all + os.kill(os.getpid(), SIGTERM) — full exit
```

**Curl examples for every endpoint:**
```bash
BASE="http://localhost:5050"
H='-H "Content-Type: application/json"'

# Check dashboard is alive
curl -s -o /dev/null -w "%{http_code}" $BASE/

# SLAM lifecycle
curl -X POST $BASE/api/slam/start            -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/slam/stop             -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/slam/save_map         -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/slam/save_map         -H "Content-Type: application/json" -d '{"filename":"living_room"}'
curl -X POST $BASE/api/slam/regularize_map   -H "Content-Type: application/json" -d '{}'
curl      $BASE/api/slam/list_maps

# Sensors
curl -X POST $BASE/api/sensors/lidar/start   -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/sensors/lidar/stop    -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/sensors/imu/start     -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/sensors/imu/stop      -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/sensors/router/restart -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/sensors/unoq/reboot   -H "Content-Type: application/json" -d '{}'

# RViz2
curl -X POST $BASE/api/rviz/launch/slam      -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/rviz/launch/scan      -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/rviz/stop             -H "Content-Type: application/json" -d '{}'

# System
curl -X POST $BASE/api/system/kill_all       -H "Content-Type: application/json" -d '{}'
curl -X POST $BASE/api/system/shutdown_all   -H "Content-Type: application/json" -d '{}'

# Telemetry
curl $BASE/api/telemetry
curl -N $BASE/api/stream  # SSE stream — Ctrl+C to stop
```

---

## 🧠 SECTION 4: IMU PIPELINE — CRITICAL TECHNICAL DETAILS

### BNO086 Firmware (`BnoTest.ino`) — What Is and Is NOT Enabled

**ENABLED reports (stable, no SHTP rejection):**
- `enableAccelerometer()` — 3-axis accelerometer
- `enableGyroscope()` — 3-axis gyroscope
- `enableGameRotationVector()` — **6-DOF quaternion (no magnetometer)** ← PRIMARY orientation source

**NOT ENABLED (caused SHTP rejection — do not re-enable):**
- `enableLinearAcceleration()` — sends un-negotiated SHTP report code → silently rejected
- `enableRotationVector()` — includes magnetometer → 1.5° yaw jitter indoors from magnetic noise
- `enableMagnetometer()` — too noisy indoors

**Why Game Rotation Vector instead of Rotation Vector:**
- `RotationVector` uses magnetometer for absolute yaw → noisy indoors (metal furniture, electrical wiring)
- `GameRotationVector` uses only gyro + accel → drift-free for room-scale sessions (< 30 minutes)
- Exponential smoothing: `q_smooth = slerp(q_prev, q_new, α=0.35)` reduces gyro noise spikes

### IPC Format — `imu/raw` Payload

The firmware sends a single atomic line per IMU sample over the arduino-router IPC:
```
imu/raw,<qW>,<qX>,<qY>,<qZ>,<gX>,<gY>,<gZ>,<aX>,<aY>,<aZ>
```
Example: `imu/raw,-0.012,0.003,0.998,0.061,0.0021,-0.0008,9.53,0.001,-0.002`

**Why single atomic line?** Multiple `Bridge.provide()` calls caused context-switch overhead → rate
dropped from expected 100 Hz to 7.7 Hz. Single payload → 100.039 Hz achieved.

### Quaternion Sign Flip Handling

Quaternions have a double-cover: `q` and `-q` represent the same rotation. The BNO086 occasionally
flips sign, causing a 360° yaw jump on smoothing. Fix in `imu_publisher.py`:
```python
if dot(q_prev, q_new) < 0:
    q_new = -q_new  # force same hemisphere before slerp
q_smooth = slerp(q_prev, q_new, 0.35)
```

### Clock Drift — Uno Q vs Laptop

Uno Q clock drifts 5–8 ms behind laptop over Wi-Fi. Solution in `qos_relay.py`:
- Re-stamp incoming `/imu/data` with `self.get_clock().now()` (laptop time)
- Add `+100ms` forward TTL to TF transforms to absorb inter-machine timestamp mismatch

---

## 🌐 SECTION 5: NETWORK & DDS CONFIGURATION

### Environment Variables (MUST be set before any ROS 2 command)

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
```

`start_dashboard.sh` sets these automatically. If running nodes manually in a new terminal, you must source and export these.

### `cyclonedds.xml` Structure

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config">
    <Domain id="any">
        <General>
            <Interfaces>
                <!-- MUST match your actual Wi-Fi interface name: `ip link show | grep "^[0-9]: w"` -->
                <NetworkInterface name="wlp4s0" multicast="true" />
            </Interfaces>
            <AllowMulticast>true</AllowMulticast>
        </General>
        <Discovery>
            <Peers>
                <Peer address="192.168.1.17"/>  <!-- Uno Q -->
            </Peers>
            <ParticipantIndex>auto</ParticipantIndex>
            <MaxAutoParticipantIndex>120</MaxAutoParticipantIndex>
        </Discovery>
    </Domain>
</CycloneDDS>
```

**If topics don't cross Wi-Fi:**
1. Verify Wi-Fi interface: `ip link show | grep "^[0-9]: w"` → must match `name=` in XML
2. Verify Uno Q IP: `ssh arduino@192.168.1.17` → `ip addr`
3. Both must have `ROS_DOMAIN_ID=42`
4. Uno Q Docker container must use `--net=host`

### Why CycloneDDS (not FastDDS)

FastDDS default caused:
- Broadcast storms on the LAN
- Uno Q dropped out from discovery after ~30s
- FastDDS multicast discovery not configured for cross-host

CycloneDDS with static unicast peers:
- Deterministic discovery (no multicast-dependent recovery)
- Sub-5ms latency for `/scan` packets
- Works through Wi-Fi AP isolation if unicast peers are specified

---

## 🗺️ SECTION 6: TOPIC & TF TREE ARCHITECTURE

### Active Topic Map

```
[Uno Q Docker container "rplidar"]
  rplidar_node ─────────────────► /scan              (LaserScan, 10 Hz, BEST_EFFORT)
  imu_publisher.py ─────────────► /imu/data          (Imu, 100 Hz, BEST_EFFORT)

[Laptop DevContainer "thirsty_burnell"]
  qos_relay.py:
    /scan  ──► filter ──────────► /scan_reliable      (LaserScan, 10 Hz, RELIABLE)
    /imu/data ──────────────────► /imu_reliable       (Imu, 100 Hz, RELIABLE)
    clock ─────────────────────► /tf: odom→base_link  (50 Hz, dynamic)
    static ────────────────────► /tf: base_link→laser (static, once)
    static ────────────────────► /tf: base_link→imu   (static, once)

  slam_toolbox:
    /scan_reliable ─────────────► /map                (OccupancyGrid, async ~1 Hz)
    /tf: odom→base_link ────────► /tf: map→odom       (async, on new scan)

  app.py (ROS listener thread):
    /imu/data ──────────────────► telemetry_dict["imu"] (in-memory, consumed by SSE)
    /scan ─────────────────────► telemetry_dict["scan_hz"]
```

### TF Tree (after SLAM is running)

```
map
 └── odom              ← published by slam_toolbox (map→odom correction)
      └── base_link    ← published by qos_relay.py at 50 Hz (odom→base_link)
           ├── laser   ← static TF (base_link→laser, offset in Z)
           └── imu     ← static TF (base_link→imu, at origin)
```

**If `odom` frame is missing in RViz:**
→ `qos_relay.py` is not running. The dashboard's "Start SLAM" button starts it automatically.

**If `map` frame is missing:**
→ `slam_toolbox` hasn't activated yet. Wait 4–5 seconds after clicking "Start SLAM".

---

## 🔧 SECTION 7: SLAM TOOLBOX PARAMS — FULL RATIONALE

File: `src/my_robot_nav/config/slam_toolbox_params.yaml`

```yaml
sync_slam_toolbox_node:
  ros__parameters:
    # --- QoS & Transport ---
    use_sim_time: false               # MUST be false on real hardware
    transform_timeout: 0.25          # Was 0.1 — increased because Wi-Fi adds 5-50ms jitter
                                     # to TF lookup timestamps. 0.1 caused TF extrapolation errors.

    # --- Scan Input ---
    scan_topic: /scan_reliable        # Use qos_relay's RELIABLE rebroadcast, not raw /scan
                                     # Raw /scan uses BEST_EFFORT — slam_toolbox drops packets

    # --- Scan Matcher ---
    use_scan_barycenter: false        # Was true — caused Ceres solver matrix to exceed bounds
    use_response_expansion: false     # Was true — same Ceres crash (Failure #12)
    correlation_search_space_dimension: 0.80  # Was 0.5 — robot could walk ~0.8 m/s; scan
                                              # matcher lost track above 0.5 m step size

    # --- Loop Closure ---
    loop_search_maximum_distance: 12.0  # Was 5.0 — entire house floor plan is ~10m wide.
                                        # 5m didn't trigger closure when returning from far rooms.
    scan_buffer_size: 30               # Was 10 — more scan history = better loop constraint
                                       # when revisiting rooms after extended walking
    loop_match_minimum_response_fine: 0.45  # Permissive — handheld has more noise than wheeled

    # --- Map ---
    resolution: 0.05                  # 5 cm/pixel — balance of detail vs memory
    map_update_interval: 5.0          # Update /map topic every 5 seconds
```

---

## 💾 SECTION 8: HARDWARE WIRING — FULL SPECIFICATIONS

### BNO086 (ES-12243) ↔ Arduino Uno Q

| BNO086 Pin | Uno Q Pin | STM32 Resource | Notes |
|------------|-----------|---------------|-------|
| VCC | 3.3V | 3.3V rail | **MUST be 3.3V — 5V will damage the sensor** |
| GND | GND | Ground | |
| SDA | A4 | Wire2 I2C2 SDA | A4 maps to Wire2 on Uno Q (NOT Wire0/Wire1) |
| SCL | A5 | Wire2 I2C2 SCL | A5 maps to Wire2 on Uno Q |
| INT | D2 | GPIO INPUT_PULLUP | Data-ready interrupt — required for 100 Hz |
| ADDR | (not connected) | Pulled HIGH on PCB | I2C address = 0x4B (high), not 0x4A (low) |

**Why Wire2 and not Wire?** Arduino Uno Q's standard `Wire` maps to a different I2C bus. The physical pins A4/A5 on the Uno Q header are wired to `Wire2` (STM32 I2C2). Using `Wire` compiles but communicates on the wrong bus → no I2C response → failure.

### RPLidar C1 ↔ Arduino Uno Q

- **Physical**: USB-A (Uno Q) to USB-A/Micro-USB (LiDAR, via CP2102 adapter)
- **Device node**: `/dev/ttyUSB0` (appears as soon as plugged in)
- **Baud rate**: 460800 bps (Slamtec C1 specific — not the default 115200)
- **ROS param**: `serial_baudrate: 460800` in rplidar launch file
- **Pre-spin**: The C1 has a 3-second motor spin-up timeout. The `start_rplidar.sh` script
  sends the spin command before launching ROS to avoid this timeout.

---

## 🖥️ SECTION 9: DASHBOARD INTERNAL ARCHITECTURE

### `app.py` Thread Model

```
Main thread: Flask WSGI server (threaded=True)
    └── handles HTTP requests, spawns subprocess for ROS nodes

Background thread: ROS listener (daemon=True)
    └── rclpy.init() → create_node("dashboard_listener")
    └── subscription to /imu/data → updates telemetry_dict["imu"]
    └── subscription to /scan → updates telemetry_dict["scan_hz"]
    └── NEVER blocks — uses rclpy.spin_once() with timeout=0

SSE generator: /api/stream route
    └── reads telemetry_dict every 100ms → yields "data: {...}\n\n"
    └── one generator per connected browser tab
```

**Critical:** The ROS listener thread must NEVER call any Flask response methods. Flask routes must NEVER call `rclpy.spin()` (blocking). This separation is what allows the dashboard to remain responsive even when SLAM is running.

### PID Singleton Sequence (in `app.py`)

```python
def enforce_singleton(port=5050):
    pid_file = "/tmp/my_robot_dashboard.pid"
    if os.path.exists(pid_file):
        old_pid = int(open(pid_file).read().strip())
        try:
            os.kill(old_pid, signal.SIGTERM)  # graceful kill
            # poll for socket release (up to 2.0s)
            for _ in range(20):
                if not socket_in_use(port):
                    break
                time.sleep(0.1)
        except ProcessLookupError:
            pass  # process already dead
    # write new PID
    open(pid_file, 'w').write(str(os.getpid()))
```

### SSH to Uno Q (from `app.py`)

All Uno Q operations use `ssh_unoq_cmd()` which runs `paramiko` SSH calls with timeout=12s.
The Uno Q IP is read from a config dict (default `192.168.1.17`), updatable via `/api/config/ip`.

---

## 🚨 SECTION 10: CUMULATIVE FAILURE KNOWLEDGE BASE

All 16 failures and their exact solutions. Read these before attempting ANY related task.

| # | Failure | Root Cause | Exact Fix |
|---|---------|-----------|-----------|
| 1 | I2C bus lockup — BNO086 not responding | Uno Q physical pins A4/A5 map to `Wire2`, not `Wire`. 7Semi ES-12243 pulls ADDR pin HIGH → I2C address 0x4B, not 0x4A | `BnoI2CBus(Wire2, BNO_RESET, INT_PIN, 0x4B)` in `BnoTest.ino` |
| 2 | SHTP Feature Rejection — IMU silent after `enableLinearAccel` | `enableLinearAccel` sends un-negotiated SHTP report ID. Sensor silently rejects and stops sending ALL reports | Remove `enableLinearAccel`. Only use: `enableAcc`, `enableGyro`, `enableGameRotationVector` |
| 3 | IPC Bottleneck — IMU rate dropped to 7.7 Hz | Multiple separate `Bridge.provide()` RPC calls per IMU sample → Python IPC context-switch overhead | Single atomic `Bridge.provide("imu/raw", "qW,qX,qY,qZ,gX,gY,gZ,aX,aY,aZ")` → 100.039 Hz |
| 4 | Quaternion sign flips — 360° yaw jump | BNO086 occasionally flips quaternion sign (q ↔ -q, both valid). `slerp()` interprets as full rotation | Check `dot(q_prev, q_new) < 0` → negate `q_new` before slerp |
| 5 | Multi-machine clock drift — TF extrapolation errors | Uno Q NTP not configured, clock lagged laptop by 5–8 ms over Wi-Fi sessions | Re-stamp `/imu/data` with laptop clock in `qos_relay.py` + `+100ms` TF TTL |
| 6 | Double-integration drift — velocity grew unboundedly | Nominal gravity 9.806 m/s² ≠ measured 9.53 m/s² → residual after gravity subtraction → drift | 3D body-frame gravity projection vector using measured g value |
| 7 | RMW discovery mismatch — topics don't cross Wi-Fi | Uno Q Docker image defaulted to `rmw_fastrtps_cpp`. Laptop used CycloneDDS. Different RMW → different wire format → invisible to each other | Set `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` in Docker container env AND install `ros-jazzy-rmw-cyclonedds-cpp` |
| 8 | SLAM race condition — RViz launches before slam_toolbox active | `slam_toolbox` is a lifecycle node — takes 3–4s to configure+activate. RViz opened immediately → no `/map` topic → user confused | Timer chain in `imu_slam.launch.py`: 2.0s → configure, 3.5s → activate, 4.5s → launch RViz |
| 9 | IMU yaw jitter ±1.5° | `enableRotationVector` uses magnetometer → metal furniture, electrical wiring cause indoor magnetic noise | Switch to `enableGameRotationVector` (6-DOF, gyro+accel only) + exponential smoothing α=0.35 |
| 10 | Missing `odom` frame in RViz | Handheld mapping has no wheel encoders → no `/odom` publisher → slam_toolbox can't find `odom→base_link` TF | `qos_relay.py` broadcasts synthetic 50 Hz `odom→base_link` dynamic TF from IMU yaw |
| 11 | Timestamp desync — `qos_relay.py` re-stamping scan broke SLAM | Re-stamping `/scan` header to laptop time created timestamp mismatch with the original scan data, breaking Karto's TF buffer lookup | Preserve original scan timestamps. Only re-stamp `/imu/data`. Increase `transform_timeout: 0.25` |
| 12 | Ceres Karto matrix crash — slam_toolbox segfault | `use_scan_barycenter: true` + `use_response_expansion: true` → scan matcher generates search matrix that exceeds Ceres solver bounds → segfault | Set both to `false`. Set `correlation_search_space_dimension: 0.80` |
| 13 | Zombie process collisions — port jumping to 5051 | Multiple terminals all ran `python3 app.py` simultaneously → all tried to bind 5050 → one succeeded on 5051 → DDS had two dashboard participants | PID lockfile at `/tmp/my_robot_dashboard.pid` with SIGTERM + 2s poll for port release |
| 14 | No emergency shutdown — had to hunt terminal windows | System had no way to stop all processes remotely; stale nodes accumulated across sessions | `POST /api/system/kill_all` (pkill all ROS) and `POST /api/system/shutdown_all` (kill + exit app.py) |
| 15 | Flask `400 Bad Request` on button clicks | `request.json` raises Werkzeug 400 when POST body is empty (0 bytes) or Content-Type missing | Replace ALL `request.json` with `request.get_json(silent=True) or {}` throughout `app.py` |
| 16 | Browser `JSON.parse SyntaxError` on button clicks | Frontend called `res.json()` directly. When server returned HTML error page (due to #15), parsing HTML as JSON threw SyntaxError. Real error was invisible | `const text = await res.text(); try { return JSON.parse(text); } catch(e) {...}` + bump `?v=X.X` |
| 17 | Container child process survival during pkill | `docker exec -t ... pkill ...` without a bash subshell fails to parse regex flags properly in some environments, leaving child ROS nodes (`qos_relay.py`, etc.) running in background | Always wrap container process cleanup in an explicit bash string: `docker exec -t thirsty_burnell bash -c 'pkill -9 -f "..." 2>/dev/null \|\| true'` |
| 18 | Rogue port fallback creating split-brain ROS nodes | Automatically jumping to random ports (5055, 5051) when 5050 is held leaves old ROS nodes running unnoticed, corrupting RViz visualization and wasting RAM | Enforce explicit port termination. Never spawn competing dashboard nodes on dynamic ports without terminating all prior ROS nodes first |


---

## 🔀 SECTION 11: GIT BRANCH & COMMIT STRATEGY

**Active branch:** `feature/lidar-imu-slam-fusion`
**Remote:** `https://github.com/akash-adhikary/distributed-ros2-robot.git`

**Commit message format:**
```
<type>(<scope>): <short description> (#<issue>)

Types: feat, fix, docs, refactor, chore, perf
Scopes: dashboard, slam, imu, nav, firmware, docs, infra
```

**Examples:**
```
feat(slam): add tilt-aware scan gating in qos_relay (#5)
fix(dashboard): prevent 400 on empty POST body with get_json (#6)
docs: comprehensive documentation overhaul (#7)
```

**Never commit to main directly.** All work goes to `feature/lidar-imu-slam-fusion` first.

---

## 📋 SECTION 12: SYSTEM HEALTH VERIFICATION RUNBOOK

Run this entire sequence to verify a healthy system state:

```bash
# ── STEP 1: Environment Setup ──────────────────────────────────────────
source /opt/ros/jazzy/setup.bash
source /home/ros/my_robot_ws/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml

# ── STEP 2: Check Dashboard is Running ─────────────────────────────────
curl -s -o /dev/null -w "Dashboard HTTP: %{http_code}\n" http://localhost:5050/
# Expected: Dashboard HTTP: 200

# ── STEP 3: Check for Zombie Processes ─────────────────────────────────
ps aux | grep -E "app.py|qos_relay|slam_toolbox|rviz2" | grep -v grep
# Expected: only the intended processes

# ── STEP 4: Verify Sensor Topics ───────────────────────────────────────
timeout 5 ros2 topic hz /scan | tail -1
# Expected: average rate: 10.xxx

timeout 5 ros2 topic hz /imu/data | tail -1
# Expected: average rate: 100.xxx

# ── STEP 5: Verify TF Tree (after SLAM start) ──────────────────────────
timeout 3 ros2 run tf2_ros tf2_echo odom base_link | head -5
# Expected: - Translation: [0.000, 0.000, 0.000] and a rotation quaternion

# ── STEP 6: Test All REST Endpoints ────────────────────────────────────
for endpoint in /api/telemetry /api/slam/list_maps; do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5050$endpoint)
  echo "GET $endpoint: $code"
done
# Expected: both 200

for endpoint in /api/system/kill_all; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:5050$endpoint \
    -H "Content-Type: application/json" -d '{}')
  echo "POST $endpoint: $code"
done
# Expected: 200

# ── STEP 7: Verify Map Files ────────────────────────────────────────────
ls -la /home/ros/my_robot_ws/src/my_robot_nav/maps/
# Expected: .pgm and .yaml files for any previously saved maps

# ── STEP 8: Check Uno Q Container ──────────────────────────────────────
ssh arduino@192.168.1.17 "sudo docker ps" 2>/dev/null
# Expected: "rplidar" container in "Up" status
```

---

## 🏗️ SECTION 13: CURRENT PROJECT STATE & NEXT STEPS

### Phase Status
- **Phase 1** ✅ COMPLETE — RPLidar C1, BNO086 IMU, CycloneDDS, multi-machine ROS 2
- **Phase 2** ✅ COMPLETE — qos_relay TF, tilt gating, SLAM, Web Dashboard, map regularizer, defensive REST
- **Phase 3** ⬅️ CURRENT — Motor control (NOT started)
- **Phase 4** — Autonomous Nav2 navigation (future)

### Phase 3 What's Needed (Motor Control)
1. Select and wire a motor controller to Uno Q via USB serial
2. Write `serial_bridge` node: subscribes `/cmd_vel` (Twist) → sends PWM commands to motor controller over serial
3. Write wheel encoder node: publishes `/odom` from encoder counts
4. Test closed loop: RViz2 Nav2 goal → `/cmd_vel` → Uno Q → robot moves → `/odom` → Nav2 localizes

### Open GitHub Issues
Check for any open issues before starting new work:
```bash
gh issue list --state open
```

### Known Limitations (as of Phase 2 completion)
- **No wheel odometry**: `qos_relay.py` publishes synthetic identity `odom→base_link` (robot always at origin in odom frame). This is sufficient for handheld SLAM but will not work for autonomous navigation.
- **IMU yaw drift**: Game Rotation Vector drifts ~0.5°/minute without magnetometer. Fine for room-scale sessions.
- **Map regularizer sensitivity**: Very open-plan spaces without clear walls produce a diffuse angle histogram — θ_dom may be unreliable. Works best in rooms with at least 4 clear walls.
- **SSH timeout**: Uno Q SSH operations in `app.py` have a 12s timeout. Reboot Uno Q command may appear to fail but actually succeeds (SSH closes before response).

---

## 📚 SECTION 14: DOCUMENTATION INDEX FOR AGENTS

When you need detailed information, refer to these files:

| What you need | Read this file |
|--------------|----------------|
| Onboard a new person / full setup steps | `README.md` |
| Day-to-day operational workflow | `docs/USAGE_GUIDE.md` |
| All REST API endpoints + curl examples | `docs/DASHBOARD.md` |
| System architecture, topic graph, TF tree | `docs/ARCHITECTURE.md` |
| Uno Q Docker deployment details | `docs/UNO_Q_DEPLOYMENT.md` |
| Full dev history and GitHub issue post-mortems | `AI_AGENT_CONTEXT_AND_DEVELOPMENT_LOG.md` |
| Simulation and Gazebo-specific issues | `docs/DEVELOPMENT_NOTES.md` |
| **This file — master AI memory** | `GEMINI.md` / `AGENTS.md` |

---

*Last updated: 2026-08-25 | Branch: feature/lidar-imu-slam-fusion | Phase: 2 Complete*
