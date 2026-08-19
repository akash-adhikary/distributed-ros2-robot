# MPU Daemon (Qualcomm QRB2210 Debian Linux)

This directory contains the Python / C++ lightweight bridge running on the **Qualcomm QRB2210** processor under Debian Linux (2GB RAM).

## Responsibilities:
1. **Lightweight DDS Bridge**: Relays ROS 2 messages (`/cmd_vel`, `/odom`, `/scan`) with the host PC.
2. **Slamtec RPLiDAR Interface**: Publishes `/scan` using minimal CPU/RAM.
3. **Arduino Bridge IPC**: Transfers velocity setpoints down to the STM32 MCU and reads encoder ticks back.
4. **Low Memory Profile**: Designed strictly to stay under 50–100MB of RAM to guarantee high system stability on 2GB RAM devices.
