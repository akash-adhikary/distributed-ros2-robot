# 🤖 Distributed Edge-ROS 2 Robot Workspace

This repository contains the complete ROS 2 workspace, deployment scripts, and architectural documentation for a distributed autonomous robot. 

The architecture is split between a lightweight edge device (Arduino Uno Q) handling hard-real-time hardware, and a development laptop handling heavy computation (Nav2, SLAM).

## 📐 Architecture & Documentation

Before diving into the code, please read the core design documents:
1. [System Architecture (docs/ARCHITECTURE.md)](docs/ARCHITECTURE.md) - Explains the edge-lite design philosophy, node distribution, and ROS 2 topic routing.
2. [Edge Deployment Guide (docs/UNO_Q_DEPLOYMENT.md)](docs/UNO_Q_DEPLOYMENT.md) - Step-by-step instructions for reproducing the Dockerized ROS 2 setup on the 2GB RAM Arduino Uno Q.

## 📂 Repository Structure

```text
my_robot_ws/
├── src/                      # ROS 2 Source Packages
│   ├── rplidar_ros/          # RPLIDAR C1 Driver (ros2 branch)
│   ├── my_robot_bringup/     # Launch files
│   ├── my_robot_description/ # URDF / Robot Models
│   └── my_robot_nav/         # Nav2 Configurations & Maps
│
├── scripts/                  # Automation & Deployment Scripts
│   ├── deploy_lidar_docker.py# Deploys the ROS 2 container to the Uno Q
│   ├── spin_up_motor.py      # Bypasses hardware timeouts via pyserial
│   ├── start_*.sh            # Shortcut scripts for Laptop Nav2/SLAM
│   └── ssh_mount.py          # Configures the USB Pendrive on the edge board
│
└── docs/                     # Technical Documentation
    ├── ARCHITECTURE.md
    └── UNO_Q_DEPLOYMENT.md
```

## 🚀 Quick Start (Phase 1: Sensor Integration)

### 1. Edge Node (Arduino Uno Q)
The edge node runs entirely inside a Docker container from a mounted USB flash drive to preserve the internal eMMC.
* Ensure both devices are on the same Wi-Fi.
* Deploy the custom Docker image to the Uno Q by following the [Deployment Guide](docs/UNO_Q_DEPLOYMENT.md).
* Launch the hardware node on the Uno Q:
  ```bash
  /home/arduino/start_rplidar.sh
  ```

### 2. Compute Node (Laptop)
The laptop receives the sensor data over Wi-Fi via **CycloneDDS**.
* Add the following to your `~/.bashrc`:
  ```bash
  export ROS_DOMAIN_ID=42
  export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
  ```
* Verify connection:
  ```bash
  ros2 topic hz /scan
  ```
* Visualize in RViz2 (Set Fixed Frame to `laser`):
  ```bash
  rviz2
  ```

## 🛡️ License
MIT License
