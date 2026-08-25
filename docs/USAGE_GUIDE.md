# 🗺️ Daily Usage Guide — Distributed ROS 2 Robot Mapping System

This guide covers **everything you need to do each time you want to run the system** — from powering on the hardware to saving and processing a finished map. Read this top-to-bottom your first time; after a few sessions it will be second nature.

---

## Prerequisites Before Every Session

Before starting, confirm:
- [ ] Arduino Uno Q is powered on (LED lit, accessible at `192.168.1.17`)
- [ ] RPLidar C1 is plugged into the Uno Q via USB-A
- [ ] BNO086 IMU is wired correctly (SDA→A4, SCL→A5, VCC→3.3V, INT→D2)
- [ ] Power bank is charged (for handheld mapping walk)
- [ ] Laptop is on the same Wi-Fi LAN as the Uno Q
- [ ] DevContainer `thirsty_burnell` is running (check: `docker ps | grep thirsty_burnell`)

---

## Part 1: Start the Edge Node (Arduino Uno Q)

The Uno Q runs two sensor nodes inside a single Docker container — the RPLidar C1 driver and the BNO086 IMU publisher. You need to start this container every time you power on the Uno Q (it does not auto-start unless you configure systemd).

### 1.1 — SSH into the Uno Q

From your laptop terminal:

```bash
ssh arduino@192.168.1.17
```

> If this is your first SSH to this machine, accept the host key fingerprint by typing `yes` and pressing Enter.

### 1.2 — Verify the LiDAR is physically detected

```bash
ls -la /dev/ttyUSB*
# Expected output: crw-rw-rw- 1 root dialout ... /dev/ttyUSB0
```

If you see `No such file or directory`, the LiDAR USB cable is not connected or the CP2102 USB-UART chip isn't recognized. Unplug and replug the USB cable.

### 1.3 — Start the sensor Docker container

```bash
bash /home/arduino/start_rplidar.sh
```

