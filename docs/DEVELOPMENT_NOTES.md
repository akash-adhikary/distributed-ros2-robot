# 📝 Simulation Engineering & Debugging Notes

A collection of resolved issues and architectural solutions encountered during simulation setup for the diff-drive robot.

---

## 1. X11 GUI display authorization (Container -> Host)
* **Symptoms**: RViz2 and Gazebo crash immediately on launch with:
  ```text
  qt.qpa.xcb: could not connect to display :0
  Authorization required, but no authorization protocol specified
  ```
* **Cause**: The host's X11 server (XWayland) blocks GUI rendering requests from container sandboxes by default. This access control list resets whenever the host machine is rebooted.
* **Resolution**: Run this command on the **host machine's terminal** (not inside VS Code container) to authorize local container connections:
  ```bash
  xhost +local:root
  ```

---

## 2. Gazebo Ogre 2 Render Engine crash & RViz2 Qt crash
* **Symptoms**: Gazebo crashes with `Segmentation fault` inside `libgz-rendering-ogre2.so` when using GUI, or RViz2 crashes immediately on launch with `exit code -6` and Qt errors.
* **Cause**: 
  - Forcing software rendering with `LIBGL_ALWAYS_SOFTWARE=1` in the container's `.bashrc` conflicts with Ogre 2's device selection API, causing Gazebo's visual window to crash.
  - On Wayland hosts, Qt (used by RViz2) may try to auto-detect Wayland directly in the container and fail, causing an instant launch crash.
* **Resolution**: 
  - Keep hardware acceleration enabled inside the container (do not set `LIBGL_ALWAYS_SOFTWARE=1`).
  - Force Qt to use XWayland explicitly inside the container's `.bashrc`:
    ```bash
    export QT_QPA_PLATFORM=xcb
    ```

---

## 3. Topic namespacing & bridge routing
* **Symptoms**: Robot did not respond to `/cmd_vel` keyboard teleop, and `/odom` received no messages.
* **Cause**: Gazebo Sim automatically namespaces diff-drive plugin topics under the model name (e.g., `/model/my_robot/cmd_vel`, `/model/my_robot/odom`, and `/model/my_robot/tf`). Sourcing simple `/cmd_vel` to `/cmd_vel` direct bridges bypassed the robot's receiver.
* **Resolution**: Bridged the fully namespaced Gazebo topics and remapped them directly to the flat root topics in ROS 2 via `sim.launch.py`:
  ```python
  arguments=[
      '/model/my_robot/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
      '/model/my_robot/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
      '/model/my_robot/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
  ],
  remappings=[
      ('/model/my_robot/cmd_vel', '/cmd_vel'),
      ('/model/my_robot/odom', '/odom'),
      ('/model/my_robot/tf', '/tf'),
  ]
  ```

---

## 4. Scan `frame_id` mismatch in SLAM
* **Symptoms**: Scan topics published correctly, but SLAM Toolbox refused to create a map, remaining completely silent.
* **Cause**: Gazebo publishes laser scan messages with the frame ID `my_robot/base_footprint/laser_frame`. However, the robot's ROS TF tree defined the scanner link simply as `laser_frame`. Because the frame names did not match, SLAM could not correlate scans to the robot pose.
* **Resolution**: Added a static transform publisher in `sim.launch.py` to bridge the two frames seamlessly:
  ```python
  Node(
      package='tf2_ros',
      executable='static_transform_publisher',
      arguments=['0', '0', '0', '0', '0', '0', 'laser_frame', 'my_robot/base_footprint/laser_frame']
  )
  ```

---

## 5. Lifecycle Node auto-start (SLAM Toolbox)
* **Symptoms**: `sync_slam_toolbox_node` launched but stayed in an `unconfigured` state, never subscribing to scans or generating a map.
* **Cause**: SLAM Toolbox is a ROS 2 Lifecycle Node. Launching it using standard `launch_ros.actions.Node` leaves it unconfigured and inactive on boot.
* **Resolution**: Upgraded the launcher to a `LifecycleNode` in `slam.launch.py` and registered automated event handlers to configure and activate the node dynamically as soon as it spawns:
  ```python
  # Configure event
  EmitEvent(
      event=ChangeState(
          lifecycle_node_matcher=matches_action(slam_toolbox_node),
          transition_id=Transition.TRANSITION_CONFIGURE
      )
  )
  # Activate event
  RegisterEventHandler(
      OnStateTransition(
          target_lifecycle_node=slam_toolbox_node,
          start_state='configuring',
          goal_state='inactive',
          entities=[
              EmitEvent(
                  event=ChangeState(
                      lifecycle_node_matcher=matches_action(slam_toolbox_node),
                      transition_id=Transition.TRANSITION_ACTIVATE
                  )
              )
          ]
      )
  # ...
  ```

---

## 6. Collision Monitor polygon points type constraint
* **Symptoms**: Nav2 launch starts but immediately aborts bringing up the lifecycle nodes, outputting this error:
  ```text
  Error while getting parameters: parameter 'stop_polygon.points' has invalid type: Wrong parameter type, parameter {stop_polygon.points} is of type {string}, setting it to {double_array} is not allowed.
  ```
* **Cause**: In the Nav2 `collision_monitor` package, the polygon coordinate `points` parameter expects to be loaded as a formatted **string** (which it parses internally), not as a raw YAML double array.
* **Resolution**: Wrapped the points arrays inside double quotes in `nav2_params.yaml`:
  ```yaml
  stop_polygon:
    type: "polygon"
    points: "[0.3, 0.2, 0.3, -0.2, 0.0, -0.2, 0.0, 0.2]" # must be a string!
  ```

---

## 7. Docking Server plugin requirement
* **Symptoms**: Nav2 launch starts but immediately aborts bringing up the lifecycle nodes, outputting this error:
  ```text
  [docking_server]: Charging dock plugins not given!
  [lifecycle_manager_navigation]: Failed to change state for node: docking_server
  ```
* **Cause**: In ROS 2 Jazzy, the `docking_server` node is enabled by default in `nav2_bringup`, but it requires at least one charging dock plugin configuration in the parameters.
* **Resolution**: Added a default charging dock plugin configuration block for `docking_server` in `nav2_params.yaml`:
  ```yaml
  docking_server:
    ros__parameters:
      use_sim_time: True
      controller_frequency: 50.0
      dock_plugins: ["simple_dock"]
      simple_dock:
        plugin: "opennav_docking::SimpleChargingDock"
        docking_threshold: 0.05
        staging_threshold: 0.5
  ```

---

## 8. Gazebo Sim black viewport screen
* **Symptoms**: Gazebo Sim GUI window opens, but the 3D simulation viewport is completely black.
* **Cause**: Gazebo Sim (Harmonic) defaults to the Ogre 2 rendering engine, which requires modern OpenGL features (typically 4.3+) that often fail or are blocked inside container GPU pass-through environments on hybrid graphics laptops.
* **Resolution**: Force Gazebo to use the classic Ogre 1 rendering engine by exporting this environment variable in the container's `.bashrc`:
  ```bash
  export GZ_RENDERING_ENGINE_NAME=ogre
  ```
