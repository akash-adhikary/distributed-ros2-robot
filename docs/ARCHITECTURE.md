# 🤖 Robot System Architecture Design Document

> **Version**: 1.0 | **Status**: Living Document — Enhancements Welcome
>
> **Purpose**: Technical reference for AI agents and human developers.
> Defines the distributed system architecture for a ROS 2–based autonomous robot
> using an Arduino Uno Q (edge SBC) and a development laptop as the compute hub.

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

### 3.1 Laptop Nodes (High Computation, Dev Environment)

| Node | Package | Responsibility |
|------|---------|----------------|
| `slam_toolbox` | `slam_toolbox` | Build and update occupancy map from `/scan` |
| `nav2_bringup` | `nav2_bringup` | Path planning (global + local), costmaps, AMCL |
| `rviz2` | `rviz2` | Visualization: map, scan, TF, goals |
| `gazebo_sim` | `ros_gz` | Simulation only (dev/test) — not used in production |
| `map_server` | `nav2_map_server` | Serve the pre-saved map to AMCL |

> **Why laptop?** Nav2 easily peaks at 800 MB RAM + heavy CPU. Offloading this keeps Uno Q free for real-time tasks.

### 3.2 Uno Q Nodes (Hardware Close, Real-Time)

| Node | Package | Responsibility | RAM Estimate |
|------|---------|----------------|-------------|
| `rplidar_node` | `rplidar_ros` | Publish `/scan` from physical RPLIDAR C1 | ~30 MB |
| `serial_bridge` | custom node | Translate `cmd_vel` → motor controller serial commands | ~20 MB |
| `robot_state_publisher` | `robot_state_publisher` | Publish `/tf` from URDF (static only) | ~15 MB |
| `static_tf_broadcaster` | `tf2_ros` | Broadcast `odom → base_footprint` when no encoders | ~5 MB |

> **Total Uno Q RAM budget**: ~70–100 MB active ROS nodes (well within 2 GB limit).

---

## 📡 4. Topic Architecture

```
Laptop (Nav2) ──────→ /cmd_vel ──────────────→ Uno Q (serial_bridge)
                                                       │
                                               Motor Controller (USB)

Uno Q (rplidar) ──→ /scan ───────────────────→ Laptop (Nav2 costmaps, SLAM)

Uno Q (odometry) ─→ /odom ───────────────────→ Laptop (AMCL localization)

Laptop (Nav2) ──────→ /goal_pose ─────────────→ bt_navigator (Laptop)

Laptop (map_server) → /map ────────────────────→ RViz2, AMCL, costmaps
```

### Critical Topics Reference

| Topic | Type | Publisher | Subscribers |
|-------|------|-----------|-------------|
| `/scan` | `sensor_msgs/LaserScan` | Uno Q rplidar_node | Nav2 costmaps, SLAM, RViz2 |
| `/odom` | `nav_msgs/Odometry` | Uno Q (encoder bridge or static) | Nav2 AMCL, controller |
| `/cmd_vel` | `geometry_msgs/Twist` | Nav2 collision_monitor | Uno Q serial_bridge |
| `/map` | `nav_msgs/OccupancyGrid` | Laptop map_server | AMCL, costmaps, RViz2 |
| `/tf` | `tf2_msgs/TFMessage` | robot_state_publisher | All navigation nodes |
| `/initialpose` | `PoseWithCovarianceStamped` | RViz2 2D Pose Estimate | AMCL |
| `/goal_pose` | `geometry_msgs/PoseStamped` | RViz2 2D Goal Pose | bt_navigator |

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

### Phase 1 — Sensor Integration ✅ (Mostly Done)
- [x] RPLIDAR C1 working with ROS 2 driver on laptop
- [x] Nav2 simulation tested and validated
- [x] Map saved from Gazebo simulation
- [x] Uno Q pendrive mounted with full read/write
- [ ] RPLIDAR driver installed and tested on Uno Q
- [ ] DDS multi-machine discovery verified between laptop and Uno Q

### Phase 2 — Hardware Bridge
- [ ] Uno Q publishes `/scan` over Wi-Fi to laptop Nav2
- [ ] Real-world map building with RPLIDAR over LAN

### Phase 3 — Motor Control
- [ ] `serial_bridge` translates `/cmd_vel` to motor serial commands
- [ ] Odometry published from wheel encoders
- [ ] Full closed-loop: Laptop plans → Uno Q executes

### Phase 4 — Autonomy & Polish
- [ ] SLAM + Autonomous navigation on physical robot
- [ ] Frontier exploration (auto-mapping)
- [ ] Systemd auto-start on Uno Q boot
- [ ] Remote monitoring dashboard (optional)

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
