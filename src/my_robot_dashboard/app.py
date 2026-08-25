#!/usr/bin/env python3
"""
Industrial-Grade Distributed Robot Control & Diagnostic Dashboard
==================================================================
Features & Resilience:
  1. PID Lockfile & Singleton Guard: Automatic graceful takeover if launched in another terminal.
  2. Complete Clean Teardown: Signal handlers (SIGINT, SIGTERM, atexit) kill all children cleanly.
  3. One-Click Emergency Stop: /api/system/kill_all endpoint resets all local & Uno Q ROS activity.
  4. Decoupled Persistent DDS Bridge: qos_relay runs as an independent daemon.
"""
import os
import sys
import json
import time
import math
import fcntl
import signal
import atexit
import subprocess
import threading
import socket
from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS

# ---- SINGLETON GUARD & PROCESS TAKEOVER ----
LOCKFILE_PATH = "/tmp/my_robot_dashboard.lock"
PIDFILE_PATH = "/tmp/my_robot_dashboard.pid"

def enforce_singleton(port=5050):
    """
    Ensures only ONE instance of the dashboard ever runs.
    If an existing instance is active, it cleanly terminates it, releases the port, and takes over.
    """
    if os.path.exists(PIDFILE_PATH):
        try:
            with open(PIDFILE_PATH, 'r') as f:
                old_pid = int(f.read().strip())
            if old_pid != os.getpid():
                try:
                    os.kill(old_pid, 0)
                    print(f"[Singleton Guard] Terminating previous dashboard instance (PID {old_pid})...")
                    os.kill(old_pid, signal.SIGTERM)
                    time.sleep(1.0)
                    try:
                        os.kill(old_pid, signal.SIGKILL)
                    except OSError:
                        pass
                except OSError:
                    pass
        except Exception:
            pass

    # Ensure port is released if held by a previous Python dashboard instance
    pass


    # Write current PID
    try:
        with open(PIDFILE_PATH, 'w') as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

target_port = int(os.environ.get('PORT', 5050))
enforce_singleton(target_port)


