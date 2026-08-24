# GEMINI.md - Distributed ROS 2 Robot Master Memory & Operational Instructions

> **CRITICAL RULE FOR ALL AI AGENTS & MODELS**:  
> Before performing any task, writing code, modifying configurations, or answering questions on this codebase, you **MUST** read, internalize, and strictly adhere to the rules and lessons documented in this file. Never skip these steps or repeat known mistakes.

---

## ⚡ 0. MANDATORY PRE-FLIGHT MEMORY & ANTI-MISTAKE CHECKLIST (RULE ZERO)

### 🛑 Rule 1: Zero Zombie / Duplicate Instances (Singleton Process Lifecycle)
- **Mistake made in past**: Running multiple scripts (`telemetry_bridge.py`, separate `qos_relay.py`, duplicate `app.py`) in parallel, causing competing DDS participants, port collisions (e.g. jumping from 5050 to 5051), and stale sockets that caused 4–5 hours of debugging.
- **Enforced Standard**:
  - `src/my_robot_dashboard/app.py` enforces a strict PID lockfile (`/tmp/my_robot_dashboard.pid`) with automated graceful takeover.
  - When starting a new instance from another terminal, it sends `SIGTERM` to the prior PID, polls socket release for up to 2.0s, and reclaims Port 5050 cleanly.
  - Never run standalone ad-hoc bridges when `app.py` already manages the internal ROS listener thread.
  - Always check running processes (`ps aux | grep ...`) before spawning ROS nodes.
  - The Web UI provides both **"Reset Nodes"** (`/api/system/kill_all`) and **"Shutdown All & Exit"** (`/api/system/shutdown_all`).

### 🛑 Rule 2: Defensive REST & UI Serialization (No Unhandled HTML / 400 Exceptions)
- **Mistake made in past**:
  1. Using Flask's `request.json` without verifying body presence $\rightarrow$ Flask threw `400 Bad Request: Failed to decode JSON object` on 0-byte POST payloads.
  2. Calling `res.json()` directly in JavaScript on HTML error pages $\rightarrow$ Browser threw `SyntaxError: JSON.parse: unexpected character at line 1 column 1`.
  3. Browser aggressively caching older JS files when new UI functions/routes were added.
- **Enforced Standard**:
  - **Backend**: Always use `req_data = request.get_json(silent=True) or {}` across ALL Flask POST endpoints.
  - **Frontend**: In `static/js/app.js`, always read `res.text()`, safely parse inside a `try...catch` block, and default `opts.body = JSON.stringify(payload || {})`.
  - **Cache Invalidation**: Always bump the query version in `templates/index.html` (e.g. `<script src="/static/js/app.js?v=X.X"></script>`) whenever modifying frontend assets.

### 🛑 Rule 3: End-to-End Verification Before Declaring Done (Never Guess or Assume)
- **Mistake made in past**: Assuming an algorithm works without verifying active sensor streams, TF2 coordinate transforms, and topic headers across both local and edge machines.
- **Enforced Standard**:
  - Every task must be verified end-to-end with real command outputs:
    1. Sensors publishing on Uno Q (`/scan` @ 10 Hz, `/imu/data` @ 80+ Hz).
    2. Dynamic TF tree published at 50 Hz (`map -> odom -> base_link -> laser`).
    3. REST API response codes and UI Toast notifications tested via curl and browser checks.
  - Never report success based on partial or theoretical checks.

### 🛑 Rule 4: Loose Coupling & Component Isolation
- **Mistake made in past**: Adding SLAM or post-processing features caused side effects that froze sensor telemetry or UI buttons.
- **Enforced Standard**:
  - The system is divided into decoupled layers:
    1. **Web UI Layer**: Non-blocking REST + SSE stream (Port 5050).
    2. **Telemetry Daemon**: Background ROS listener in `app.py` that never blocks Flask routes.
    3. **Bridge Layer (`qos_relay.py`)**: Persistent 50 Hz dynamic TF and tilt filter daemon.
    4. **SLAM Layer (`slam_toolbox`)**: Standalone async mapper.
    5. **Post-Processing Layer (`map_regularizer.py`)**: Independent on-demand 90° wall regularizer.

