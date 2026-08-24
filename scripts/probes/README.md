# Sensor Diagnostic & Probing Toolkit

Modular, standalone diagnostic tools to test, probe, and verify every layer of the robot system independently—from raw I2C hardware registers up to distributed ROS 2 CycloneDDS topics.

---

## Directory Overview

```text
scripts/probes/
├── edge_mcu/                 # Microcontroller (STM32 Zephyr) & I2C Probes
│   ├── query_raw_bridge.py   # Queries /var/run/arduino-router.sock directly over msgpack IPC
│   └── flash_firmware.py     # Compiles and flashes BnoTest.ino to Uno Q STM32
│
├── sensors/                  # Edge Sensor Launchers & Unit Tests
│   └── start_edge_sensors.py # Starts RPLidar C1 (10 Hz) & BNO086 (100 Hz) via CycloneDDS
│
├── networking/               # Middleware & Network Verification
│   └── verify_all_topics.py  # Checks all distributed topics, rates, and payloads over Wi-Fi
│
└── visualization/            # Isolated RViz Launchers
    ├── view_imu.sh           # Visualizes 3D IMU orientation & gesture tracking with origin anchor
    └── view_imu_integral.sh  # Visualizes pure cumulative double-integration without origin reset
```

---

## Quick Reference Commands

### 1. Launch All Edge Sensors (On Uno Q)
```bash
python3 scripts/probes/sensors/start_edge_sensors.py
```

### 2. Verify Distributed Topics & Rates (From Laptop)
```bash
python3 scripts/probes/networking/verify_all_topics.py
```

### 3. Query Raw MCU Bridge Directly (Bypass ROS)
```bash
python3 scripts/probes/edge_mcu/query_raw_bridge.py
```

### 4. Visualize IMU in RViz
```bash
# Gesture Mode (Returns to origin smoothly)
./view_imu.sh

# Cumulative Open-Loop Mode (Pure integration, holds position)
./view_imu_integral.sh
```
