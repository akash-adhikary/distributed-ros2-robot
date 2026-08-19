# 🤖 Robot Simulation Workflow Guide

Quick reference for launching, driving, mapping, and navigating your differential-drive robot in Gazebo + Nav2.

---

## Prerequisites

- VS Code is open with the Dev Container active
- Bottom-left corner of VS Code shows: `Dev Container: ROS 2 Jazzy Robotics DevContainer`
- Open integrated terminal: `Ctrl + ~`
- **If you recently restarted your laptop**: You must grant display access to the container. Open a terminal on your **host machine** (outside VS Code) and run:
  ```bash
  xhost +local:root
  ```

---

## ⚡ Automation Scripts (Fast Track)

For both **Human Developers** and **AI Coding Agents**, we provide automated helper scripts to easily spin up, control, and clean up simulation pipelines:

### 1. Start Simulation
* **Human (GUI Mode)**: Opens Gazebo and RViz2 on your host screen.
  ```bash
  ./scripts/start_sim.sh
  ```
* **AI Agent (Headless Mode)**: Runs simulation server-only in the background (no OpenGL dependencies).
  ```bash
  ./scripts/start_sim.sh --headless
  ```

### 2. SLAM Mapping
* Launches the SLAM mapping node.
  ```bash
  ./scripts/start_slam.sh
  ```

### 3. Keyboard Driving (Teleop)
* Launches the keyboard teleop terminal tab to manually drive the robot and explore.
  ```bash
  ./scripts/drive_teleop.sh
  ```

### 4. Save Map
* Triggers SLAM Toolbox to save the mapped arena to the correct paths.
  ```bash
  ./scripts/save_map.sh
  ```

### 4. Autonomous Navigation (Nav2)
* Boots the Nav2 stack, map server, and AMCL localization.
  ```bash
  ./scripts/start_nav.sh
  ```

### 5. Stop/Reset Everything
* Forcefully terminates all background ROS 2 and Gazebo sessions to clean the workspace.
  ```bash
  ./scripts/stop_all.sh
  ```

---

## Step 1 — Build & Source (do this once per session)

```bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --parallel-workers 4
source install/setup.bash
```

> [!TIP]
> After the first build, if you only change YAML/launch files (not C++), you can skip `colcon build` and just `source install/setup.bash`.

---

## Step 2 — Launch Gazebo Simulation + RViz2

**Terminal 1:**
```bash
ros2 launch my_robot_bringup sim_robot.launch.py
```
```bash
ros2 launch my_robot_bringup sim_robot.launch.py headless:=false
```

**What opens:**
- Gazebo Sim → 6×6 m walled arena with pillars and boxes
- Your diff-drive robot spawned at origin
- RViz2 → shows Robot Model, laser scan rays, TF frames, and odometry arrow

**Wait until you see this in the terminal:**
```text
[robot_state_publisher] Robot initialized
[create-3] Entity creation successful.
```

---

## Step 3 — Launch SLAM Toolbox (Live Mapping)

Open a **new terminal tab** (`Ctrl + Shift + 5` or click `+` in VS Code terminal):

**Terminal 2:**
```bash
source install/setup.bash
ros2 launch my_robot_nav slam.launch.py
```

**Wait until you see:**
```text
[slam_toolbox]: Node using stack size 40000000
```

---

## Step 4 — Drive the Robot with Keyboard

Open another **new terminal tab**:

**Terminal 3:**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Key bindings** (click this terminal first so keypresses register):

| Key | Action |
|:---:|:---|
| `i` | Move forward |
| `,` | Move backward |
| `j` | Rotate left (counter-clockwise) |
| `l` | Rotate right (clockwise) |
| `k` | **Stop immediately** |
| `u` | Forward + left arc |
| `o` | Forward + right arc |
| `q` / `z` | Increase / decrease speed |

> [!NOTE]
> Drive slowly around the arena, covering all corners. Watch the **grey occupancy grid** building in RViz2 as you explore.

---

## Step 5 — Confirm Map is Being Generated

In any terminal tab, verify `/map` is being published:

```bash
ros2 topic list | grep map
```

**Expected output:**
```text
/map
/map_metadata
```

> [!IMPORTANT]
> If `/map` does not appear — keep driving the robot. SLAM Toolbox only activates after receiving laser scan data from a moving robot. Drive for at least 10 seconds.

