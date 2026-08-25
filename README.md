# 🤖 Distributed Edge-ROS 2 Robot — Full Mapping Stack

A production-grade, distributed autonomous robot system built with **ROS 2 Jazzy**, **CycloneDDS**, and a **Flask + Three.js Web Dashboard**. The system splits workload between a lightweight edge board (Arduino Uno Q with RPLidar C1 + BNO086 IMU) and a development laptop running SLAM, sensor fusion, and the control dashboard.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Hardware You Need](#hardware-you-need)
3. [Software Prerequisites](#software-prerequisites)
4. [Repository Structure](#repository-structure)
5. [First-Time Setup — Step by Step](#first-time-setup--step-by-step)
   - [Step 1: Clone the Repository](#step-1-clone-the-repository)
   - [Step 2: Open the DevContainer on the Laptop](#step-2-open-the-devcontainer-on-the-laptop)
   - [Step 3: Build the ROS 2 Workspace](#step-3-build-the-ros-2-workspace)
   - [Step 4: Flash the BNO086 IMU Firmware (Arduino Uno Q)](#step-4-flash-the-bno086-imu-firmware-arduino-uno-q)
   - [Step 5: Deploy the Sensor Docker Container to the Uno Q](#step-5-deploy-the-sensor-docker-container-to-the-uno-q)
   - [Step 6: Configure CycloneDDS Networking](#step-6-configure-cyclonedds-networking)
6. [Daily Usage — Start the System](#daily-usage--start-the-system)
7. [Web Dashboard Guide](#web-dashboard-guide)
8. [CLI Verification Commands](#cli-verification-commands)
9. [All REST API Endpoints](#all-rest-api-endpoints)
10. [Troubleshooting](#troubleshooting)
11. [Documentation Index](#documentation-index)
12. [License](#license)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ARDUINO UNO Q  (192.168.1.17 — Edge SBC, Debian aarch64)              │
│                                                                          │
│  BNO086 IMU ──I2C(Wire2, 0x4B)──► imu_publisher.py ──► /imu/data      │
│  RPLidar C1 ──USB(/dev/ttyUSB0)──► rplidar_node ────► /scan            │
│                                                                          │
│  Both nodes run inside a single Docker container "rplidar"              │
│  IMU data relayed through arduino-router IPC socket                     │
└────────────────────────────┬────────────────────────────────────────────┘
                             │  Wi-Fi  ·  CycloneDDS  ·  ROS_DOMAIN_ID=42
┌────────────────────────────▼────────────────────────────────────────────┐
│  LAPTOP  (192.168.1.15 — DevContainer "thirsty_burnell", ROS 2 Jazzy)  │
│                                                                          │
│  qos_relay.py   ── 50 Hz TF (map→odom→base_link→laser)                 │
│                 ── Tilt-aware scan gating (BNO086 roll/pitch guard)     │
│  slam_toolbox   ── Async 2D SLAM mapper                                 │
│  map_regularizer── Post-process maps → boxy 90° CAD walls              │
│  Flask app.py   ── Web Dashboard at http://localhost:5050               │
│  RViz2          ── Live 3D visualization                                │
└─────────────────────────────────────────────────────────────────────────┘
```

The **single entry point** for the whole system is:
```bash
cd ~/my_robot_ws
./start_dashboard.sh
```
Then open **http://localhost:5050** in your browser. Everything else is controlled from the Web UI.

---

## Hardware You Need

| Component | Details | Purpose |
|-----------|---------|---------|
| **Arduino Uno Q** | Qualcomm QRB2210, aarch64, 2 GB RAM, Debian | Edge SBC running Docker sensor nodes |
| **RPLidar C1** | Slamtec, USB, 460800 baud, 16m range, 10 Hz | 2D laser scanner |
| **7Semi BNO086** | ES-12243 breakout, I2C, 9-DOF | IMU — orientation, gyro, accel |
| **USB Power Bank** | 5V 3A+ output | Powers the Uno Q + LiDAR during handheld mapping |
| **USB-A to USB-C cable** | For LiDAR connection | LiDAR data + motor power |
| **Dupont jumper wires** | 5 wires | IMU ↔ Uno Q I2C connection |
| **Development Laptop** | Ubuntu, Docker, VS Code, Wi-Fi | Runs SLAM, dashboard, RViz |

**IMU wiring (BNO086 → Uno Q):**

| BNO086 Pin | Uno Q Pin | Notes |
|------------|-----------|-------|
| VCC | 3.3V | **Use 3.3V not 5V** |
| GND | GND | Common ground |
| SDA | A4 | Routed to Wire2 (I2C2) |
| SCL | A5 | Routed to Wire2 (I2C2) |
| INT | D2 | Data-ready interrupt, INPUT_PULLUP |

> I2C address: **0x4B** (ADDR pin pulled high on the ES-12243 board)

---

## Software Prerequisites

### On the Laptop (Development Machine):

| Tool | Version | Install |
|------|---------|---------|
| **Docker Engine** | 24.x+ | `curl -fsSL https://get.docker.com \| sh` |
| **VS Code** | Latest | [code.visualstudio.com](https://code.visualstudio.com) |
| **Dev Containers extension** | Latest | VS Code: `ms-vscode-remote.remote-containers` |
| **GitHub CLI** | Latest | `sudo apt install gh` (for issue management) |

> **Note:** You do NOT need to install ROS 2 on your host machine. Everything runs inside the DevContainer.

### On the Arduino Uno Q (Edge Board):

| Tool | Install command |
|------|----------------|
| **Docker** | `curl -fsSL https://get.docker.com \| sh` |
| **Python 3 + pyserial** | `sudo apt install python3 python3-pip && pip3 install pyserial` |
| **arduino-router** | Installed as part of edge deployment script |

### Arduino IDE (for firmware):
- **Arduino IDE 2.x** with Arduino Uno Q board support
- Required library: `SparkFun BNO08x Cortex` (install from Library Manager)

---

## Repository Structure

```
my_robot_ws/
│
├── 📄 README.md                         ← You are here — start here
├── 📄 GEMINI.md / AGENTS.md            ← AI agent memory & anti-mistake rules
├── 📄 AI_AGENT_CONTEXT_AND_DEVELOPMENT_LOG.md  ← Full project dev log
├── 📄 cyclonedds.xml                   ← CycloneDDS network config (peer IPs)
├── 📄 start_dashboard.sh               ← ⭐ MAIN ENTRY POINT — run this!
├── 📄 start_mapping.sh                 ← Alternative: headless SLAM only
├── 📄 launch_all.sh                    ← Launch all ROS nodes manually
│
├── src/
│   ├── my_robot_dashboard/             ← Flask Web Dashboard (Port 5050)
│   │   ├── app.py                      ← Backend: all REST APIs + ROS thread
│   │   ├── templates/index.html        ← Web UI (HTML/CSS/JS)
│   │   └── static/js/app.js           ← Frontend JavaScript
│   │
│   ├── my_robot_nav/                   ← Navigation & SLAM
│   │   ├── scripts/qos_relay.py        ← 50Hz TF bridge + tilt scan filter
│   │   ├── scripts/map_regularizer.py  ← Manhattan 90° boxy wall snapper
│   │   ├── config/slam_toolbox_params.yaml  ← SLAM tuning
│   │   └── maps/                       ← Saved maps (.pgm + .yaml)
│   │
│   ├── my_robot_bringup/              ← ROS 2 launch files
│   │   └── launch/imu_slam.launch.py  ← Full sensor fusion launch
│   │
│   ├── bno08x_ros/                    ← BNO086 IMU ROS 2 driver
│   ├── my_robot_bridge/               ← Edge ↔ laptop bridge nodes
│   ├── my_robot_description/          ← URDF robot model
│   ├── my_robot_gazebo/               ← Gazebo simulation (dev/test)
│   └── rplidar_ros/                   ← RPLidar C1 ROS 2 driver
│
├── uno_q_firmware/
│   └── BnoTest/BnoTest.ino            ← Arduino firmware for BNO086 IMU
│
├── scripts/
│   ├── deploy_lidar_docker.py         ← Deploy sensor Docker to Uno Q
│   └── install_deps.sh                ← Workspace dependency installer
│
└── docs/
    ├── SETUP.md                       ← Full environment setup guide
    ├── USAGE_GUIDE.md                 ← Day-to-day operational guide
    ├── DASHBOARD.md                   ← Web dashboard API & UI reference
    ├── ARCHITECTURE.md                ← System architecture deep-dive
    ├── UNO_Q_DEPLOYMENT.md            ← Edge board Docker deployment
    └── DEVELOPMENT_NOTES.md           ← Historical debugging notes
```

---

## First-Time Setup — Step by Step

### Step 1: Clone the Repository

On your **laptop**, open a terminal:

```bash
git clone https://github.com/akash-adhikary/distributed-ros2-robot.git my_robot_ws
cd my_robot_ws
```

---

### Step 2: Open the DevContainer on the Laptop

The entire ROS 2 environment runs in a pre-configured Docker container. You do **not** need to install ROS 2 on your host machine.

**Option A — VS Code (recommended):**
1. Open VS Code: `code .` (from inside `my_robot_ws/`)
2. VS Code will detect `.devcontainer/devcontainer.json` and show a popup:  
   **"Folder contains a Dev Container configuration file. Reopen in Container?"**
3. Click **"Reopen in Container"**
4. Wait ~5–10 minutes for the image to build (first time only — uses cache after that)
5. The integrated terminal inside VS Code is now **inside the ROS 2 container**

**Option B — Terminal only (no VS Code):**
```bash
# Build the container image (first time)
docker build -t my_robot_ws:jazzy -f .devcontainer/Dockerfile .

# Allow GUI apps (RViz2) to connect to your display
xhost +local:root

# Run the container
docker run -it --rm \
    --net=host \
    --ipc=host \
    --privileged \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v $(pwd):/home/ros/my_robot_ws \
    my_robot_ws:jazzy bash
```

---

### Step 3: Build the ROS 2 Workspace

**Inside the DevContainer terminal:**

```bash
# Navigate to workspace root
cd /home/ros/my_robot_ws

# Install any missing system dependencies
bash scripts/install_deps.sh

# Build all packages (symlink-install avoids copying large files)
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

# Source the workspace overlay — you must do this in every new terminal
source install/setup.bash
```

> ⚠️ **Important:** If you open a new terminal tab inside the DevContainer, you must re-run `source install/setup.bash`. To make it permanent, add it to `~/.bashrc` inside the container.

**Verify the build succeeded:**
```bash
# You should see no errors and these packages listed:
ros2 pkg list | grep my_robot
# Expected output:
# my_robot_bringup
# my_robot_dashboard
# my_robot_description
# my_robot_nav
```

---

### Step 4: Flash the BNO086 IMU Firmware (Arduino Uno Q)

This step installs the custom firmware that reads the BNO086 sensor and sends data over USB to the arduino-router service.

**On your laptop, connect the Arduino Uno Q via USB:**

1. Open **Arduino IDE 2.x**
2. Install the **SparkFun BNO08x Cortex** library:  
   `Tools → Manage Libraries → Search "SparkFun BNO08x" → Install`
3. Select board: `Tools → Board → Arduino Uno Q`
4. Select the correct COM/USB port: `Tools → Port → /dev/ttyACM0` (or similar)
5. Open the firmware file:  
   `File → Open → my_robot_ws/uno_q_firmware/BnoTest/BnoTest.ino`
6. Click **Upload** (Ctrl+U)
7. Open Serial Monitor (115200 baud) and verify output like:  
   ```
   imu/raw,-0.012,0.003,0.998,0.061,0.0021,-0.0008,9.53,0.001,-0.002
   ```

> The firmware sends a single comma-separated line at ~100 Hz per the format:  
> `imu/raw, qW, qX, qY, qZ, gX, gY, gZ, aX, aY, aZ`

---

### Step 5: Deploy the Sensor Docker Container to the Uno Q

The RPLidar C1 and IMU publisher both run inside a single Docker container on the Uno Q.

**From your laptop, SSH into the Uno Q:**
```bash
ssh arduino@192.168.1.17
# Default password: (see project secrets / your team)
```

**On the Uno Q, set up the Docker workspace:**
```bash
# Create workspace directory on external pendrive (saves eMMC wear)
mkdir -p /home/arduino/pendrive/ros_ws/src
cd /home/arduino/pendrive/ros_ws/src

# Clone the RPLidar driver
git clone -b ros2 https://github.com/Slamtec/rplidar_ros.git
```

**Build the Docker image on the Uno Q:**
```bash
cd /home/arduino/pendrive/ros_ws

# Create the Dockerfile (copy from below or use the deploy script from laptop)
cat > Dockerfile << 'EOF'
FROM ros:jazzy-ros-base

RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    ros-jazzy-rmw-cyclonedds-cpp \
    python3-pip \
    && pip3 install pyserial msgpack \
    && rm -rf /var/lib/apt/lists/*

ENV ROS_DOMAIN_ID=42
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
EOF

# Build the image (takes 5-10 minutes on Uno Q)
sudo docker build -t uno_ros_base .
```

**Build the RPLidar package inside the container:**
```bash
sudo docker run --rm \
  -v /home/arduino/pendrive/ros_ws:/ws \
  uno_ros_base \
  bash -c "source /opt/ros/jazzy/setup.bash && cd /ws && colcon build"
```

**Create the startup script on the Uno Q:**
```bash
cat > /home/arduino/start_rplidar.sh << 'EOF'
#!/bin/bash
echo "=== Setting USB permissions ==="
sudo chmod a+rw /dev/ttyUSB0

echo "=== Stopping any old containers ==="
sudo docker rm -f rplidar 2>/dev/null || true

echo "=== Starting RPLidar + IMU container ==="
sudo docker run -d \
  --name rplidar \
  --net=host \
  --privileged \
  -v /home/arduino/pendrive/ros_ws:/ws \
  -v /dev/ttyUSB0:/dev/ttyUSB0 \
  -v /var/run/arduino-router.sock:/var/run/arduino-router.sock \
  uno_ros_base \
  bash -c "
    source /opt/ros/jazzy/setup.bash
    source /ws/install/setup.bash
    export ROS_DOMAIN_ID=42
    export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
    ros2 launch rplidar_ros rplidar_c1_launch.py &
    python3 /ws/src/imu_publisher.py &
    wait
  "

echo "=== Container started! Check logs: sudo docker logs -f rplidar ==="
EOF

chmod +x /home/arduino/start_rplidar.sh
```

**Start the container:**
```bash
bash /home/arduino/start_rplidar.sh
```

**Verify it's working (from the Uno Q):**
```bash
sudo docker logs -f rplidar
# You should see:
# RPLIDAR running on /dev/ttyUSB0
# [imu_publisher]: Publishing IMU data @ 100 Hz
```

---

### Step 6: Configure CycloneDDS Networking

Both the Uno Q and the laptop **must** use the same DDS configuration so ROS 2 topics cross the Wi-Fi bridge.

**On the Laptop (inside the DevContainer):**

The `cyclonedds.xml` file is already in the repo root. Edit it to match your network:
```bash
nano /home/ros/my_robot_ws/cyclonedds.xml
```

The file should look like this (update IP addresses to match your network):
```xml
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config">
    <Domain id="any">
        <General>
            <Interfaces>
                <!-- Your laptop's Wi-Fi interface name (run: ip link show) -->
                <NetworkInterface name="wlp4s0" multicast="true" />
            </Interfaces>
            <AllowMulticast>true</AllowMulticast>
        </General>
        <Discovery>
            <Peers>
                <!-- Uno Q IP address -->
                <Peer address="192.168.1.17"/>
            </Peers>
            <ParticipantIndex>auto</ParticipantIndex>
            <MaxAutoParticipantIndex>120</MaxAutoParticipantIndex>
        </Discovery>
    </Domain>
</CycloneDDS>
```

**Find your Wi-Fi interface name:**
```bash
ip link show | grep -E "^[0-9]+: w"
# Example output: "3: wlp4s0: <BROADCAST,MULTICAST,UP,LOWER_UP>"
# Use "wlp4s0" in the XML above
```

**Set environment variables in the DevContainer's `~/.bashrc`:**
```bash
echo 'export ROS_DOMAIN_ID=42' >> ~/.bashrc
echo 'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp' >> ~/.bashrc
echo 'export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml' >> ~/.bashrc
source ~/.bashrc
```

**Verify the Uno Q is reachable and topics are flowing:**
```bash
# From inside the DevContainer
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 topic list
# You should see /scan and /imu/data in the list

ros2 topic hz /scan
# Expected: average rate: 10.xxx

ros2 topic hz /imu/data
# Expected: average rate: 100.xxx
```

If you do NOT see those topics, check:
1. Both devices are on the same Wi-Fi LAN
2. The Docker container on the Uno Q is running (`sudo docker ps`)
3. The cyclonedds.xml peer IP matches the Uno Q's actual IP (`ip addr` on Uno Q)

---

## Daily Usage — Start the System

Once setup is complete, every session follows these steps:

### 1. Start the Uno Q edge node

```bash
ssh arduino@192.168.1.17
bash /home/arduino/start_rplidar.sh
exit
```

### 2. Start the Dashboard (from your laptop)

**If you are INSIDE the DevContainer terminal:**
```bash
cd /home/ros/my_robot_ws
python3 src/my_robot_dashboard/app.py
```

**If you are on the HOST machine (outside Docker):**
```bash
cd ~/my_robot_ws
./start_dashboard.sh
```
> `start_dashboard.sh` automatically detects whether you are inside or outside the container and runs `app.py` in the right context. It also enforces the singleton — if an old instance is running, it gracefully kills it first.

### 3. Open the Web UI

Open your browser and go to:
```
http://localhost:5050
```

### 4. Map your space

From the Web UI:
1. Click **"Start SLAM"** — this launches `qos_relay.py`, `slam_toolbox`, and opens RViz2
2. Wait ~5 seconds for the message "SLAM active" to appear in the status panel
3. **Pick up the Uno Q** (with power bank) and slowly walk through all rooms
   - Move at a walking pace — do NOT run
   - Revisit doorways and corridors to close loops
   - Keep the LiDAR roughly level (tilt gating handles small tilts < 7.5°)
4. Watch the map grow in RViz2 in real time
5. When finished mapping, click **"Save Map"** in the Web UI
6. (Optional) Click **"Snap to 90° Boxy Walls"** to regularize the map into clean orthogonal room shapes

### 5. Emergency controls

- **Reset Nodes** (Web UI button or CLI): Kills all ROS processes and restarts clean
  ```bash
  curl -X POST http://localhost:5050/api/system/kill_all
  ```
- **Full Shutdown** (Web UI button or CLI): Kills everything including the dashboard server
  ```bash
  curl -X POST http://localhost:5050/api/system/shutdown_all
  ```

---

## Web Dashboard Guide

See **[docs/DASHBOARD.md](docs/DASHBOARD.md)** for the full reference. Quick summary:

| UI Button | API Endpoint | What it does |
|-----------|-------------|--------------|
| Start SLAM | `POST /api/slam/start` | Launches qos_relay + slam_toolbox + RViz2 |
| Stop SLAM | `POST /api/slam/stop` | Kills SLAM and qos_relay |
| Save Map | `POST /api/slam/save_map` | Saves .pgm + .yaml to maps/ folder |
| Snap to 90° Boxy Walls | `POST /api/slam/regularize_map` | Runs Manhattan wall regularizer |
| Start LiDAR | `POST /api/sensors/lidar/start` | SSH to Uno Q, starts rplidar Docker |
| Start IMU | `POST /api/sensors/imu/start` | SSH to Uno Q, starts imu_publisher |
| Reset Nodes | `POST /api/system/kill_all` | Kills all ROS processes |
| Shutdown All & Exit | `POST /api/system/shutdown_all` | Full system shutdown |
| Live Telemetry | `GET /api/stream` | SSE stream: IMU quaternion, scan rate |

---

## CLI Verification Commands

Run these inside the DevContainer to verify the system is healthy:

```bash
# Source the environment first (required in every new terminal)
source /opt/ros/jazzy/setup.bash
source /home/ros/my_robot_ws/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml

# Check all topics are flowing
ros2 topic list

# Verify LiDAR rate (should be ~10 Hz)
ros2 topic hz /scan

# Verify IMU rate (should be ~100 Hz)
ros2 topic hz /imu/data

# Check TF tree is publishing (after starting SLAM)
ros2 run tf2_ros tf2_echo odom base_link

# View raw IMU data
ros2 topic echo /imu/data --once

# View a single laser scan message
ros2 topic echo /scan --once

# Check that qos_relay is re-publishing scans with QoS
ros2 topic hz /scan_reliable
```

---

## All REST API Endpoints

Full curl examples for every endpoint (run from any machine on the same LAN):

```bash
# ── SLAM CONTROL ─────────────────────────────────────────────────────────

# Start SLAM (launches qos_relay + slam_toolbox + RViz2)
curl -X POST http://localhost:5050/api/slam/start \
  -H "Content-Type: application/json" -d '{}'

# Stop SLAM
curl -X POST http://localhost:5050/api/slam/stop \
  -H "Content-Type: application/json" -d '{}'

# Save the current map to disk
curl -X POST http://localhost:5050/api/slam/save_map \
  -H "Content-Type: application/json" -d '{"filename": "my_living_room"}'

# Regularize (snap walls to 90° boxy shapes)
curl -X POST http://localhost:5050/api/slam/regularize_map \
  -H "Content-Type: application/json" -d '{}'

# List all saved maps
curl http://localhost:5050/api/slam/list_maps

# ── SENSOR CONTROL ───────────────────────────────────────────────────────

# Start LiDAR on Uno Q (SSH + Docker)
curl -X POST http://localhost:5050/api/sensors/lidar/start \
  -H "Content-Type: application/json" -d '{}'

# Stop LiDAR
curl -X POST http://localhost:5050/api/sensors/lidar/stop \
  -H "Content-Type: application/json" -d '{}'

# Start IMU publisher on Uno Q
curl -X POST http://localhost:5050/api/sensors/imu/start \
  -H "Content-Type: application/json" -d '{}'

# Stop IMU publisher
curl -X POST http://localhost:5050/api/sensors/imu/stop \
  -H "Content-Type: application/json" -d '{}'

# Restart arduino-router on Uno Q
curl -X POST http://localhost:5050/api/sensors/router/restart \
  -H "Content-Type: application/json" -d '{}'

# Reboot Uno Q
curl -X POST http://localhost:5050/api/sensors/unoq/reboot \
  -H "Content-Type: application/json" -d '{}'

# ── RVIZ2 ────────────────────────────────────────────────────────────────

# Launch RViz2 (mode: "scan" | "slam" | "imu")
curl -X POST http://localhost:5050/api/rviz/launch/slam \
  -H "Content-Type: application/json" -d '{}'

# Stop RViz2
curl -X POST http://localhost:5050/api/rviz/stop \
  -H "Content-Type: application/json" -d '{}'

# ── SYSTEM CONTROL ───────────────────────────────────────────────────────

# Kill all ROS nodes (soft reset — dashboard stays running)
curl -X POST http://localhost:5050/api/system/kill_all \
  -H "Content-Type: application/json" -d '{}'

# Full shutdown — kills nodes AND exits app.py
curl -X POST http://localhost:5050/api/system/shutdown_all \
  -H "Content-Type: application/json" -d '{}'

# ── TELEMETRY ─────────────────────────────────────────────────────────────

# Get latest IMU + scan telemetry (JSON snapshot)
curl http://localhost:5050/api/telemetry

# Subscribe to live SSE stream (streams forever, Ctrl+C to stop)
curl -N http://localhost:5050/api/stream
```

---

## Troubleshooting

| Problem | Symptoms | Fix |
|---------|----------|-----|
| **No `/scan` on laptop** | `ros2 topic hz /scan` shows nothing | SSH to Uno Q and run `bash /home/arduino/start_rplidar.sh`. Verify with `sudo docker logs -f rplidar` |
| **No `/imu/data` on laptop** | `ros2 topic hz /imu/data` shows nothing | Check arduino-router: `sudo systemctl status arduino-router`. Check BNO086 wiring (SDA=A4, SCL=A5, 3.3V, 0x4B) |
| **Map not appearing in RViz2** | RViz2 opens but no map | Wait 5–7s for slam_toolbox to activate. Fixed frame must be `map`. Verify `/scan` is arriving |
| **Map overlaps when returning to room** | Rooms appear duplicated | Walk more slowly. Revisit corridors for loop closure. SLAM params already tuned: 12m loop search, 30 scan buffer |
| **`400 Bad Request` from Dashboard** | API buttons show 400 error | All Flask routes use `request.get_json(silent=True) or {}` — should not happen. Check server logs |
| **`JSON.parse` error in browser** | Toast shows "SyntaxError: unexpected character" | Hard-refresh browser (Ctrl+Shift+R) to clear cached JS. Check `?v=5.0` in index.html |
| **Port 5050 already in use** | Dashboard fails to start | `kill -9 $(lsof -ti:5050)`. The PID lockfile at `/tmp/my_robot_dashboard.pid` handles this automatically in `start_dashboard.sh` |
| **Zombie ROS processes** | Old nodes interfere with new session | From Web UI: click "Reset Nodes". Or: `curl -X POST http://localhost:5050/api/system/kill_all` |
| **LiDAR not spinning** | Container starts but no scan data | On Uno Q: `sudo chmod a+rw /dev/ttyUSB0` then restart container. The startup script does this automatically |
| **IMU tilt gating active** | Map looks sparse (many inf rays) | This is correct behavior when tilted > 7.5°. Hold the device level. Rays that would hit floor/ceiling are intentionally removed |
| **CycloneDDS no discovery** | Topics don't cross Wi-Fi | Verify `wlp4s0` in cyclonedds.xml matches your actual Wi-Fi interface. Both must have `ROS_DOMAIN_ID=42` |
| **RViz2 crashes instantly** | `exit code -6`, Qt errors | Run `xhost +local:root` on HOST before starting container |

---

## Documentation Index

| Document | Description |
|----------|-------------|
| **[docs/SETUP.md](docs/SETUP.md)** | Complete environment setup — DevContainer, Uno Q, CycloneDDS |
| **[docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md)** | Day-to-day operational guide — full workflow every session |
| **[docs/DASHBOARD.md](docs/DASHBOARD.md)** | Web dashboard guide — all UI elements, API endpoints, curl examples |
| **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Full system architecture — node graph, topics, design decisions |
| **[docs/UNO_Q_DEPLOYMENT.md](docs/UNO_Q_DEPLOYMENT.md)** | Uno Q Docker deployment reference |
| **[docs/DEVELOPMENT_NOTES.md](docs/DEVELOPMENT_NOTES.md)** | Simulation debugging history |
| **[GEMINI.md](GEMINI.md)** | AI agent memory — pre-flight checklist, failure catalog, rules |
| **[AI_AGENT_CONTEXT_AND_DEVELOPMENT_LOG.md](AI_AGENT_CONTEXT_AND_DEVELOPMENT_LOG.md)** | Full project development log |

---

## License

MIT License — see `LICENSE` file for details.