### 🛑 Rule 5: Tilt-Aware Gating & Multi-Room SLAM Quality
- **Mistake made in past**: Carrying the setup by hand caused pitch/roll tilts ($3^\circ - 8^\circ$) where 2D laser rays struck floors and ceilings, confusing the 2D scan matcher and causing multi-room maps to overlap and distort.
- **Enforced Standard**:
  - `qos_relay.py` monitors real-time IMU tilt $\theta_{\text{tilt}} = \sqrt{\text{roll}^2 + \text{pitch}^2}$. When tilted $> 7.5^\circ$, laser rays with vertical height offsets $|r \sin(\theta)| > 0.40\,\text{m}$ are gated out (`float('inf')`).
  - `slam_toolbox_params.yaml` is tuned for multi-room mapping:
    - Search radius: `correlation_search_space_dimension: 0.80` (handles walking up to $0.8\,\text{m/s}$).
    - Loop closure range: `loop_search_maximum_distance: 12.0` (entire floor plan).
    - Scan history buffer: `scan_buffer_size: 30`.

### 🛑 Rule 6: Architectural Manhattan 90° Wall Snapping (`map_regularizer.py`)
- **Enforced Standard**:
  - Raw 2D SLAM maps produce fuzzy, jagged pixel clouds.
  - `src/my_robot_nav/scripts/map_regularizer.py` converts raw occupancy grids into crisp, architectural CAD-like boxy rooms:
    1. Extracts wall line segments via Hough Transform (`cv2.HoughLinesP`).
    2. Computes the dominant building orientation angle $\theta_{\text{dom}}$.
    3. Snaps all wall segments to orthogonal Manhattan angles ($\theta_{\text{dom}} + k \cdot 90^\circ$).
    4. Exports `_regularized.yaml` / `_regularized.pgm` and clean vector CAD `_regularized.svg`.

### 🛑 Rule 7: Mandatory GitHub Issue Lifecycle & Traceability
- **Enforced Standard**:
  - Create a GitHub issue (`gh issue create`) for every bug, architectural change, or feature.
  - Reference issue numbers in commits.
  - Close issues with structured post-mortems in `AI_AGENT_CONTEXT_AND_DEVELOPMENT_LOG.md`.

---

## 1. System Topology & Network Architecture

```mermaid
graph TD
    subgraph Edge Hardware: Arduino Uno Q (192.168.1.17)
        MCU[STM32U585 Zephyr M33 Core]
        IMU[7Semi BNO086 9-DOF IMU] -->|I2C Wire2 A4/A5 + INT D2 @ 0x4B| MCU
        MCU -->|Bridge.provide 'imu/raw'| ROUTER[arduino-router IPC /var/run/arduino-router.sock]
        
        LIDAR[RPLidar C1] -->|UART /dev/ttyUSB0 @ 460800 baud| DOCKER_EDGE[Docker Container: rplidar]
        ROUTER -->|msgpack IPC| DOCKER_EDGE
        
        subgraph rplidar Container
            PUB_LIDAR[rplidar_node -> /scan @ 10 Hz]
            PUB_IMU[imu_publisher.py -> /imu/data @ 100 Hz]
        end
    end

    subgraph Distributed Network: Wi-Fi (ROS_DOMAIN_ID=42, CycloneDDS)
        PUB_LIDAR -->|UDP Multicast + Static Unicast Peers| DDS[CycloneDDS DataBus]
        PUB_IMU -->|UDP Multicast + Static Unicast Peers| DDS
    end

    subgraph Laptop Station: Development PC (192.168.1.15)
        DDS --> DOCKER_HOST[DevContainer: thirsty_burnell]
        
        subgraph thirsty_burnell Container
            RELAY[qos_relay.py: 50 Hz TF + Tilt Ray Gating]
            SLAM[slam_toolbox: Async 2D SLAM]
            REG[map_regularizer.py: 90° Manhattan Snapper]
            DASH[Flask + Three.js Dashboard @ :5050]
            RVIZ[RViz2 3D Visualizer]
        end
    end
```