---

## Step 6 — Save the Map

Once you've explored enough of the arena, save the map.

**Option A — SLAM Toolbox Service (Recommended):**
```bash
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap \
  "{name: {data: '/home/ros/my_robot_ws/src/my_robot_nav/maps/my_map'}}"
```

**Option B — Nav2 Map Saver (after `/map` is confirmed in topic list):**
```bash
ros2 run nav2_map_server map_saver_cli \
  -f /home/ros/my_robot_ws/src/my_robot_nav/maps/my_map \
  --ros-args -p map_subscribe_transient_local:=true
```

> [!IMPORTANT]
> Always use **absolute paths** (starting with `/home/ros/...`), not relative paths like `src/...`.

**Verify the saved files:**
```bash
ls -la src/my_robot_nav/maps/
```

You should see:
```text
my_map.yaml        ← map metadata (resolution, origin)
my_map.pgm         ← occupancy grid image (open with any image viewer)
my_map.posegraph   ← SLAM pose graph (for resuming mapping later)
my_map.data        ← pose graph data
```

---

## Step 7 — Autonomous Navigation with Nav2

Once you have a saved map, launch Nav2 for autonomous point-to-point navigation.

> [!NOTE]
> Stop the SLAM Toolbox first (`Ctrl + C` in Terminal 2) before launching Nav2 navigation. They should not run simultaneously.

**Terminal 2 (after stopping SLAM):**
```bash
ros2 launch my_robot_nav navigation.launch.py
```

**In RViz2:**
1. Click the **"2D Pose Estimate"** button (top toolbar) → Click on the map where the robot currently is to initialize localization.
2. Click the **"2D Goal Pose"** button → Click anywhere on the map to send a navigation goal.
3. Watch the robot plan a path and autonomously drive there while avoiding obstacles!

---

## Deployment to Arduino UNO Q (Physical Robot)

When you are ready to deploy to the real robot over Wi-Fi:

```bash
bash scripts/deploy_to_uno_q.sh uno-q.local debian /home/debian/robot_deploy
```

Dry run (no files transferred, just preview):
```bash
bash scripts/deploy_to_uno_q.sh uno-q.local debian /home/debian/robot_deploy --dry-run
```

---

## Cleaning Up Active Sessions (Resetting the Environment)

If the simulation gets stuck, graphics freeze, or you want to restart clean, you can forcefully kill all background Gazebo and ROS 2 sessions with a single command in any container terminal:

```bash
pkill -9 -f 'ros2|gz|rviz|slam'
```

This instantly terminates:
- **Gazebo Sim** (`gz-sim` / `ruby`)
- **RViz2** (`rviz2`)
- **ROS 2 nodes** (bridges, publishers, teleop)
- **SLAM nodes** (`slam_toolbox`)

---

## Troubleshooting Quick Reference

| Problem | Cause | Fix |
|:---|:---|:---|
| `/map` not in `ros2 topic list` | Robot hasn't moved, SLAM not yet active | Drive with teleop for 10+ seconds |
| `map_saver_cli` fails with "Failed to spin" | `/map` not yet published | Use SLAM Toolbox service (Option A) with **absolute path** |
| Service "waiting for service to become available" | SLAM not initialized yet | Drive robot first, then retry |
| SLAM runs but never generates a map | `frame_id` mismatch — old sensor name `lidar` ≠ TF link `laser_frame` | **Fixed in code**: sensor renamed to `laser_frame` in `lidar.xacro` |
| Gazebo opens but robot not visible | Robot spawn race condition (world not ready) | **Fixed**: spawn delayed 3s after world load |
| RViz2 shows no laser scan | Bridge not started yet or frame_id wrong | Verify: `ros2 topic echo /scan --once \| grep frame_id` must equal `laser_frame` |
| Teleop keys not working | Wrong terminal focused | Click on the teleop terminal window first |
| `/odom` TF frame missing | Diff-drive plugin not active | Bridge starts 5s after spawn — wait for it before checking |

---

## Summary: Correct Launch Order

```
1. sim_robot.launch.py      → Gazebo + RViz2 + Bridge
2. slam.launch.py           → SLAM Toolbox
3. teleop_twist_keyboard    → Drive the robot
4. (drive until /map appears)
5. Save map via service call
6. (Stop SLAM)
7. navigation.launch.py     → Autonomous Nav2
```
