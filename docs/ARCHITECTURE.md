# 🤖 Robot System Architecture Design Document

> **Version**: 2.0 | **Status**: Phase 2 Complete — Phase 3 (Motor Control) In Progress
>
> **Purpose**: Technical reference for AI agents and human developers.
> Defines the distributed system architecture for a ROS 2–based autonomous robot
> using an Arduino Uno Q (edge SBC, 192.168.1.17) and a development laptop (192.168.1.15) as the compute hub.
>
> **Single entry point:** `./start_dashboard.sh` → open http://localhost:5050

---

## 📐 1. Design Philosophy

| Principle | Description |
|-----------|-------------|
| **Edge-Lite** | The Uno Q runs only hardware-close, real-time nodes. Heavy computation stays on the laptop. |
| **Composable** | Every subsystem is independent and can be replaced, upgraded, or run separately. |
| **Gradual** | Start minimal. Add components only when needed. Never pre-optimize prematurely. |
| **Recoverable** | Every service should be auto-restartable. Hardware failures should not crash the whole stack. |
| **Storage-Aware** | Use the pendrive (`/home/arduino/pendrive/`) for all large files: workspace, maps, logs, models. |

---

## 🏗️ 2. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  DEVELOPMENT LAPTOP                             │
│          (Ubuntu 26.04, x86_64, Docker DevContainer)           │
│                                                                  │
│  ┌─────────────────┐   ┌──────────────────┐   ┌────────────┐   │
│  │  Gazebo Sim      │   │  Nav2 Stack       │   │  RViz2     │   │
│  │  (Dev/Test only) │   │  (SLAM, Planner,  │   │  (Viz &    │   │
│  │                  │   │  Controller,      │   │  Goal UI)  │   │
│  │                  │   │  Costmaps)        │   │            │   │
│  └─────────────────┘   └──────────────────┘   └────────────┘   │
│                                │                                 │
│              ROS 2 DDS (Cyclone DDS over Wi-Fi)                 │
└─────────────────────────────────────────────────────────────────┘
                                 │
                  Wi-Fi (LAN, ~5ms typical latency)
                                 │
┌─────────────────────────────────────────────────────────────────┐
│              ARDUINO UNO Q EDGE SBC                             │
│     (Qualcomm QRB2210, aarch64 Debian, 2GB RAM, 14.6GB eMMC)   │
│                                                                  │
│  ┌─────────────────┐   ┌──────────────────┐   ┌────────────┐   │
│  │  RPLIDAR C1      │   │  Serial Bridge    │   │  Watchdog  │   │
│  │  Driver Node     │   │  (cmd_vel →       │   │  & Health  │   │
│  │  (/scan)         │   │  motor encoder)   │   │  Monitor   │   │
│  └─────────────────┘   └──────────────────┘   └────────────┘   │
│                    │                  │                          │
│              USB Serial          USB Serial                      │
│                    │                  │                          │
│             RPLIDAR C1         Arduino Motor Controller           │
│                              (Differential Drive)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ 3. Node Distribution

### 3.1 Laptop Nodes — DevContainer `thirsty_burnell` (192.168.1.15)

| Node / Script | Package | Responsibility | Status |
|---|---|---|---|
| `app.py` (Flask Dashboard) | `my_robot_dashboard` | Web UI + REST API + SSE telemetry @ port 5050 | ✅ Running |
| `qos_relay.py` | `my_robot_nav` | 50 Hz TF broadcaster (map→odom→base_link→laser) + IMU tilt scan gating | ✅ Running |
| `slam_toolbox` | `slam_toolbox` | Async 2D SLAM — builds and updates occupancy map from `/scan_reliable` | ✅ Running |
| `map_regularizer.py` | `my_robot_nav` | Post-processing: Manhattan 90° wall snapper, SVG CAD export | ✅ On-demand |
| `rviz2` | `rviz2` | 3D visualization: map, scan, TF, IMU orientation | ✅ On-demand |
| `nav2_bringup` | `nav2_bringup` | Full Nav2 stack (planned — Phase 3) | 🔲 Not yet |