---

## 2. Hardware Wiring & Pinout Specifications

### 7Semi BNO086 (ES-12243) $\leftrightarrow$ Arduino Uno Q
| Pin | Uno Q Physical Pin | STM32 Resource | Function | Logic Level |
|---|---|---|---|---|
| **VCC** | **3.3V** | 3.3V Power Rail | Power Supply | 3.3V DC |
| **GND** | **GND** | Ground Plane | Common Reference | 0V |
| **SDA** | **Analog A4** | `Wire2` (I2C2 SDA) | I2C Serial Data | 3.3V Open-Drain (`0x4B`) |
| **SCL** | **Analog A5** | `Wire2` (I2C2 SCL) | I2C Serial Clock | 100 kHz Open-Drain |
| **INT** | **Digital D2** | GPIO Pin 2 | Data Ready Interrupt | 3.3V (`INPUT_PULLUP`) |

### RPLidar C1 $\leftrightarrow$ Arduino Uno Q
- **Interface**: USB Type-A to Micro-USB / CP2102 Bridge (`/dev/ttyUSB0` @ 460800 baud).
- **Settings**: Standard Scan Mode, 5 kHz sample rate, 10.0 Hz scan frequency, 16.0 m range.

---

## 3. Standard Operating Commands Cheat Sheet

### Launch Dashboard (Preferred Single-Point Control)
```bash
cd ~/my_robot_ws
./start_dashboard.sh
# Access UI in browser at: http://localhost:5050
```

### Emergency Teardown & Reset via CLI
```bash
curl -X POST http://localhost:5050/api/system/kill_all      # Reset ROS nodes
curl -X POST http://localhost:5050/api/system/shutdown_all  # Full exit
```

### Manual Headless Verification
```bash
docker exec -t thirsty_burnell bash -c "
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
ros2 topic hz /scan
ros2 topic hz /imu/data
ros2 run tf2_ros tf2_echo odom base_link
"
```

---

## 4. Cumulative Knowledge Base of Resolved Failures

