# Distributed ROS 2 Robot Architecture

This document serves as the permanent memory and source of truth for the robot's architecture, configurations, and fixes.

## 1. Hardware Architecture
*   **Host (Laptop):** Lenovo ThinkPad T470 (x86_64, Ubuntu)
    *   **Role:** Main compute node, SLAM algorithm (slam_toolbox), Navigation (Nav2), and Visualization (RViz2).
*   **Edge Compute:** Arduino Uno Q (ARM64, Debian)
    *   **Role:** Hardware interface node. Directly powers and reads from the RPLidar and BNO08x IMU.
    *   **Storage Mod:** The internal 9.8GB SD card is protected. Docker is configured to run off a 113GB ext4 partition on an attached USB Pendrive (`/home/arduino/pendrive/docker`), ensuring high read/write endurance and ample space.

## 2. Software & Container Architecture
*   **ROS Version:** ROS 2 (Jazzy on Laptop, Humble in Uno Q Docker).
*   **Containerization:**
    *   Laptop uses VS Code Dev Containers (`thirsty_burnell` container) with GUI/X11 forwarding for RViz.
    *   Uno Q runs a headless `ros:humble-ros-base` container (named `rplidar`) mounted to `/home/arduino/pendrive/ros_ws`.
*   **DDS Middleware:** Eclipse CycloneDDS (`rmw_cyclonedds_cpp`).

## 3. Major Fixes and Debugging Log
*   **Network Dropouts:** Initially, CycloneDDS was trying to use virtual Docker network interfaces, causing ROS topics to randomly vanish.
    *   *Fix:* Enforced a custom `cyclonedds.xml` on both devices strictly locking traffic to the WiFi interface (`wlan0` / `wlp4s0`) and enabling `AllowMulticast`.
*   **Timestamp Desync (TF Extrapolation Errors):** The Laptop and Uno Q clocks drifted, causing the SLAM Toolbox to drop Lidar scans because they were stamped "in the past" or "in the future".
    *   *Fix:* Wrote a custom `qos_relay.py` node that intercepts `/scan` and `/imu/data_raw`, overrides their message headers with the Laptop's synchronized local time, and republishes them as `/scan_synced` and `/imu/data_raw_synced`.
*   **RViz GLSL Shader Crash:** RViz crashed on the laptop due to an Intel Mesa driver bug with `indexed_8bit_image` parsing.
    *   *Fix:* Bypassed the bug by changing the Map Color Scheme in RViz to `costmap` and saving it as `fixed.rviz`.
*   **Lidar Zombie Node:** Rebooting the Uno Q caused the Lidar hardware to jump from `/dev/ttyUSB0` to `/dev/ttyUSB1`, causing the `rplidar_node` to lock up as a zombie process with Error `80008004`.
    *   *Fix:* Mapped both USB ports in Docker and dynamically passed `serial_port:=/dev/ttyUSB1` to the launch file.

## 4. Current Status
*   End-to-End communication is established. Lidar successfully spins automatically on power.