> **Why laptop?** slam_toolbox peaks at 400–800 MB RAM. map_regularizer uses OpenCV. The Flask dashboard requires Python 3.10+. All offloaded to keep Uno Q free for real-time sensor tasks.

### 3.2 Uno Q Nodes — Docker container `rplidar` (192.168.1.17)

| Node / Script | Package | Responsibility | Frequency |
|---|---|---|---|
| `rplidar_node` | `rplidar_ros` | Publish `/scan` from RPLidar C1 at `/dev/ttyUSB0` @ 460800 baud | 10 Hz |
| `imu_publisher.py` | custom | Read BNO086 data from `arduino-router` IPC socket, publish `/imu/data` | 100 Hz |
| `robot_state_publisher` | future | Publish TF from URDF static transforms | future |

> **Total Uno Q RAM budget**: ~60 MB active (well within 2 GB limit).



---

## 📡 4. Topic Architecture

```
Uno Q (rplidar_node) ──► /scan (10 Hz, BEST_EFFORT QoS) ──────────────────► Laptop
                                                                               │
Uno Q (imu_publisher) ──► /imu/data (100 Hz) ─────────────────────────────► Laptop
                                                                               │
Laptop (qos_relay.py) ──► /scan_reliable (10 Hz, RELIABLE QoS) ───────────► slam_toolbox
Laptop (qos_relay.py) ──► /imu_reliable (100 Hz, RELIABLE QoS) ───────────► future nodes
Laptop (qos_relay.py) ──► /tf: odom → base_link (50 Hz dynamic TF) ───────► slam_toolbox, RViz2
Laptop (qos_relay.py) ──► /tf: base_link → laser (static TF) ─────────────► slam_toolbox, RViz2

Laptop (slam_toolbox) ──► /map (OccupancyGrid, async) ────────────────────► RViz2, map_saver
Laptop (slam_toolbox) ──► /tf: map → odom ─────────────────────────────────► RViz2

Laptop (nav2) ──────────► /cmd_vel ────────────────────────────────────────► Uno Q (Phase 3)
Uno Q (encoders) ────────► /odom ──────────────────────────────────────────► Laptop (Phase 3)
```

### Current Active Topics Reference

| Topic | Type | Publisher | Subscribers | Rate |
|-------|------|-----------|-------------|------|
| `/scan` | `sensor_msgs/LaserScan` | Uno Q `rplidar_node` | `qos_relay.py` | 10 Hz |
| `/imu/data` | `sensor_msgs/Imu` | Uno Q `imu_publisher.py` | `qos_relay.py` | 100 Hz |
| `/scan_reliable` | `sensor_msgs/LaserScan` | `qos_relay.py` | `slam_toolbox`, RViz2 | 10 Hz |
| `/imu_reliable` | `sensor_msgs/Imu` | `qos_relay.py` | future | 100 Hz |
| `/map` | `nav_msgs/OccupancyGrid` | `slam_toolbox` | RViz2, map_saver | async |
| `/tf` (odom→base_link) | `tf2_msgs/TFMessage` | `qos_relay.py` | all nav nodes | 50 Hz |
| `/tf` (map→odom) | `tf2_msgs/TFMessage` | `slam_toolbox` | all nav nodes | async |

### Future Topics (Phase 3)

| Topic | Type | Direction |
|-------|------|-----------|
| `/cmd_vel` | `geometry_msgs/Twist` | Laptop → Uno Q motor controller |
| `/odom` | `nav_msgs/Odometry` | Uno Q encoder bridge → Laptop Nav2 |
| `/goal_pose` | `geometry_msgs/PoseStamped` | RViz2 → Nav2 bt_navigator |



---

## 💾 5. Storage Architecture

```
Uno Q Internal eMMC (14.6 GB total, ~2.7 GB free on /)
├── /                   (System OS, Debian packages)
├── /home/arduino/      (User home, 3.6 GB partition, 2.7 GB free)
│
/home/arduino/pendrive/ [USB Drive, 115 GB, 109 GB free]
├── ros_ws/          ← Full ROS 2 workspace built from source
│   ├── src/         ← Cloned packages (rplidar_ros, etc.)
│   └── install/     ← Compiled binaries
├── maps/            ← Saved map files (.pgm, .yaml) synced from laptop
├── config/          ← Robot parameter YAML files
├── logs/            ← ROS 2 logs (~/.ros/log → symlink here)
└── models/          ← Any ML model files (future)
```