| Failure # | Description | Root Cause | Breakthrough Solution |
|---|---|---|---|
| **1** | I2C Bus Lockup | Uno Q routes headers A4/A5 to `Wire2`; 7Semi pulls ADDR high (`0x4B`). | Initialized `BnoI2CBus(Wire2, ..., 0x4B)`. |
| **2** | SHTP Feature Rejection | `enableLinearAccel` sends un-negotiated SHTP report code. | Initialized only proven reports (`enableAcc`, `enableGyro`, `enableRotationVector`, `enableGameRotationVector`). |
| **3** | IPC Bottleneck (7.7 Hz) | Multiple `Bridge.provide` RPC calls caused context-switch overhead. | Created single atomic comma-separated payload (`imu/raw` @ 100.039 Hz). |
| **4** | Quaternion Sign Flips | Quaternions double-cover 3D rotations ($q \leftrightarrow -q$). | Continuous quaternion dot-product tracking in Python. |
| **5** | Multi-Machine Clock Drift | Uno Q clock lagged laptop by 5–8 ms over Wi-Fi. | Local re-stamping in `qos_relay.py` + `+100ms` TF forward time-to-live. |
| **6** | Double-Integration Drift | Nominal gravity ($9.806\,\text{m/s}^2$) differed from measured ($9.53\,\text{m/s}^2$). | Omnidirectional 3D Body-Frame Gravity Projection vector. |
| **7** | RMW Discovery Mismatch | Uno Q defaulted to `rmw_fastrtps_cpp` without multicast route. | Installed `rmw_cyclonedds_cpp` with static Unicast Peer configs on both ends. |
| **8** | SLAM Frame Race Condition | RViz launched before `slam_toolbox` transitioned to active state. | Deterministic lifecycle activator timer ($2.0\text{s}$ configure $\rightarrow$ $3.5\text{s}$ activate $\rightarrow$ $4.5\text{s}$ RViz). |
| **9** | IMU Yaw Jitter ($1.5^\circ$) | Geomagnetic rotation vector had magnetometer noise indoors. | Switched to 6-DOF Game Rotation Vector + exponential smoothing ($\alpha=0.35$). |
| **10** | Missing `odom` Frame in RViz | Handheld 2D SLAM lacked continuous wheel odometry. | `qos_relay.py` broadcasts continuous 50 Hz `odom -> base_link` dynamic TF. |
| **11** | Timestamp Desync & Freezes | Ingesting and re-stamping `/scan` broke Karto's TF lookup buffer. | Preserved original laser scan timestamps; adjusted `slam_toolbox` `transform_timeout: 0.25`. |
| **12** | Ceres Karto Matrix Crash | `use_scan_barycenter: true` / `use_response_expansion: true` exceeded bounds. | Set both to `false` and set `correlation_search_space_dimension: 0.80`. |
| **13** | Zombie Process Collisions | Competing background daemons and port jumping. | Singleton PID lockfile (`/tmp/my_robot_dashboard.pid`) with automated graceful takeover. |
| **14** | Missing Emergency Controls | Stale nodes on Laptop and Uno Q required manual terminal hunting. | Built `/api/system/kill_all` and `/api/system/shutdown_all` with UI buttons. |
| **15** | Flask `400 Bad Request` | `request.json` rejected empty 0-byte POST payloads. | Switched all routes to `req_data = request.get_json(silent=True) or {}`. |
| **16** | Browser `JSON.parse` SyntaxError | `apiCall` called `res.json()` on HTML error responses. | Read `res.text()` first, safely parsed in `try...catch`, and bumped cache versioning. |

---

## 5. Completed GitHub Issues Traceability Matrix

| Issue | Type | Title | Status | Linked Commits | Key Deliverables |
|---|---|---|---|---|---|
| **[#1](https://github.com/akash-adhikary/distributed-ros2-robot/issues/1)** | Feature | Robust 2D SLAM Sensor Fusion (RPLidar + BNO086 IMU) | Closed | `5e4769a` | `imu_slam.launch.py`, `qos_relay.py` |
| **[#2](https://github.com/akash-adhikary/distributed-ros2-robot/issues/2)** | Fix | Eliminate Yaw Jitter via Game Rotation Vector ($0.35$ SLERP) | Closed | `5e4769a` | `BnoTest.ino`, `imu_publisher.py` |
| **[#3](https://github.com/akash-adhikary/distributed-ros2-robot/issues/3)** | Feature | Post-Processing Manhattan Wall Regularization & Line Snapping | Closed | `e57d607` | `map_regularizer.py`, `app.py` |
| **[#4](https://github.com/akash-adhikary/distributed-ros2-robot/issues/4)** | Refactor | System Robustness: Singleton Process Guard & Emergency Shutdown | Closed | `fd5ba89` | `app.py`, `index.html` |
| **[#5](https://github.com/akash-adhikary/distributed-ros2-robot/issues/5)** | Enhancement | Multi-Room SLAM Quality & Tilt-Gated Scan Filtering | Closed | `e57d607` | `qos_relay.py`, `slam_toolbox_params.yaml` |
| **[#6](https://github.com/akash-adhikary/distributed-ros2-robot/issues/6)** | Fix | Prevent HTTP 400 on Empty POST Payloads & Safe JSON Parsing | Closed | `920b741` | Silent request parsing & safe frontend error handling |