This script does the following in sequence:
1. Sets USB permissions: `chmod a+rw /dev/ttyUSB0`
2. Removes any stale container named `rplidar`
3. Starts a new `rplidar` Docker container with:
   - `--net=host` (shares the Uno Q's network namespace for ROS 2 DDS)
   - `--privileged` (needed for USB device access)
   - Volume mounts for the ROS workspace and USB device
4. Launches `rplidar_ros` ROS 2 driver and `imu_publisher.py` inside the container

### 1.4 — Verify the container is healthy

```bash
sudo docker logs -f rplidar
```

You should see output similar to:
```
[INFO] [rplidar_node]: RPLIDAR running on /dev/ttyUSB0
[INFO] [rplidar_node]: Lidar health status: Good, (0)
[INFO] [imu_publisher]: Publishing /imu/data @ 100 Hz
[INFO] [imu_publisher]: BNO086 quaternion: w=0.998 x=0.001 y=0.004 z=-0.012
```

Press `Ctrl+C` to exit the log view (the container keeps running in background).

### 1.5 — Exit the Uno Q SSH session

```bash
exit
```

---

## Part 2: Start the Dashboard on the Laptop

The dashboard is your single control point for everything — sensors, SLAM, maps, RViz2, and emergency shutdown. You only need to do this once per session.

### 2.1 — Option A: From inside the DevContainer

If your terminal is already inside the `thirsty_burnell` DevContainer:

```bash
cd /home/ros/my_robot_ws
python3 src/my_robot_dashboard/app.py
```

### 2.2 — Option B: From the host machine (outside Docker)

```bash
cd ~/my_robot_ws
./start_dashboard.sh
```

`start_dashboard.sh` automatically:
- Detects whether `ros2` is available on the host or inside a Docker container
- Kills any previous instance using the PID lockfile at `/tmp/my_robot_dashboard.pid`
- Exports all required environment variables (`ROS_DOMAIN_ID=42`, `RMW_IMPLEMENTATION`, `CYCLONEDDS_URI`)
- Launches `app.py` in the correct context

### 2.3 — Confirm the dashboard started

You should see in the terminal:
```
=========================================================
  STARTING DISTRIBUTED ROS 2 ROBOT CONTROL HUB
  Web UI: http://localhost:5050
=========================================================
 * Serving Flask app 'app'
 * Running on http://0.0.0.0:5050
```

### 2.4 — Open the Web UI in your browser

Open **Google Chrome, Firefox, or any modern browser** and go to:
```
http://localhost:5050
```

> If the page doesn't load, make sure port 5050 isn't blocked by a firewall:  
> `sudo ufw allow 5050` or check `curl -v http://localhost:5050`

---

## Part 3: Verify Sensors Are Working

Before starting SLAM, confirm that both sensors are delivering data. You can do this from:
- The Web UI telemetry panel (shows live IMU quaternion + scan rate)
- OR the terminal

### 3.1 — From the terminal (inside DevContainer)

Open a **new terminal tab** inside the DevContainer and run:

```bash
# Source the environment
source /opt/ros/jazzy/setup.bash
source /home/ros/my_robot_ws/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml

# Check LiDAR is publishing (should show ~10.0 Hz)
ros2 topic hz /scan

# Check IMU is publishing (should show ~100.0 Hz)
ros2 topic hz /imu/data
```

**Healthy output example:**
```
average rate: 10.003
        min: 0.097s max: 0.103s std dev: 0.00183s window: 10

average rate: 100.039
        min: 0.0098s max: 0.0102s std dev: 0.00012s window: 100
```

### 3.2 — From the Web UI

The dashboard's telemetry panel displays:
- **IMU Status**: quaternion W/X/Y/Z, roll, pitch, yaw in degrees
- **Scan Rate**: Hz reading from `/scan` topic
- **TF Status**: whether `odom → base_link` transform is being broadcast

If either sensor shows "No Data" or "0 Hz", go back to Part 1 and restart the Uno Q container.

---

## Part 4: Start SLAM and Map Your Space

### 4.1 — Click "Start SLAM" in the Web UI

This single button does the following in sequence:
1. Launches `qos_relay.py` — the 50 Hz TF bridge (publishes `map → odom → base_link → laser`) and tilt-aware scan filter
2. Waits 1 second for TF to stabilize
3. Launches `slam_toolbox` in async mapping mode
4. Waits 3.5 seconds for the lifecycle node to configure and activate
5. Opens **RViz2** with the appropriate display config

Wait for the Web UI to show: **"SLAM active — ready to map"**

You can also start via CLI:
```bash
curl -X POST http://localhost:5050/api/slam/start \
  -H "Content-Type: application/json" -d '{}'
```

### 4.2 — Set up RViz2 for visualization

Once RViz2 opens, configure it to show the map:
1. In the **"Displays"** panel (left side), click **"Add"**
2. Select **"By Topic"** tab
3. Find `/map` → click **"Map"** → click **"OK"**
4. Set **"Fixed Frame"** (top of Displays panel) to: `map`
5. (Optional) Add `/scan_reliable` → **LaserScan** to see live laser dots
6. (Optional) Add **TF** to see the coordinate frame tree

You should now see a small grey area around the robot's starting position. This will grow as you walk.

### 4.3 — Walk and map

Pick up the complete Uno Q assembly (board + LiDAR + power bank) and walk slowly through your space.

**Best practices for clean maps:**
- **Walk slowly** — 0.5–1 m/s maximum. Faster motion causes scan matcher drift.
- **Pause at corners** — give SLAM time to register the new geometry before turning
- **Revisit areas** — walking back through a corridor or doorway triggers loop closure, which stitches previously separate map sections together accurately
- **Keep it level** — the IMU tilt gating filters rays when tilt > 7.5°, but severe tilts still reduce map quality
- **Map whole rooms** — walk around the perimeter of each room, not just through the middle
- **Avoid glass and mirrors** — LiDAR reflections cause phantom walls

**Indicator of healthy SLAM in RViz2:**
- The map grows smoothly as you move
- The robot's pose marker (red arrow / axes) tracks your real position
- No sudden large jumps in position

### 4.4 — Return to start position

When you're done mapping, walk back near your starting position and pause for a moment. This gives SLAM a chance to close the final loop and align the map.

---

## Part 5: Save the Map

### 5.1 — Click "Save Map" in the Web UI

This calls the map saver and writes two files:
- `src/my_robot_nav/maps/<timestamp>_map.pgm` — the pixel image of the map
- `src/my_robot_nav/maps/<timestamp>_map.yaml` — metadata (resolution, origin, threshold)

You can also trigger via CLI:
```bash
# Save with auto-generated timestamp filename
curl -X POST http://localhost:5050/api/slam/save_map \
  -H "Content-Type: application/json" -d '{}'

# Save with a custom filename
curl -X POST http://localhost:5050/api/slam/save_map \
  -H "Content-Type: application/json" \
  -d '{"filename": "living_room_2026"}'
```

### 5.2 — Verify the map was saved

```bash
ls -la /home/ros/my_robot_ws/src/my_robot_nav/maps/
# You should see your newly created .pgm and .yaml files
```

### 5.3 — View the saved map image

```bash
# View the raw map image (from DevContainer terminal)
eog src/my_robot_nav/maps/*.pgm
# OR
display src/my_robot_nav/maps/*.pgm
```

---

## Part 6: Regularize the Map (Snap to 90° Boxy Walls)

Raw SLAM maps look fuzzy and jagged because the laser scanner accumulates small errors. The **Map Regularizer** post-processes the map to produce clean, architectural 90° walls — like a CAD floorplan.

### 6.1 — Click "Snap to 90° Boxy Walls" in the Web UI

This runs `map_regularizer.py` which:
1. Loads the most recently saved map
2. Thresholds the occupancy grid into binary wall/free pixels
3. Applies morphological gap-closing to connect wall segments
4. Runs Probabilistic Hough Line Transform to detect wall segments
5. Computes the dominant building orientation angle (θ_dom) via weighted histogram
6. Snaps ALL wall segments to orthogonal Manhattan axes (θ_dom, θ_dom+90°, etc.)
7. Saves three output files:
   - `<map>_regularized.pgm` — regularized raster map
   - `<map>_regularized.yaml` — metadata (same resolution/origin as original)
   - `<map>_regularized.svg` — clean vector CAD export (importable in any vector editor)

Via CLI:
```bash
curl -X POST http://localhost:5050/api/slam/regularize_map \
  -H "Content-Type: application/json" -d '{}'
```

### 6.2 — Compare the before and after maps

```bash
# View original
display src/my_robot_nav/maps/my_map.pgm

# View regularized
display src/my_robot_nav/maps/my_map_regularized.pgm
```

The regularized map will show clean rectangular rooms instead of fuzzy blobs.

---

### 7.1 — CLI Operational Helper Scripts

| Situation | Command | What it does |
|---|---|---|
| **Normal Launch** | `./start_dashboard.sh` | Cleans previous instances, sets CycloneDDS env, launches Dashboard at http://localhost:5050 |
| **Clean Restart** | `./restart_dashboard.sh` | Invokes `./stop_dashboard.sh`, waits 1.5s, then re-runs `./start_dashboard.sh` |
| **SLAM frozen / Reset** | `./kill_all_ros.sh` | Soft reset: kills SLAM, `qos_relay`, and RViz2 while keeping Web UI alive |
| **Full Emergency Teardown** | `./stop_dashboard.sh` | Forcefully terminates all dashboard, relay, SLAM, and visualizer nodes on host and in DevContainer |
| **Nuclear CLI Option** | `kill -9 $(lsof -ti:5050 2>/dev/null) && docker exec -t thirsty_burnell rm -f /tmp/my_robot_dashboard.pid` | Clears any external lock or stubborn socket binding |

### 7.2 — Soft reset (keep dashboard running, restart ROS nodes)

Use this if something goes wrong with SLAM or sensors and you want a clean restart:

**Via Web UI:** Click **"Reset Nodes"** button  
**Via CLI:** `./kill_all_ros.sh` or:
```bash
curl -X POST http://localhost:5050/api/system/kill_all \
  -H "Content-Type: application/json" -d '{}'
```

This kills all ROS 2 processes (`slam_toolbox`, `qos_relay`, RViz2) but leaves the Flask dashboard running at port 5050.

### 7.3 — Full shutdown (everything off)

**Via Web UI:** Click **"Shutdown All & Exit"** button  
**Via CLI:** `./stop_dashboard.sh` or:
```bash
curl -X POST http://localhost:5050/api/system/shutdown_all \
  -H "Content-Type: application/json" -d '{}'
```

This kills all ROS nodes AND exits the Flask app. Port 5050 is released.

### 7.4 — Stop the Uno Q container


SSH back into the Uno Q and stop the sensor container:
```bash
ssh arduino@192.168.1.17
sudo docker stop rplidar
exit
```

---

## Manual CLI Verification Reference

Use these commands inside the DevContainer to probe the system state at any time:

```bash
# Source environment (required in each new terminal session)
source /opt/ros/jazzy/setup.bash
source /home/ros/my_robot_ws/install/setup.bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml

# ─── TOPIC HEALTH CHECKS ────────────────────────────────────────────────

# List all visible ROS 2 topics
ros2 topic list

# Check LiDAR scan rate (should be ~10 Hz)
ros2 topic hz /scan

# Check IMU rate (should be ~100 Hz)
ros2 topic hz /imu/data

# Check qos_relay's re-published scan (should be ~10 Hz after SLAM starts)
ros2 topic hz /scan_reliable

# ─── VIEW ACTUAL DATA ───────────────────────────────────────────────────

# Print one laser scan message (shows ranges[], angle_min, angle_max, etc.)
ros2 topic echo /scan --once

# Print one IMU message (shows quaternion, angular_velocity, linear_acceleration)
ros2 topic echo /imu/data --once

# ─── TF TREE VERIFICATION ────────────────────────────────────────────────

# Print the current TF tree structure (after SLAM starts)
ros2 run tf2_tools view_frames
# Opens a PDF: frames_YYYYMMDD_HHMMSS.pdf — should show map→odom→base_link→laser

# Echo a live transform (map → base_link, i.e. robot's global pose)
ros2 run tf2_ros tf2_echo map base_link

# Echo the odometry transform (odom → base_link, published by qos_relay at 50 Hz)
ros2 run tf2_ros tf2_echo odom base_link

# ─── NODE INSPECTION ────────────────────────────────────────────────────

# List all running ROS 2 nodes
ros2 node list

# Inspect a specific node's parameters
ros2 param list /sync_slam_toolbox_node

# ─── SLAM STATUS ────────────────────────────────────────────────────────

# Check if SLAM map is being published
ros2 topic hz /map

# ─── PROCESS CHECKS (on the host or inside container) ───────────────────

# Check for running ROS/dashboard processes
ps aux | grep -E "app.py|qos_relay|slam_toolbox|rviz2" | grep -v grep

# Check what's listening on port 5050
lsof -i :5050

# Check Uno Q Docker container status
ssh arduino@192.168.1.17 "sudo docker ps"
```

---

## Troubleshooting

| Problem | What you see | Step-by-step fix |
|---------|-------------|-----------------|
| **No `/scan` data** | `ros2 topic hz /scan` shows no output or 0 Hz | 1. SSH to Uno Q: `ssh arduino@192.168.1.17` 2. Check container: `sudo docker ps` (should show `rplidar`) 3. If not running: `bash /home/arduino/start_rplidar.sh` 4. Check USB: `ls /dev/ttyUSB*` — must exist |
| **No `/imu/data` data** | IMU shows 0 Hz or "No Data" in dashboard | 1. Check arduino-router service: `sudo systemctl status arduino-router` on Uno Q 2. Check IMU wiring (A4=SDA, A5=SCL, 3.3V, D2=INT) 3. Verify firmware uploaded: open Serial Monitor at 115200 baud — must see `imu/raw,...` lines 4. Restart container: `sudo docker restart rplidar` |
| **Map not appearing in RViz2** | RViz2 opens, viewport is empty | 1. Set "Fixed Frame" to `map` (not `odom` or `laser`) 2. Wait 5–7 seconds for slam_toolbox to fully activate 3. Click Add → By Topic → `/map` → Map 4. Verify `/scan` is flowing: `ros2 topic hz /scan` |
| **Map overlaps when returning to a room** | Rooms appear twice, map splits | This is loop closure failing. Fix: 1. Walk back more slowly through doorways 2. Pause 2–3 seconds at known landmarks 3. Check `loop_search_maximum_distance: 12.0` in `slam_toolbox_params.yaml` — if your space is larger, increase it |
| **`400 Bad Request` from Web UI buttons** | Toast notification: "400 Bad Request" | Check the `app.py` log in the terminal. All routes use `request.get_json(silent=True) or {}` so this should not happen. If it does, restart the dashboard: `curl -X POST http://localhost:5050/api/system/shutdown_all` then `./start_dashboard.sh` |
| **`JSON.parse: unexpected character` error** | Toast shows SyntaxError | Browser is loading a cached version of `app.js`. Fix: hard-refresh the browser with **Ctrl+Shift+R** (or Cmd+Shift+R on Mac) |
| **Port 5050 already in use** | `Address already in use` error on dashboard start | `./start_dashboard.sh` handles this automatically via PID lockfile. If it fails: `kill -9 $(lsof -ti:5050)` then try again |
| **Zombie ROS processes from previous session** | Old slam_toolbox or qos_relay still running | From Web UI: "Reset Nodes". From CLI: `curl -X POST http://localhost:5050/api/system/kill_all -H "Content-Type: application/json" -d '{}'` |
| **LiDAR motor not spinning** | Container runs but `/scan` is empty, no ranges | On Uno Q: 1. `sudo chmod a+rw /dev/ttyUSB0` 2. `sudo docker restart rplidar` 3. Check the USB cable (try a different cable — power-only cables won't work) |
| **IMU tilt gating — sparse map** | Lots of `inf` values in scan, map looks patchy | This is **correct behavior** — you are tilting the device more than 7.5°. Hold it level. The filter removes rays that would hit floors/ceilings. Threshold and height cutoff tunable in `qos_relay.py` |
| **CycloneDDS peer discovery fails** | Topics don't appear across Wi-Fi | 1. Verify both on same LAN: `ping 192.168.1.17` from laptop 2. Check `cyclonedds.xml` has correct peer IP 3. Check Wi-Fi interface name matches: `ip link show \| grep "^[0-9]: w"` 4. Ensure Uno Q container uses `--net=host` 5. Restart both sides: stop container, restart dashboard |
| **RViz2 crashes on launch (Qt errors)** | `qt.qpa.xcb: could not connect to display` | On HOST machine: `xhost +local:root` then restart dashboard |
| **Snap to Boxy Walls does nothing** | Button click, no new files appear | The regularizer needs a saved map first. Click "Save Map" before "Snap to 90° Boxy Walls". Check terminal for `cv2` / `numpy` import errors — install with `pip3 install opencv-python-headless numpy` inside the container |
| **Dashboard doesn't show live telemetry** | Telemetry panel shows stale or zero values | The SSE stream at `/api/stream` may have disconnected. Refresh the page. Check that `qos_relay.py` is running: `ps aux \| grep qos_relay` |