### Symlinks to Redirect Heavy Storage to Pendrive
```bash
ln -sf /home/arduino/pendrive/logs ~/.ros/log
ln -sf /home/arduino/pendrive/ros_ws ~/ros_ws
```

---

## 🔧 6. ROS 2 Multi-Machine Configuration

### 6.1 DDS Discovery
Both machines must use the same `ROS_DOMAIN_ID`. Add to `~/.bashrc` on BOTH:
```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

> **Why CycloneDDS?** Most reliable RMW for multi-host LAN networks. Avoids FastDDS broadcast storms and has better reconnection behavior.

### 6.2 Uno Q Startup Services (systemd)
```text
/etc/systemd/system/robot-lidar.service   → starts rplidar_node
/etc/systemd/system/robot-bridge.service  → starts serial_bridge
```
Both with `Restart=always`.

### 6.3 Bandwidth Budget
| Data | Rate | Size |
|------|------|------|
| `/scan` (RPLIDAR C1) | 10 Hz | ~60–80 KB/s |
| `/cmd_vel` | 20 Hz | ~1 KB/s |
| `/odom` | 20 Hz | ~5 KB/s |
| **Total** | | **~1–2 Mbps** (well within 5 GHz Wi-Fi) |

---

## ⚙️ 7. Development vs Production Modes

| Mode | What Runs on Laptop | What Runs on Uno Q |
|------|--------------------|--------------------|
| **Simulation (Dev)** | Everything (Gazebo, Nav2, RViz2) | Nothing |
| **Hardware Test** | Nav2, RViz2 | rplidar_node |
| **Full Robot** | Nav2, RViz2, map_server | rplidar_node, serial_bridge, robot_state_publisher |
| **Standalone Robot (future)** | Optional telemetry | All nodes including Nav2 |

---

## 🚀 8. Phase-by-Phase Deployment Plan

### Phase 1 — Sensor Integration ✅ COMPLETE

- [x] RPLIDAR C1 working with ROS 2 driver on laptop
- [x] Nav2 simulation tested and validated in Gazebo Harmonic
- [x] Map saved from Gazebo simulation
- [x] Uno Q pendrive mounted with full read/write
- [x] RPLIDAR C1 driver installed and tested on Uno Q (Docker container `rplidar`)
- [x] CycloneDDS multi-machine discovery verified (Laptop ↔ Uno Q Wi-Fi)
- [x] BNO086 9-DOF IMU wired and firmware flashed (`BnoTest.ino`)
- [x] `imu_publisher.py` publishing `/imu/data` @ 100 Hz from Uno Q
- [x] arduino-router IPC bridge running at `/var/run/arduino-router.sock`

### Phase 2 — SLAM Fusion & Control Hub ✅ COMPLETE

- [x] `qos_relay.py` broadcasting 50 Hz `odom → base_link` TF
- [x] IMU tilt-aware scan gating (> 7.5° tilt gates rays > 0.40 m height deviation)
- [x] `slam_toolbox` multi-room SLAM tuned (12m loop closure, 30 scan buffer, 0.80m correlation)
- [x] Full 2D maps built and saved by walking handheld through multiple rooms
- [x] Flask Web Dashboard (`app.py`) running at port 5050
- [x] All sensor controls, SLAM controls, and emergency shutdown via REST API + Web UI
- [x] `map_regularizer.py` Manhattan 90° wall snapper with SVG CAD export
- [x] PID singleton process guard + graceful takeover
- [x] `request.get_json(silent=True)` defensive REST pattern throughout
- [x] Safe JS `res.text()` → try/catch JSON parsing in frontend

### Phase 3 — Motor Control ⬅️ CURRENT PHASE (Not Started)

- [ ] Design and wire motor controller to Uno Q (USB serial)
- [ ] `serial_bridge` node: translate `/cmd_vel` (Twist) → motor PWM serial commands
- [ ] Wheel encoders publish `/odom` from Uno Q
- [ ] Full closed-loop: Laptop Nav2 plans → `/cmd_vel` → Uno Q motor controller → robot moves

### Phase 4 — Autonomous Navigation & Polish

- [ ] Nav2 full stack: global planner, local planner, AMCL localization
- [ ] Frontier exploration (`explore_lite`) for automatic room mapping
- [ ] Systemd service for auto-start on Uno Q boot
- [ ] Battery state publishing from ADC voltage monitor
- [ ] Map export to multiple formats (SVG, DXF, PNG with scale bar)


---

## 🏋️ 9. Optimization Guidelines

### RAM on Uno Q
- Use component containers when running multiple related nodes.
- Never run `rviz2`, `rqt`, or any GUI on Uno Q.
- Use `--ros-args --log-level WARN` to reduce I/O overhead.
- Set `history_depth: 1` QoS for real-time sensor topics.

### CPU on Uno Q
- Use `nice -n -5 <process>` for real-time nodes.
- Use `taskset -c 0,1` to pin hardware nodes to specific cores.

---

## 📂 10. File Layout Reference

```
my_robot_ws/                   ← Laptop workspace (Docker DevContainer)
├── src/
│   ├── my_robot_bringup/      ← Simulation launch files
│   ├── my_robot_description/  ← URDF model
│   ├── my_robot_nav/          ← Nav2 config, maps, launch
│   └── rplidar_ros/           ← RPLIDAR C1 driver (source)
├── scripts/
│   ├── start_sim.sh / start_slam.sh / start_nav.sh
│   ├── drive_teleop.sh / save_map.sh / start_rplidar.sh
│   └── stop_all.sh
└── docs/
    ├── ARCHITECTURE.md        ← This file
    ├── SIMULATION_WORKFLOW.md ← Step-by-step guide
    └── DEVELOPMENT_NOTES.md   ← Troubleshooting history

