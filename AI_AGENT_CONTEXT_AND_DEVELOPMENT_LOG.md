# AI-AGENT COMPREHENSIVE CONTEXT & DEVELOPMENT LOG

**Document Purpose**: Autonomous engineering context, hardware wiring schematics, low-level firmware protocols, failure analysis, middleware topology, and development manual for AI agents and roboticists continuing work on the **Distributed ROS 2 Robot Architecture**.

---

## 1. System Topology & Architecture

```mermaid
graph TD
    subgraph Edge Hardware: Arduino Uno Q (192.168.1.17)
        MCU[STM32U585 Zephyr M33 Core]
        IMU[7Semi BNO086 9-DOF IMU] -->|I2C Wire2 A4/A5 + INT D2 @ 0x4B| MCU
        MCU -->|Bridge.provide 'imu/raw'| ROUTER[arduino-router IPC /var/run/arduino-router.sock]
        
        LIDAR[RPLidar C1] -->|UART /dev/ttyUSB0 @ 460800 baud| DOCKER_EDGE[Docker Container: rplidar]
        ROUTER -->|msgpack IPC| DOCKER_EDGE
        
        subgraph rplidar Container
            PUB_LIDAR[rplidar_node -> /scan @ 10 Hz]
            PUB_IMU[imu_publisher.py -> /imu/data @ 100 Hz]
        end
    end

    subgraph Distributed Network: Wi-Fi (ROS_DOMAIN_ID=42, CycloneDDS)
        PUB_LIDAR -->|UDP Multicast/Unicast| DDS[CycloneDDS DataBus]
        PUB_IMU -->|UDP Multicast/Unicast| DDS
    end

    subgraph Laptop Station: Development PC (192.168.1.15)
        DDS --> DOCKER_HOST[DevContainer: thirsty_burnell]
        
        subgraph thirsty_burnell Container
            RELAY[qos_relay.py: BestEffort -> Reliable + Clock Sync]
            EKF[robot_localization: EKF Filter]
            SLAM[slam_toolbox: Async 2D SLAM]
            DASH[Flask + Three.js Dashboard @ :5000]
            RVIZ[RViz2 3D Visualizer]
        end
    end
```

---

## 2. Hardware Wiring & Pin Mapping Specification

### 7Semi BNO086 (ES-12243) $\leftrightarrow$ Arduino Uno Q

| 7Semi BNO086 Pin | Uno Q Physical Pin | STM32 Zephyr Resource | Electrical Function | Logic Level |
| :--- | :--- | :--- | :--- | :--- |
| **VCC** | **3.3V Pin** | 3.3V Power Rail | Power Supply | 3.3V DC |
| **GND** | **GND Pin** | Ground Plane | Common Reference | 0V |
| **SDA** | **Analog Pin A4** | `Wire2` (I2C2 SDA) | I2C Serial Data | 3.3V Open-Drain (Internal Pullup) |
| **SCL** | **Analog Pin A5** | `Wire2` (I2C2 SCL) | I2C Serial Clock (100 kHz) | 3.3V Open-Drain (Internal Pullup) |
| **INT / INTN** | **Digital Pin D2** | GPIO Port / Pin 2 | Active-Low Data Ready Interrupt | 3.3V (`pinMode(2, INPUT_PULLUP)`) |
| **RST / NRST** | *NC* | Hardware Reset | Managed via software SHTP reset | N/A |
| **PS0 / PS1** | *NC (Factory GND)* | Protocol Mode Select | Hardwired to `(0, 0)` for I2C | 0V (I2C Address: `0x4B`) |

### RPLidar C1 $\leftrightarrow$ Arduino Uno Q
- **Interface**: USB Type-A to Micro-USB / CP2102 Bridge.
- **Port**: `/dev/ttyUSB0` (Baud rate: 460800).
- **Permissions**: `chmod 666 /dev/ttyUSB0`.
- **Motor / Health Status**: Standard Scan Mode, 5 kHz sample rate, 10.0 Hz scan frequency, 16.0 m range.

---

## 3. History of Failures, Root Causes & Breakthrough Solutions

### Failure 1: I2C Address & SHTP Bus Lockup
- **Symptom**: Standard I2C scanners on default `Wire` found zero devices; `Wire.requestFrom(0x4A, ...)` returned 0 bytes.
- **Root Cause**: The Arduino Uno Q runs Zephyr OS where the standard Uno header pins A4/A5 are mapped to `Wire2` (not `Wire`). Additionally, the 7Semi breakout pulls the address select pin high by default, placing the chip at address `0x4B` (not `0x4A`).
- **Breakthrough Fix**:
  ```cpp
  static BnoI2CBus bus(Wire2, -1, -1, 0x4B, 100000, 2, -1);
  static BNO08x_7Semi bno(bus);
  ```

