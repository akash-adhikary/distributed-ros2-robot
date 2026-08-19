# 🚀 Edge Deployment Guide (Arduino Uno Q)

This guide documents the exact steps required to deploy the ROS 2 node stack on the Arduino Uno Q (or any lightweight Debian/Ubuntu ARM64 edge SBC) using Docker. 

This approach ensures a **lightweight, reproducible, and production-grade** setup without polluting the host OS with ROS 2 dependencies.

---

## 📋 Prerequisites
1. **Host OS:** Debian or Ubuntu (aarch64/arm64)
2. **Storage:** An external USB Pendrive mounted (e.g., at `/home/arduino/pendrive`) to save eMMC wear and tear.
3. **Software:** Docker installed (`curl -fsSL https://get.docker.com | sh`).
4. **Hardware:** RPLIDAR C1 connected via USB-A to USB-C cable.

> **⚠️ USB Hub Power Quirk:** If using a Type-C PD hub, the Uno Q acts as a power `[sink]`. Some hubs will disable their USB-A ports unless the host acts as a `[source]`. **Solution:** Power the Uno Q via its dedicated 12V DC barrel jack so the Type-C port becomes a power source, instantly waking up the USB-A ports.

---

## 🛠️ Step 1: Workspace Preparation

We keep all ROS 2 code and build artifacts entirely on the pendrive.

```bash
# 1. Create the workspace source directory
mkdir -p /home/arduino/pendrive/ros_ws/src

# 2. Clone the Slamtec ROS 2 driver (ros2 branch is required for C1 baudrate support)
cd /home/arduino/pendrive/ros_ws/src
git clone -b ros2 https://github.com/Slamtec/rplidar_ros.git
```

---

## 🐳 Step 2: Custom Docker Environment

We build a custom Docker image based on `ros:humble-ros-base`. We add `colcon` for building and `CycloneDDS` for reliable multi-machine networking over Wi-Fi.

Create `/home/arduino/pendrive/ros_ws/Dockerfile`:
```dockerfile
FROM ros:humble-ros-base

# Install build tools and CycloneDDS for networking
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    ros-humble-rmw-cyclonedds-cpp \
    && rm -rf /var/lib/apt/lists/*

# Set standard networking environment variables
ENV ROS_DOMAIN_ID=42
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Build the image locally on the Uno Q (this takes ~3-5 minutes):
```bash
cd /home/arduino/pendrive/ros_ws
sudo docker build -t uno_ros_base .
```

---

## 🔨 Step 3: Compiling the Code

Instead of installing ROS 2 build tools on the Uno Q host OS, we use a temporary Docker container to compile the workspace. The build artifacts (`build/`, `install/`, `log/`) are saved directly to the pendrive via volume mapping.

```bash
sudo docker run --rm \
  -v /home/arduino/pendrive/ros_ws:/ws \
  uno_ros_base \
  bash -c "source /opt/ros/humble/setup.bash && cd /ws && colcon build"
```
*(Note: Compiling C++ nodes on 2GB RAM takes a few minutes. Wait for completion.)*

---

## 🚀 Step 4: Launching the Edge Node

The RPLIDAR C1 has a strict startup timeout. We use a lightweight Python script (`spin_test.py`) using `pyserial` to pre-spin the motor *before* ROS takes over.

### The Startup Script (`/home/arduino/start_rplidar.sh`)

Create this script to automate the entire hardware launch:

```bash
#!/bin/bash
echo "Setting USB permissions..."
sudo chmod a+rw /dev/ttyUSB0

echo "Spinning up motor (bypassing strict Slamtec timeout)..."
# Runs a quick python script to send \xA5\x20 to 460800 baud
python3 /home/arduino/spin_test.py

echo "Killing any old docker containers..."
sudo docker rm -f rplidar >/dev/null 2>&1

echo "Starting RPLIDAR ROS 2 Node in Docker..."
sudo docker run -d \
  --name rplidar \
  --net=host \
  --privileged \
  -v /home/arduino/pendrive/ros_ws:/ws \
  -v /dev/ttyUSB0:/dev/ttyUSB0 \
  uno_ros_base \
  bash -c "source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && ros2 launch rplidar_ros rplidar_c1_launch.py"

echo "Node running in background! Check logs with: sudo docker logs -f rplidar"
```

### Networking Checklist
To ensure the laptop receives the `/scan` topic from the Uno Q:
1. Both devices must be on the same Wi-Fi LAN.
2. Laptop must have `export ROS_DOMAIN_ID=42` and `export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` in its `~/.bashrc`.
3. The Docker container on Uno Q must be launched with `--net=host` (done in the script above).

---
*Document designed for automated AI Agent reproduction and GitHub documentation.*