/home/arduino/pendrive/        ← Uno Q USB drive (115 GB)
├── ros_ws/src/
│   ├── rplidar_ros/           ← RPLIDAR driver (aarch64 build)
│   └── robot_bridge/          ← Serial cmd_vel bridge (Phase 3)
├── maps/                      ← Synced map files from laptop
├── config/                    ← Uno Q parameter YAML files
└── logs/                      ← ROS 2 log redirect
```

---

## 🔮 11. Future Enhancement Avenues

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| **Encoder Odometry** | Wheel encoders → real `/odom` for accurate localization | High |
| **Micro-ROS** | Firmware on STM32/Arduino for motor control | Medium |
| **Frontier Exploration** | `explore_lite` for fully autonomous mapping | Medium |
| **Docker on Uno Q** | Containerized ROS 2 for cleaner deployments | Low |
| **Web Dashboard** | Foxglove or custom UI for telemetry | Low |
| **Camera Integration** | RGB-D or fisheye for visual SLAM | Future |
| **Battery Monitor** | Publish `/battery_state` from ADC voltage divider | Future |

---

## 📝 12. AI Agent Usage Notes

> **For AI Agents reading this document:**

1. **Always check `ROS_DOMAIN_ID=42`** on both machines before testing multi-machine topics.
2. **Use `./scripts/stop_all.sh`** before any fresh launch to avoid port conflicts.
3. **The pendrive is the primary workspace on Uno Q** — always build packages to `/home/arduino/pendrive/ros_ws/`, not to the home directory.
4. **Nav2 is NOT expected to run on Uno Q** in Phase 1–3. Only `rplidar_node` and `robot_bridge` run there.
5. **The RPLIDAR C1 pre-spin workaround** (`scripts/spin_up_motor.py`) is required before launching the ROS 2 driver. See `DEVELOPMENT_NOTES.md`.
6. **Test all changes in simulation first** (Gazebo), then deploy to hardware.
7. **SSH**: `ssh arduino@192.168.1.17` — password in project secrets, never in code.
8. **Never commit passwords or secrets to git**. Use environment variables or `.env` files.