---

### Failure 2: SHTP Feature Report Descriptor Rejection
- **Symptom**: Calling `bno.enableLinearAccel(10)` corrupted the sensor state machine, resulting in frozen packets (`10000,0,0,0...`).
- **Root Cause**: The 7Semi driver's `enableLinearAccel` implementation sends an un-negotiated SHTP report code that the BNO086 firmware rejects on boot.
- **Breakthrough Fix**: Initialize only the proven SHTP fusion reports:
  ```cpp
  bno.enableAcc(20);             // 50 Hz Raw Acceleration
  bno.enableGyro(20);            // 50 Hz Gyroscope
  bno.enableRotationVector(20);  // 50 Hz 9-DOF Fused Quaternion
  bno.enableGameRotationVector(20); // 50 Hz Game Rotation Vector (6-DOF)
  ```

---

### Failure 3: IPC Round-Trip Bottleneck (7.7 Hz $\rightarrow$ 100.039 Hz)
- **Symptom**: Querying 10 separate RPC properties (`imu/qr`, `imu/qi`, `imu/ax`, etc.) over `arduino-router` took ~130ms per cycle, throttling the IMU node to 7.7 Hz.
- **Root Cause**: Each `Bridge.provide` call incurs a round-trip Unix Domain Socket context switch and msgpack serialization overhead.
- **Breakthrough Fix**: Engineered a single atomic string RPC payload on the STM32:
  ```cpp
  // Format: qr,qi,qj,qk,ax,ay,az,gx,gy,gz,count
  imu_str = String(q_r) + "," + String(q_i) + "," + String(q_j) + "," + String(q_k) + "," +
            String((int)(ax * 100.0f)) + "," + String((int)(ay * 100.0f)) + "," + String((int)(az * 100.0f)) + "," +
            String((int)(gx * 1000.0f)) + "," + String((int)(gy * 1000.0f)) + "," + String((int)(gz * 1000.0f)) + "," +
            String(packet_count);
  Bridge.provide("imu/raw", []() { return imu_str; });
  ```
  *Result*: Reduced cycle time from 130ms to <0.8ms, achieving steady **100.039 Hz** throughput.

---

### Failure 4: Quaternion Sign Inversion Axis Flips ($q \leftrightarrow -q$)
- **Symptom**: In RViz, rotating the sensor past certain pitch angles caused sudden 180° visual snaps.
- **Root Cause**: Quaternions double-cover 3D rotations ($q$ and $-q$ represent the identical physical orientation). The on-chip fusion engine occasionally flips signs across the hemisphere boundary.
- **Breakthrough Fix**: Implemented continuous dot-product tracking in Python:
  ```python
  dot = w*last_quat[0] + x*last_quat[1] + y*last_quat[2] + z*last_quat[3]
  if dot < 0.0:
      w, x, y, z = -w, -x, -y, -z
  ```

---

### Failure 5: Multi-Machine Clock Drift & RViz Extrapolation Warnings
- **Symptom**: RViz display error: `Lookup would require extrapolation into the future. Requested time X but latest data is at time Y`.
- **Root Cause**: Timestamps stamped on the Uno Q clock lagged the laptop's local system clock by 5–8 ms over Wi-Fi.
- **Breakthrough Fix**:
  1. The receiver node (`imu_dead_reckoning.py` / `qos_relay.py`) re-stamps incoming packets using local synchronized clock (`self.get_clock().now()`).
  2. Broadcasted dynamic transforms include a `+100ms` forward time-to-live buffer.
  3. Static sensor mounting transforms (`base_link -> imu_link`) are broadcasted atomically in the same packet array.

---

### Failure 6: Double-Integration Gravity Drift & Multi-Axis Runaway
- **Symptom**: When held flat, the sensor model fell into an infinite abyss ($Z$-axis); when tilted 90°, it accelerated sideways across the room ($X/Y$ axes).
- **Root Cause**: 
  - Nominal gravity ($9.806\,\text{m/s}^2$) differed from local measured gravity ($9.53\,\text{m/s}^2$).
  - Subtracting gravity only on global $Z$ failed when the sensor was tilted, projecting $1G$ onto the body $X/Y$ axes.
- **Breakthrough Fix**: Omnidirectional 3D Body-Frame Gravity Projection:
  ```python
  def compute_gravity_vector(q, g_mag=9.53):
      qw, qx, qy, qz = q
      gx = 2.0 * (qx * qz - qw * qy) * g_mag
      gy = 2.0 * (qy * qz + qw * qx) * g_mag
      gz = (qw * qw - qx * qx - qy * qy + qz * qz) * g_mag
      return [gx, gy, gz]
  ```
  Subtracting `[gx, gy, gz]` directly from the body accelerometer cancels gravity at **any 3D angle** (flat, tilted 45°, pitched 90°, or upside down).

