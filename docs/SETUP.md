# Setup Guide: Environment & Build Instructions

---

## ⭐ Current System Setup (Production Hardware Mode)

This section documents the **live, production-ready setup** for running the full distributed robot stack on real hardware.

> For simulation or legacy development setup, see the [Development & Simulation Setup (Legacy)](#development--simulation-setup-legacy) section below.

---

### 1. Hardware Prerequisites

| Component | Specification |
|-----------|--------------|
| **Edge SBC** | Arduino Uno Q at `192.168.1.17` (Wi-Fi configured, SSH enabled) |
| **Lidar** | RPLidar C1 — USB at `/dev/ttyUSB0` @ 460800 baud |
| **IMU** | 7Semi BNO086 (ES-12243) — I2C `Wire2`, A4=SDA, A5=SCL, D2=INT, addr `0x4B`, VCC=3.3V |
| **Laptop** | x86_64 Ubuntu, Docker Engine, VS Code with Dev Containers extension |
| **Network** | Both devices on same Wi-Fi subnet (Uno Q: `192.168.1.17`, Laptop: `192.168.1.15`) |

---

### 2. Clone the Repository

```bash
git clone https://github.com/akash-adhikary/distributed-ros2-robot.git my_robot_ws
cd my_robot_ws
```

---

### 3. Open in VS Code Dev Containers

```bash
code .
```

When prompted **"Reopen in Container"**, click it.  
*(Or press `F1` → `Dev Containers: Reopen in Container`.)*

The DevContainer (`thirsty_burnell`) provides:
- **ROS 2 Jazzy** pre-installed with `slam_toolbox`, `rmw_cyclonedds_cpp`, and all Python dependencies.
- GUI passthrough for RViz2.
- The workspace mounted at `/home/ros/my_robot_ws`.

---

### 4. Build the Workspace

Inside the DevContainer integrated terminal:

```bash
colcon build --symlink-install
source install/setup.bash
```

> `--symlink-install` avoids redundant file copies and is required for the dashboard's Python scripts to hot-reload during development.

---

### 5. Uno Q Edge Node Setup

#### 5a. Flash the BNO086 Firmware (One-Time)

Open `uno_q_firmware/BnoTest.ino` in Arduino IDE:
- Board: **Arduino Uno Q**
- Programmer: Standard USB
- Upload to the Uno Q.

The firmware initializes `Wire2` (A4/A5) at I2C address `0x4B` and streams quaternion + accelerometer + gyroscope data to `arduino-router` IPC at `/var/run/arduino-router.sock` as an atomic comma-separated payload on the `imu/raw` channel @ 100 Hz.

#### 5b. Deploy the RPLidar Docker Container

SSH into the Uno Q:

```bash
ssh arduino@192.168.1.17
```

Start the pre-built Docker container (which runs both `rplidar_node` and `imu_publisher.py`):

```bash
docker start rplidar
```

If starting for the first time, the full run command is:
```bash
docker run -d \
  --name rplidar \
  --privileged \
  --net=host \
  --restart=unless-stopped \
  -e ROS_DOMAIN_ID=42 \
  -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  -e CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml \
  -v /var/run/arduino-router.sock:/var/run/arduino-router.sock \
  -v /home/arduino/my_robot_ws/cyclonedds.xml:/home/ros/my_robot_ws/cyclonedds.xml:ro \
  --device=/dev/ttyUSB0 \
  my_robot_rplidar:jazzy
```

Inside the container, two processes run:
- **`rplidar_node`** — publishes `/scan` @ 10 Hz from `/dev/ttyUSB0` @ 460800 baud.
- **`imu_publisher.py`** — reads the `imu/raw` msgpack IPC from `arduino-router.sock` and publishes `/imu/data` @ 100 Hz.

Verify:
```bash
docker exec -t rplidar bash -c "
  source /opt/ros/jazzy/setup.bash && \
  export ROS_DOMAIN_ID=42 && \
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && \
  export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml && \
  ros2 topic hz /scan && ros2 topic hz /imu/data
"
```

Exit SSH:
```bash
exit
```

---

### 6. CycloneDDS Configuration

The file [`cyclonedds.xml`](../cyclonedds.xml) in the workspace root configures static unicast peer discovery between the two machines:

```xml
<!-- cyclonedds.xml (excerpt) -->
<CycloneDDS>
  <Domain>
    <General>
      <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>
    </General>
    <Discovery>
      <Peers>
        <Peer address="192.168.1.15"/>  <!-- Laptop -->
        <Peer address="192.168.1.17"/>  <!-- Uno Q  -->
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

Both machines must export these environment variables (already handled by `start_dashboard.sh` and the Docker container):

```bash
export ROS_DOMAIN_ID=42
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
```

---

### 7. Launch the Full Stack

```bash
cd ~/my_robot_ws
./start_dashboard.sh
```

Then open **http://localhost:5050** in your browser.

Click **▶ Start SLAM** to begin mapping.

See [USAGE_GUIDE.md](USAGE_GUIDE.md) for the complete operational workflow.

---
---

## Development & Simulation Setup (Legacy)

The following sections document the original development and simulation environment. These steps remain valid for development without the Uno Q hardware.

---

### Option 1: VS Code Dev Containers / Docker (Fully Reproducible)

#### Prerequisites:
- Docker Engine & Docker Compose installed.
- VS Code with the **Dev Containers** (`ms-vscode-remote.remote-containers`) extension.

#### Quickstart:
1. Open this workspace directory in VS Code:
   ```bash
   code /path/to/my_robot_ws
   ```
2. When prompted with **"Reopen in Container"**, click it.
   *(Or press `F1` / `Ctrl+Shift+P`, type `Dev Containers: Reopen in Container`, and press Enter).*
3. The DevContainer will build the pinned **ROS 2 Jazzy + Gazebo Harmonic + Nav2** image, configure GUI pass-through for simulation, and run `scripts/install_deps.sh`.
4. Open the integrated terminal and compile the workspace:
   ```bash
   cbuild
   ```

#### Plain Docker Build (CLI Alternative):
If you want to build and run the container purely from the terminal without VS Code:
```bash
# Build the Docker image
docker build -t my_robot_ws:jazzy -f .devcontainer/Dockerfile .

# Run container with X11 GUI forwarding
xhost +local:root
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

### Option 2: Native Ubuntu Setup

If developing directly on the host machine:

#### 1. Add ROS 2 Repositories
```bash
sudo apt update && sudo apt install -y locales curl gnupg2 lsb-release software-properties-common
sudo add-apt-repository -y universe

sudo install -m 0755 -d /etc/apt/keyrings
curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo tee /etc/apt/keyrings/ros-archive-keyring.gpg > /dev/null
sudo chmod 644 /etc/apt/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

#### 2. Install Core Stacks & Build Tools
```bash
sudo apt update
sudo apt install -y \
    ros-${ROS_DISTRO}-desktop \
    ros-${ROS_DISTRO}-ros-gz \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool
```

#### 3. Install Workspace Dependencies
Run the idempotent dependency installer:
```bash
bash scripts/install_deps.sh
```

---

### Building and Sourcing the Workspace

Inside the workspace root (`my_robot_ws`):

```bash
# Build all packages with symlink-install (saves disk space on 90GB SSD)
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release --parallel-workers 4

# Source the local overlay
source install/setup.bash
```

---

### Deploying to Uno Q Edge Hardware (Legacy Script)

```bash
# Test deployment dry run
bash scripts/deploy_to_uno_q.sh uno-q.local debian /home/debian/robot_deploy --dry-run

# Live deployment
bash scripts/deploy_to_uno_q.sh uno-q.local debian /home/debian/robot_deploy
```