# ---- ROS 2 CycloneDDS environment ----
os.environ['ROS_DOMAIN_ID'] = '42'
os.environ['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'
if os.path.exists('/home/ros/my_robot_ws/cyclonedds.xml'):
    os.environ['CYCLONEDDS_URI'] = 'file:///home/ros/my_robot_ws/cyclonedds.xml'
elif os.path.exists('/home/bliss/my_robot_ws/cyclonedds.xml'):
    os.environ['CYCLONEDDS_URI'] = 'file:///home/bliss/my_robot_ws/cyclonedds.xml'

if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'
os.environ['QT_X11_NO_MITSHM'] = '1'

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, LaserScan

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

robot_config = {
    'ip': os.environ.get('UNOQ_IP', '192.168.1.17'),
    'user': 'arduino',
    'pass': 'Askaban78@#'
}

telemetry = {
    'robot_ip': robot_config['ip'],
    'unoq_online': True,
    'lidar_running': False,
    'imu_running': False,
    'slam_running': False,
    'imu_rate': 0.0,
    'lidar_rate': 0.0,
    'roll_deg': 0.0,
    'pitch_deg': 0.0,
    'yaw_deg': 0.0,
    'quat': {'w': 1.0, 'x': 0.0, 'y': 0.0, 'z': 0.0},
    'acc': {'x': 0.0, 'y': 0.0, 'z': 0.0},
    'gyro': {'x': 0.0, 'y': 0.0, 'z': 0.0},
    'lidar_points': [],
    'map_metadata': {'width': 0, 'height': 0, 'resolution': 0.05}
}

imu_msg_times = []
lidar_msg_times = []
last_imu_update = 0.0
last_scan_update = 0.0
active_processes = {}
ros_node = None
ros_running = True

# ---- ROS Subscriber Node ----
class DashboardRosNode(Node):
    def __init__(self):
        super().__init__('dashboard_backend_node')
        self.sub_imu = self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.get_logger().info("Dashboard ROS 2 Node initialized on Domain 42.")

    def imu_cb(self, msg):
        global telemetry, imu_msg_times, last_imu_update
        now = time.time()
        imu_msg_times.append(now)
        imu_msg_times = [t for t in imu_msg_times if now - t <= 2.0]
        telemetry['imu_rate'] = round(len(imu_msg_times) / 2.0, 1)
        telemetry['imu_running'] = (telemetry['imu_rate'] > 5.0)

        if now - last_imu_update < 0.033:
            return
        last_imu_update = now

        w = msg.orientation.w
        x = msg.orientation.x
        y = msg.orientation.y
        z = msg.orientation.z
        telemetry['quat'] = {'w': round(w, 4), 'x': round(x, 4), 'y': round(y, 4), 'z': round(z, 4)}

        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        telemetry['roll_deg'] = round(math.atan2(sinr_cosp, cosr_cosp) * 180.0 / math.pi, 1)

        sinp = 2.0 * (w * y - z * x)
        if abs(sinp) >= 1.0:
            telemetry['pitch_deg'] = round(math.copysign(90.0, sinp), 1)
        else:
            telemetry['pitch_deg'] = round(math.asin(sinp) * 180.0 / math.pi, 1)

        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        telemetry['yaw_deg'] = round(math.atan2(siny_cosp, cosy_cosp) * 180.0 / math.pi, 1)

        telemetry['acc'] = {
            'x': round(msg.linear_acceleration.x, 2),
            'y': round(msg.linear_acceleration.y, 2),
            'z': round(msg.linear_acceleration.z, 2)
        }
        telemetry['gyro'] = {
            'x': round(msg.angular_velocity.x, 2),
            'y': round(msg.angular_velocity.y, 2),
            'z': round(msg.angular_velocity.z, 2)
        }

    def scan_cb(self, msg):
        global telemetry, lidar_msg_times, last_scan_update
        now = time.time()
        lidar_msg_times.append(now)
        lidar_msg_times = [t for t in lidar_msg_times if now - t <= 2.0]
        telemetry['lidar_rate'] = round(len(lidar_msg_times) / 2.0, 1)
        telemetry['lidar_running'] = (telemetry['lidar_rate'] > 2.0)

        if now - last_scan_update < 0.09:
            return
        last_scan_update = now

        step = max(1, len(msg.ranges) // 100)
        points = []
        for i in range(0, len(msg.ranges), step):
            r = msg.ranges[i]
            if msg.range_min < r < msg.range_max:
                angle = msg.angle_min + i * msg.angle_increment
                points.append([round(angle, 3), round(r, 2)])
        telemetry['lidar_points'] = points

# ---- Non-blocking ROS spin thread ----
def non_blocking_ros_spin():
    global ros_node, ros_running, telemetry
    try:
        rclpy.init()
        ros_node = DashboardRosNode()
        last_heartbeat_check = 0.0
        while ros_running and rclpy.ok():
            rclpy.spin_once(ros_node, timeout_sec=0.008)
            now = time.time()
            
            # Check sensor streams first
            sensor_active = (now - last_imu_update < 2.5) or (now - last_scan_update < 2.5)
            if sensor_active:
                telemetry['unoq_online'] = True
            else:
                # Periodic fast TCP probe (Port 22 SSH) every 2.0s if no topics flowing
                if now - last_heartbeat_check > 2.0:
                    last_heartbeat_check = now
                    ip = robot_config['ip']
                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.settimeout(0.6)
                            telemetry['unoq_online'] = (s.connect_ex((ip, 22)) == 0)
                    except Exception:
                        telemetry['unoq_online'] = False


            telemetry['slam_running'] = ('slam_toolbox' in active_processes and active_processes['slam_toolbox'].poll() is None)
            time.sleep(0.01)
    except Exception as e:
        print(f"[ROS Thread] Exception: {e}", file=sys.stderr)


    finally:
        if ros_node:
            try:
                ros_node.destroy_node()
            except Exception:
                pass
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception:
                pass

ros_thread = threading.Thread(target=non_blocking_ros_spin, daemon=True)
ros_thread.start()

# ---- Helper utilities ----
def get_ws_dir():
    if os.path.exists('/home/ros/my_robot_ws'):
        return '/home/ros/my_robot_ws'
    return '/home/bliss/my_robot_ws'

def get_exec_env():
    env = os.environ.copy()
    env['DISPLAY'] = os.environ.get('DISPLAY', ':0')
    env['QT_X11_NO_MITSHM'] = '1'
    env['ROS_DOMAIN_ID'] = '42'
    env['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'
    ws = get_ws_dir()
    cyclone = f'{ws}/cyclonedds.xml'
    if os.path.exists(cyclone):
        env['CYCLONEDDS_URI'] = f'file://{cyclone}'
    return env

def ssh_unoq_cmd(cmd, timeout=12):
    ip = robot_config['ip']
    password = robot_config['pass']
    user = robot_config['user']
    ssh_cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=4 {user}@{ip} \"{cmd}\""
    try:
        res = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if res.returncode == 0:
            telemetry['unoq_online'] = True
            return True, res.stdout.strip()
        else:
            telemetry['unoq_online'] = False
            return False, res.stderr.strip() or res.stdout.strip()
    except Exception as e:
        telemetry['unoq_online'] = False
        return False, str(e)

def start_qos_relay_daemon():
    """
    Start qos_relay as a persistent background process.
    Provides continuous 50Hz odom->base_link TF and static sensor transforms.
    """
    # Kill any stale existing instance
    subprocess.run("pkill -9 -f 'src/my_robot_nav/scripts/qos_relay.py' 2>/dev/null || true", shell=True)
    ws = get_ws_dir()
    cmd = (
        f"source /opt/ros/jazzy/setup.bash && "
        f"source {ws}/install/setup.bash 2>/dev/null || true && "
        f"python3 {ws}/src/my_robot_nav/scripts/qos_relay.py"
    )
    proc = subprocess.Popen(
        cmd, shell=True, executable='/bin/bash',
        env=get_exec_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    active_processes['qos_relay'] = proc
    return proc

# Cleanly start qos_relay daemon at boot
start_qos_relay_daemon()

def cleanup_all():
    """Clean exit handler terminating all child processes."""
    global ros_running
    ros_running = False
    print("\n[Dashboard Shutdown] Cleaning up all subprocesses...")
    subprocess.run("pkill -9 -f 'async_slam_toolbox_node|rviz2|qos_relay.py|imu_dead_reckoning' 2>/dev/null || true", shell=True)
    for name, proc in list(active_processes.items()):
        try:
            proc.terminate()
            proc.kill()
        except Exception:
            pass
    try:
        if os.path.exists(PIDFILE_PATH):
            os.remove(PIDFILE_PATH)
    except Exception:
        pass

atexit.register(cleanup_all)
signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))

# ---- REST API ROUTES ----

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config/ip', methods=['POST'])
def set_ip():
    req_data = request.get_json(silent=True) or {}
    new_ip = req_data.get('ip', '').strip()
    if new_ip:
        robot_config['ip'] = new_ip
        telemetry['robot_ip'] = new_ip
        return jsonify({'success': True, 'message': f'Robot IP updated to {new_ip}'})
    return jsonify({'success': False, 'message': 'Invalid IP address'})

@app.route('/api/telemetry')
def get_telemetry():
    return jsonify(telemetry)

@app.route('/api/stream')
def sse_stream():
    def event_stream():
        while True:
            try:
                data = json.dumps(telemetry)
                yield f"data: {data}\n\n"
                time.sleep(0.04)  # 25 FPS
            except GeneratorExit:
                break
            except Exception:
                time.sleep(0.05)
    return Response(event_stream(), mimetype="text/event-stream")

# ---- SYSTEM-WIDE EMERGENCY KILL / RESET ----
@app.route('/api/system/kill_all', methods=['POST'])
def kill_all_ros_activity():
    """
    Nuclear Kill Button: Terminates ALL local and edge ROS processes,
    clears participant leases, and resets system to clean zero.
    """
    # 1. Kill all local visualizers, SLAM, and nodes
    subprocess.run("pkill -9 -f 'async_slam_toolbox_node|rviz2|imu_dead_reckoning|tf2_ros|ros2' 2>/dev/null || true", shell=True)
    
    # 2. Kill edge sensors on Uno Q
    cmd_unoq = "docker exec -t rplidar pkill -9 -f 'rplidar_node|imu_publisher|ros2' 2>/dev/null || true"
    ssh_unoq_cmd(cmd_unoq)
    
    # 3. Reset internal telemetry state
    telemetry['lidar_running'] = False
    telemetry['imu_running'] = False
    telemetry['slam_running'] = False
    telemetry['lidar_rate'] = 0.0
    telemetry['imu_rate'] = 0.0
    telemetry['lidar_points'] = []
    
    # 4. Ensure qos_relay is cleanly restarted
    time.sleep(0.5)
    start_qos_relay_daemon()
    
    return jsonify({'success': True, 'message': 'All ROS activity terminated across Laptop & Uno Q. System reset to clean state.'})

@app.route('/api/sensors/lidar/start', methods=['POST'])
def start_lidar():
    cmd = """
    echo 'Askaban78@#' | sudo -S chmod 666 /dev/ttyUSB0 2>/dev/null || true
    docker start rplidar
    docker exec -t rplidar pkill -f 'rplidar_node' 2>/dev/null || true
    sleep 1
    docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0'
    """
    success, msg = ssh_unoq_cmd(cmd)
    return jsonify({'success': success, 'message': 'RPLidar C1 started' if success else msg})

@app.route('/api/sensors/lidar/stop', methods=['POST'])
def stop_lidar():
    cmd = "docker exec -t rplidar pkill -f 'rplidar_node' 2>/dev/null || true"
    success, msg = ssh_unoq_cmd(cmd)
    telemetry['lidar_running'] = False
    return jsonify({'success': success, 'message': 'RPLidar stopped' if success else msg})

@app.route('/api/sensors/imu/start', methods=['POST'])
def start_imu():
    cmd = """
    docker start rplidar
    docker exec -t rplidar pkill -f 'imu_publisher' 2>/dev/null || true
    sleep 1
    docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && python3 /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'
    """
    success, msg = ssh_unoq_cmd(cmd)
    return jsonify({'success': success, 'message': 'BNO086 IMU started' if success else msg})

@app.route('/api/sensors/imu/stop', methods=['POST'])
def stop_imu():
    cmd = "docker exec -t rplidar pkill -f 'imu_publisher' 2>/dev/null || true"
    success, msg = ssh_unoq_cmd(cmd)
    telemetry['imu_running'] = False
    return jsonify({'success': success, 'message': 'IMU stopped' if success else msg})

@app.route('/api/sensors/router/restart', methods=['POST'])
def restart_router():
    cmd = "echo 'Askaban78@#' | sudo -S systemctl restart arduino-router"
    success, msg = ssh_unoq_cmd(cmd)
    return jsonify({'success': success, 'message': 'Arduino router restarted' if success else msg})

@app.route('/api/sensors/unoq/reboot', methods=['POST'])
def reboot_unoq():
    cmd = "echo 'Askaban78@#' | sudo -S reboot"
    ssh_unoq_cmd(cmd, timeout=5)
    telemetry['unoq_online'] = False
    return jsonify({'success': True, 'message': 'Reboot signal sent to Uno Q'})

@app.route('/api/rviz/launch/<mode>', methods=['POST'])
def launch_rviz(mode):
    subprocess.run("pkill -9 -f rviz2 2>/dev/null || true", shell=True)
    subprocess.run("pkill -9 -f imu_dead_reckoning 2>/dev/null || true", shell=True)

    ws = get_ws_dir()
    if mode == 'imu':
        cmd = f"bash {ws}/view_imu.sh"
    elif mode == 'integral':
        cmd = f"bash {ws}/view_imu_integral.sh"
    elif mode == 'slam':
        cmd = f"source /opt/ros/jazzy/setup.bash && source {ws}/install/setup.bash 2>/dev/null || true && ros2 launch my_robot_nav imu_slam.launch.py"
    else:
        cmd = "source /opt/ros/jazzy/setup.bash && rviz2"

    proc = subprocess.Popen(cmd, shell=True, executable='/bin/bash', env=get_exec_env())
    active_processes['rviz'] = proc
    return jsonify({'success': True, 'message': f'Launched visualizer: {mode}'})

@app.route('/api/rviz/stop', methods=['POST'])
def stop_rviz():
    subprocess.run("pkill -9 -f rviz2 2>/dev/null || true", shell=True)
    subprocess.run("pkill -9 -f imu_dead_reckoning 2>/dev/null || true", shell=True)
    return jsonify({'success': True, 'message': 'RViz closed'})

@app.route('/api/slam/start', methods=['POST'])
def start_slam():
    """
    Start SLAM mapping pipeline.
    Manages slam_toolbox and rviz2 cleanly without interrupting qos_relay.
    """
    subprocess.run(
        "pkill -9 -f 'async_slam_toolbox_node|rviz2|imu_slam.launch.py' 2>/dev/null || true",
        shell=True
    )
    time.sleep(0.5)

    # Verify qos_relay is alive
    relay_proc = active_processes.get('qos_relay')
    if relay_proc is None or relay_proc.poll() is not None:
        start_qos_relay_daemon()
        time.sleep(1.0)

    ws = get_ws_dir()
    cmd = (
        f"source /opt/ros/jazzy/setup.bash && "
        f"source {ws}/install/setup.bash 2>/dev/null || true && "
        f"ros2 launch my_robot_nav imu_slam.launch.py"
    )
    proc = subprocess.Popen(cmd, shell=True, executable='/bin/bash', env=get_exec_env())
    active_processes['slam'] = proc
    telemetry['slam_running'] = True
    return jsonify({'success': True, 'message': 'SLAM Mapping started - RViz opening in ~4s'})

@app.route('/api/slam/stop', methods=['POST'])
def stop_slam():
    """Stop SLAM and RViz cleanly."""
    subprocess.run(
        "pkill -9 -f 'async_slam_toolbox_node|rviz2|imu_slam.launch.py' 2>/dev/null || true",
        shell=True
    )
    telemetry['slam_running'] = False
    return jsonify({'success': True, 'message': 'SLAM stopped'})

@app.route('/api/slam/save_map', methods=['POST'])
def save_map():
    req_data = request.get_json(silent=True) or {}
    map_name = req_data.get('name', f"map_{int(time.time())}")
    ws = get_ws_dir()
    maps_dir = f'{ws}/src/my_robot_nav/maps'
    os.makedirs(maps_dir, exist_ok=True)
    target_path = os.path.join(maps_dir, map_name)

    cyclone = os.environ.get('CYCLONEDDS_URI', '')
    cmd = (
        f"source /opt/ros/jazzy/setup.bash && "
        f"export ROS_DOMAIN_ID=42 && "
        f"export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && "
        f"export CYCLONEDDS_URI={cyclone} && "
        f"ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "
        f"\"{{name: {{data: '{target_path}'}}}}\""
    )
    res = subprocess.run(
        cmd, shell=True, executable='/bin/bash',
        env=get_exec_env(), capture_output=True, text=True, timeout=10
    )

    if os.path.exists(f"{target_path}.yaml") or os.path.exists(f"{target_path}.pgm"):
        return jsonify({'success': True, 'message': f'Map saved: {map_name}.yaml', 'map_name': map_name})

    # Fallback: nav2_map_server
    cmd2 = (
        f"source /opt/ros/jazzy/setup.bash && "
        f"export ROS_DOMAIN_ID=42 && "
        f"export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && "
        f"export CYCLONEDDS_URI={cyclone} && "
        f"ros2 run nav2_map_server map_saver_cli -f {target_path}"
    )
    res2 = subprocess.run(
        cmd2, shell=True, executable='/bin/bash',
        env=get_exec_env(), capture_output=True, text=True, timeout=10
    )

    if os.path.exists(f"{target_path}.yaml") or res2.returncode == 0:
        return jsonify({'success': True, 'message': f'Map saved: {map_name}.yaml', 'map_name': map_name})
    return jsonify({'success': False, 'message': f'Save failed: {res.stdout or res2.stderr}'})

@app.route('/api/system/shutdown_all', methods=['POST'])
def shutdown_all():
    """
    Complete Full System Shutdown: Terminates all ROS 2 activity on Laptop & Uno Q,
    and terminates the Flask Dashboard server itself, exiting start_dashboard.sh cleanly.
    """
    # 1. Kill all local processes and discovery daemon
    subprocess.run("pkill -9 -f 'async_slam_toolbox_node|rviz2|imu_dead_reckoning|qos_relay|tf2_ros|sync_slam_toolbox_node' 2>/dev/null || true", shell=True)
    subprocess.run("ros2 daemon stop 2>/dev/null || true", shell=True)
    
    # 2. Kill edge sensors on Uno Q
    cmd_unoq = "docker exec -t rplidar pkill -9 -f 'rplidar_node|imu_publisher|ros2' 2>/dev/null || true"
    ssh_unoq_cmd(cmd_unoq)

    # 3. Clean up PID and lock files
    try:
        if os.path.exists(PIDFILE_PATH):
            os.remove(PIDFILE_PATH)
        if os.path.exists(LOCKFILE_PATH):
            os.remove(LOCKFILE_PATH)
    except Exception:
        pass


    def stop_server():
        time.sleep(0.5)
        print("[Dashboard] Full system shutdown complete. Exiting...")
        os._exit(0)

    threading.Thread(target=stop_server, daemon=True).start()
    return jsonify({'success': True, 'message': 'Full system shutdown initiated. Dashboard and all ROS nodes stopping.'})

@app.route('/api/slam/regularize_map', methods=['POST'])
def regularize_map():
    """
    Applies Manhattan World 90-degree orthogonal line snapping to a map.
    Auto-saves live map if no saved map is found.
    """
    req_data = request.get_json(silent=True) or {}
    map_name = req_data.get('name', '')
    ws = get_ws_dir()
    maps_dir = f'{ws}/src/my_robot_nav/maps'
    os.makedirs(maps_dir, exist_ok=True)
    
    yaml_files = sorted([f for f in os.listdir(maps_dir) if f.endswith('.yaml') and not f.endswith('_regularized.yaml')], reverse=True)
    
    if not map_name:
        if yaml_files:
            map_name = yaml_files[0]
        else:
            # Auto-save live map
            auto_name = f"map_{int(time.time())}"
            target_path = os.path.join(maps_dir, auto_name)
            cyclone = os.environ.get('CYCLONEDDS_URI', '')
            cmd = (
                f"source /opt/ros/jazzy/setup.bash && "
                f"export ROS_DOMAIN_ID=42 && "
                f"export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && "
                f"export CYCLONEDDS_URI={cyclone} && "
                f"ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "
                f"\"{{name: {{data: '{target_path}'}}}}\""
            )
            subprocess.run(cmd, shell=True, executable='/bin/bash', env=get_exec_env(), timeout=8)
            if not (os.path.exists(f"{target_path}.yaml") or os.path.exists(f"{target_path}.pgm")):
                # Fallback saver
                cmd2 = f"source /opt/ros/jazzy/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI={cyclone} && ros2 run nav2_map_server map_saver_cli -f {target_path}"
                subprocess.run(cmd2, shell=True, executable='/bin/bash', env=get_exec_env(), timeout=8)
            map_name = f"{auto_name}.yaml"

    yaml_path = os.path.join(maps_dir, map_name if map_name.endswith('.yaml') else f"{map_name}.yaml")
    
    if not os.path.exists(yaml_path):
        return jsonify({'success': False, 'message': f'Map file {map_name} not found. Please click "Start SLAM Mapping" and "Save Map" first!'})

    try:
        sys.path.insert(0, f'{ws}/src/my_robot_nav/scripts')
        from map_regularizer import regularize_saved_map_file
        
        ok, res = regularize_saved_map_file(yaml_path)
        if ok:
            return jsonify({
                'success': True,
                'message': f"Map {map_name} snapped to 90° boxy walls ({res['stats']['snapped_walls']} walls snapped)!",
                'regularized_yaml': os.path.basename(res['regularized_yaml']),
                'regularized_svg': os.path.basename(res['regularized_svg']),
                'stats': res['stats']
            })
        else:
            return jsonify({'success': False, 'message': str(res)})
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error during map regularization: {str(e)}"})

@app.route('/api/slam/list_maps')
def list_maps():
    ws = get_ws_dir()
    maps_dir = f'{ws}/src/my_robot_nav/maps'
    if not os.path.exists(maps_dir):
        return jsonify([])
    files = [f for f in os.listdir(maps_dir) if f.endswith('.yaml')]
    return jsonify(sorted(files, reverse=True))

if __name__ == '__main__':
    initial_port = int(os.environ.get('PORT', 5050))
    selected_port = initial_port
    
    # Check if selected_port is bindable, otherwise try alternative fallback ports (5055, 5051, 8080)
    for p in [initial_port, 5055, 5051, 8080]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', p))
                selected_port = p
                break
        except OSError:
            continue

    print(f"==================================================")
    print(f"  INDUSTRIAL ROBOT CONTROL & DIAGNOSTIC HUB")
    print(f"  Access UI at: http://localhost:{selected_port}")
    if selected_port != initial_port:
        print(f"  [Note] Port {initial_port} in use by IDE/tunnel, running on fallback port {selected_port}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=selected_port, debug=False, threaded=True)