---

### Failure 7: RMW Mismatch & CycloneDDS Interface Binding
- **Symptom**: `ros2 topic list` showed topics on Domain 42, but `ros2 topic echo` received 0 messages.
- **Root Cause**: Uno Q container defaulted to `rmw_fastrtps_cpp` without multicast route, while Laptop used `rmw_cyclonedds_cpp`.
- **Breakthrough Fix**:
  1. Installed `ros-jazzy-rmw-cyclonedds-cpp` in the `rplidar` container on Uno Q.
  2. Configured identical CycloneDDS XML interface bindings on both machines:
     - Uno Q: `<NetworkInterfaceAddress>wlan0</NetworkInterfaceAddress>`
     - Laptop: `<NetworkInterfaceAddress>wlp4s0</NetworkInterfaceAddress>`

---

### Failure 8: SLAM Lifecycle Race Condition (`Fixed Frame [map] does not exist`)
- **Symptom**: Clicking "Start SLAM Mapping" opened RViz with a persistent red error: `Fixed Frame: Frame [map] does not exist`.
- **Root Cause**: `slam_toolbox` in ROS 2 Jazzy is an unconfigured lifecycle node at startup. Initializing the Ceres non-linear solver and executing lifecycle transitions (`unconfigured -> inactive -> active`) takes ~2.5 seconds. RViz was opening at $t=0$, attempting to resolve the `map` coordinate frame before `slam_toolbox` created it, latching a permanent red error status in RViz.
- **Breakthrough Fix**:
  1. **Sequenced Startup**: Wrapped `rviz2` in a `TimerAction(period=3.5)` in [`imu_slam.launch.py`](file:///home/bliss/my_robot_ws/src/my_robot_nav/launch/imu_slam.launch.py) so it only opens **after** `slam_toolbox` is verified in the `ACTIVE` state.
  2. **Fixed Frame Alignment**: Set the initial RViz Fixed Frame to `odom` in [`mapping.rviz`](file:///home/bliss/my_robot_ws/src/my_robot_nav/config/mapping.rviz) (which exists immediately from EKF at $t=0$), allowing `/map` to overlay without error.

---

### Failure 9: CycloneDDS XML Schema Element Placement
- **Symptom**: `python3: config: //CycloneDDS/Domain/General: MaxAutoParticipantIndex: unknown element (cyclonedds.xml line 8)` causing `rmw_create_node: failed to create domain`.
- **Root Cause**: In the Eclipse CycloneDDS XML schema, the tag `<MaxAutoParticipantIndex>` belongs strictly inside `<Discovery>`, not `<General>`.
- **Breakthrough Fix**:
  ```xml
  <Domain id="any">
      <General>
          <Interfaces><NetworkInterface name="wlp4s0" /></Interfaces>
          <AllowMulticast>true</AllowMulticast>
      </General>
      <Discovery>
          <MaxAutoParticipantIndex>120</MaxAutoParticipantIndex>
      </Discovery>
  </Domain>
  ```

---

### Failure 10: VS Code Remote Container Port 5000 Conflict
- **Symptom**: Starting Flask web server threw `Address already in use. Port 5000 is in use by another program`.
- **Root Cause**: VS Code Remote Containers automatically opens internal port-forwarding tunnels and loopback listeners on port `5000`.
- **Breakthrough Fix**:
  1. Moved Dashboard default port to **`5050`**.
  2. Added dynamic port discovery `find_available_port(5050)` in `app.py` to seamlessly increment to 5051/5052 if any port is ever occupied.

---

## 4. Key Source Code References

### 1. Uno Q STM32 Firmware (`BnoTest.ino`)
- **Location on Uno Q**: `/home/arduino/BnoTest/BnoTest.ino`
- **Compiler**: `arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest`
- **Uploader**: `arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest`

### 2. Edge ROS 2 Driver (`imu_publisher.py`)
- **Location on Uno Q**: `/home/arduino/pendrive/ros_ws/src/bno08x_ros/bno08x_ros/imu_publisher.py`
- **Container**: `rplidar` (mounted to `/ws/src/bno08x_ros/bno08x_ros/imu_publisher.py`)
- **Topics Published**:
  - `/imu/data` (`sensor_msgs/msg/Imu` @ 100 Hz, with full covariance matrices)
  - `/imu/data_raw` (`sensor_msgs/msg/Imu` @ 100 Hz)

### 3. Jitter-Filtered 3D Motion Tracker (`imu_dead_reckoning_pure.py`)
- **Location on Laptop**: [`src/my_robot_nav/scripts/imu_dead_reckoning_pure.py`](file:///home/bliss/my_robot_ws/src/my_robot_nav/scripts/imu_dead_reckoning_pure.py)
- **Features**: Quaternion SLERP smoothing ($\alpha=0.35$), unphysical outlier glitch gate ($>35^\circ / 10\text{ms}$ rejection), 3D body gravity compensation, and ZUPT resting clamp.

### 4. Unified Web Control & Telemetry Dashboard (`app.py`)
- **Location on Laptop**: [`src/my_robot_dashboard/app.py`](file:///home/bliss/my_robot_ws/src/my_robot_dashboard/app.py)
- **Server**: Flask + SSE live telemetry stream on port `5000`.
- **Frontend**: [`src/my_robot_dashboard/templates/index.html`](file:///home/bliss/my_robot_ws/src/my_robot_dashboard/templates/index.html) + Three.js 3D orientation canvas + 2D polar Lidar radar.

---

## 5. Standard Operating Runbook (Commands Cheat Sheet)

### Launch Dashboard (Preferred Single-Point Control)
```bash
cd ~/my_robot_ws
./start_dashboard.sh
# Access in browser at: http://localhost:5000
```

### Launch Edge Sensors Remotely via Script
```bash
cd ~/my_robot_ws
python3 scripts/probes/sensors/start_edge_sensors.py
```

### Verify Distributed Topics & Rates Headlessly
```bash
python3 scripts/probes/networking/verify_all_topics.py
```

### Launch Isolated Visualizers
```bash
./view_imu.sh           # Gesture mode (anchored to origin)
./view_imu_integral.sh  # Pure cumulative open-loop double integrator
```

---

## 6. Next Phase Blueprint: Full SLAM Sensor Fusion

```mermaid
graph LR
    subgraph Sensors
        IMU["/imu/data @ 100 Hz"]
        LIDAR["/scan @ 10 Hz"]
    end

    subgraph Filtering & Sync
        IMU --> RELAY["qos_relay.py (Re-stamping + Reliable QoS)"]
        LIDAR --> RELAY
    end

    subgraph Estimation & Mapping
        RELAY -->|/imu_reliable| EKF["robot_localization EKF (odom -> base_link)"]
        RELAY -->|/scan_reliable| SLAM["slam_toolbox Async SLAM (map -> odom)"]
        EKF --> SLAM
    end

    subgraph Output
        SLAM --> MAP["/map (OccupancyGrid)"]
        EKF --> ODOM["/odometry/filtered"]
    end
```

### Files Configured & Ready for Fusion Launch:
1. **Launch File**: [`src/my_robot_nav/launch/imu_slam.launch.py`](file:///home/bliss/my_robot_ws/src/my_robot_nav/launch/imu_slam.launch.py)
2. **EKF Config**: [`src/my_robot_nav/config/ekf_imu_only.yaml`](file:///home/bliss/my_robot_ws/src/my_robot_nav/config/ekf_imu_only.yaml)
3. **SLAM Config**: [`src/my_robot_nav/config/mapper_params_online_async.yaml`](file:///home/bliss/my_robot_ws/src/my_robot_nav/config/mapper_params_online_async.yaml)
4. **URDF Model**: [`src/my_robot_description/urdf/robot.urdf.xacro`](file:///home/bliss/my_robot_ws/src/my_robot_description/urdf/robot.urdf.xacro)

To launch the complete SLAM stack:
```bash
ros2 launch my_robot_nav imu_slam.launch.py
```

---

## 7. Mandatory GitHub Issue Lifecycle & AI Workflow Protocol

To maintain complete traceability, reproducible context, and clean software engineering standards across all AI agents and human contributors:

### 1. Issue Creation Rule
Before starting work on any bug fix, optimization, or feature:
```bash
gh issue create --title "<Component>: <Clear description>" --body "<Technical requirements & context>"
```

### 2. Implementation & Traceability
- Branching: Always branch from `main` (e.g., `feature/lidar-imu-slam-fusion` or `fix/i2c-timeout`).
- Commits: Reference the issue number in the commit message (e.g., `feat(slam): implement QoS relay and EKF fusion (#1)`).

### 3. Resolution & Closure Protocol
When an issue is resolved and tested:
```bash
gh issue close <issue_number> --comment "### Resolution Summary
1. Root Cause / Architecture: ...
2. Changes Implemented: ...
3. Verification & Test Logs: ...
4. Linked Commits: ..."
```
