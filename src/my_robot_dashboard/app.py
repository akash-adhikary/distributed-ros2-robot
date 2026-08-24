#!/usr/bin/env python3
import os
import sys
import json
import time
import math
import pexpect
import threading
import subprocess
import socket
from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS

# Configure ROS 2 CycloneDDS environment
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
    'unoq_online': False,
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

class DashboardRosNode(Node):
    def __init__(self):
        super().__init__('dashboard_backend_node')
        self.sub_imu = self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.get_logger().info("Dashboard ROS 2 Subscriber Node initialized on Domain 42.")

    def imu_cb(self, msg):
        global telemetry, imu_msg_times, last_imu_update
        now = time.time()
        imu_msg_times.append(now)
        imu_msg_times = [t for t in imu_msg_times if now - t <= 2.0]
        telemetry['imu_rate'] = round(len(imu_msg_times) / 2.0, 1)
        telemetry['imu_running'] = (telemetry['imu_rate'] > 5.0)

        # Cap UI updates to 30 Hz
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

        telemetry['acc'] = {'x': round(msg.linear_acceleration.x, 2), 'y': round(msg.linear_acceleration.y, 2), 'z': round(msg.linear_acceleration.z, 2)}
        telemetry['gyro'] = {'x': round(msg.angular_velocity.x, 2), 'y': round(msg.angular_velocity.y, 2), 'z': round(msg.angular_velocity.z, 2)}

    def scan_cb(self, msg):
        global telemetry, lidar_msg_times, last_scan_update
        now = time.time()
        lidar_msg_times.append(now)
        lidar_msg_times = [t for t in lidar_msg_times if now - t <= 2.0]
        telemetry['lidar_rate'] = round(len(lidar_msg_times) / 2.0, 1)
        telemetry['lidar_running'] = (telemetry['lidar_rate'] > 2.0)

        # Cap radar updates to 10 Hz
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

def non_blocking_ros_spin():
    rclpy.init()
    node = DashboardRosNode()
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.008)
        time.sleep(0.01) # Yields GIL to Flask threads smoothly!
    node.destroy_node()
    rclpy.shutdown()

ros_thread = threading.Thread(target=non_blocking_ros_spin, daemon=True)
ros_thread.start()

def ssh_unoq_cmd(cmd, timeout=15):
    ip = robot_config['ip']
    try:
        child = pexpect.spawn(f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 {robot_config['user']}@{ip}", encoding='utf-8')
        res = child.expect([r'[pP]assword:', pexpect.TIMEOUT, pexpect.EOF], timeout=5)
        if res != 0:
            telemetry['unoq_online'] = False
            return False, f"Could not connect to {ip} (Timeout / Unreachable)"
        child.sendline(robot_config['pass'])
        child.expect([r'\$ '], timeout=8)
        child.sendline(cmd)
        child.expect([r'\$ '], timeout=timeout)
        output = child.before
        child.sendline("exit")
        child.expect(pexpect.EOF)
        telemetry['unoq_online'] = True
        return True, output
    except Exception as e:
        telemetry['unoq_online'] = False
        return False, str(e)

def get_exec_env():
    env = os.environ.copy()
    env['DISPLAY'] = os.environ.get('DISPLAY', ':0')
    env['QT_X11_NO_MITSHM'] = '1'
    env['ROS_DOMAIN_ID'] = '42'
    env['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'
    if os.path.exists('/home/ros/my_robot_ws/cyclonedds.xml'):
        env['CYCLONEDDS_URI'] = 'file:///home/ros/my_robot_ws/cyclonedds.xml'
    elif os.path.exists('/home/bliss/my_robot_ws/cyclonedds.xml'):
        env['CYCLONEDDS_URI'] = 'file:///home/bliss/my_robot_ws/cyclonedds.xml'
    return env

# ----------------- REST API ROUTES ----------------- #

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config/ip', methods=['POST'])
def set_ip():
    new_ip = request.json.get('ip', '').strip()
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
                time.sleep(0.04) # Steady 25 FPS SSE stream
            except GeneratorExit:
                break
            except Exception:
                time.sleep(0.05)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/api/sensors/lidar/start', methods=['POST'])
def start_lidar():
    cmd = """
    echo 'Askaban78@#' | sudo -S chmod 666 /dev/ttyUSB0 2>/dev/null || true
    docker start rplidar
    docker exec -t rplidar pkill -f 'rplidar_node' 2>/dev/null || true
    docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0'
    """
    success, msg = ssh_unoq_cmd(cmd)
    return jsonify({'success': success, 'message': 'RPLidar C1 launch command issued' if success else msg})

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
    docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && python3 /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'
    """
    success, msg = ssh_unoq_cmd(cmd)
    return jsonify({'success': success, 'message': 'BNO086 100Hz IMU Publisher launch command issued' if success else msg})

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
    return jsonify({'success': success, 'message': 'Arduino router bridge restarted' if success else msg})

@app.route('/api/sensors/unoq/reboot', methods=['POST'])
def reboot_unoq():
    cmd = "echo 'Askaban78@#' | sudo -S reboot"
    ssh_unoq_cmd(cmd, timeout=5)
    telemetry['unoq_online'] = False
    return jsonify({'success': True, 'message': 'Reboot signal sent to Uno Q hardware'})

@app.route('/api/rviz/launch/<mode>', methods=['POST'])
def launch_rviz(mode):
    global active_processes
    subprocess.run("pkill -9 -f rviz2 2>/dev/null || true", shell=True)
    subprocess.run("pkill -9 -f imu_dead_reckoning 2>/dev/null || true", shell=True)

    ws_dir = '/home/ros/my_robot_ws' if os.path.exists('/home/ros/my_robot_ws') else '/home/bliss/my_robot_ws'
    
    if mode == 'imu':
        cmd = f"bash {ws_dir}/view_imu.sh"
    elif mode == 'integral':
        cmd = f"bash {ws_dir}/view_imu_integral.sh"
    elif mode == 'slam':
        cmd = f"source /opt/ros/jazzy/setup.bash && source {ws_dir}/install/setup.bash 2>/dev/null || true && ros2 launch my_robot_nav imu_slam.launch.py"
    else:
        cmd = f"source /opt/ros/jazzy/setup.bash && rviz2"

    proc = subprocess.Popen(cmd, shell=True, executable='/bin/bash', env=get_exec_env())
    active_processes['rviz'] = proc
    return jsonify({'success': True, 'message': f'Launched visualizer for mode: {mode}'})

@app.route('/api/rviz/stop', methods=['POST'])
def stop_rviz():
    subprocess.run("pkill -9 -f rviz2 2>/dev/null || true", shell=True)
    subprocess.run("pkill -9 -f imu_dead_reckoning 2>/dev/null || true", shell=True)
    return jsonify({'success': True, 'message': 'All RViz visualizers closed'})

@app.route('/api/slam/start', methods=['POST'])
def start_slam():
    global active_processes
    subprocess.run("pkill -9 -f 'async_slam_toolbox_node|ekf_node|qos_relay|rviz2|imu_slam.launch.py' 2>/dev/null || true", shell=True)
    
    ws_dir = '/home/ros/my_robot_ws' if os.path.exists('/home/ros/my_robot_ws') else '/home/bliss/my_robot_ws'
    cmd = f"source /opt/ros/jazzy/setup.bash && source {ws_dir}/install/setup.bash 2>/dev/null || true && ros2 launch my_robot_nav imu_slam.launch.py"
    proc = subprocess.Popen(cmd, shell=True, executable='/bin/bash', env=get_exec_env())
    active_processes['slam'] = proc
    telemetry['slam_running'] = True
    return jsonify({'success': True, 'message': 'SLAM Mapping pipeline & RViz window launched'})

@app.route('/api/slam/stop', methods=['POST'])
def stop_slam():
    global active_processes
    subprocess.run("pkill -9 -f 'async_slam_toolbox_node|ekf_node|qos_relay|rviz2|imu_slam.launch.py' 2>/dev/null || true", shell=True)
    telemetry['slam_running'] = False
    return jsonify({'success': True, 'message': 'SLAM Mapping pipeline stopped'})

@app.route('/api/slam/save_map', methods=['POST'])
def save_map():
    map_name = request.json.get('name', f"map_{int(time.time())}") if request.is_json else f"map_{int(time.time())}"
    save_dir = '/home/ros/my_robot_ws/src/my_robot_nav/maps' if os.path.exists('/home/ros/my_robot_ws') else '/home/bliss/my_robot_ws/src/my_robot_nav/maps'
    os.makedirs(save_dir, exist_ok=True)
    target_path = os.path.join(save_dir, map_name)

    cmd = f"source /opt/ros/jazzy/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI={os.environ.get('CYCLONEDDS_URI', '')} && ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap \"{{name: {{data: '{target_path}'}}}}\""
    res = subprocess.run(cmd, shell=True, executable='/bin/bash', env=get_exec_env(), capture_output=True, text=True, timeout=8)
    
    if "result=0" in res.stdout or "result: 0" in res.stdout or os.path.exists(f"{target_path}.yaml") or os.path.exists(f"{target_path}.pgm"):
        return jsonify({'success': True, 'message': f'Map saved successfully to {target_path}.yaml', 'map_name': map_name})
    
    cmd_nav2 = f"source /opt/ros/jazzy/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI={os.environ.get('CYCLONEDDS_URI', '')} && ros2 run nav2_map_server map_saver_cli -f {target_path}"
    res2 = subprocess.run(cmd_nav2, shell=True, executable='/bin/bash', env=get_exec_env(), capture_output=True, text=True, timeout=8)
    
    if os.path.exists(f"{target_path}.yaml") or res2.returncode == 0:
        return jsonify({'success': True, 'message': f'Map saved successfully to {target_path}.yaml', 'map_name': map_name})
    return jsonify({'success': False, 'message': f'Save failed: {res.stdout or res2.stderr}'})

@app.route('/api/slam/list_maps')
def list_maps():
    maps_dir = '/home/ros/my_robot_ws/src/my_robot_nav/maps' if os.path.exists('/home/ros/my_robot_ws') else '/home/bliss/my_robot_ws/src/my_robot_nav/maps'
    if not os.path.exists(maps_dir):
        return jsonify([])
    files = [f for f in os.listdir(maps_dir) if f.endswith('.yaml')]
    return jsonify(files)

def find_available_port(start_port=5050):
    for p in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) != 0:
                return p
    return start_port

if __name__ == '__main__':
    default_port = int(os.environ.get('PORT', 5050))
    port = find_available_port(default_port)
    print(f"==================================================")
    print(f"  ROBOT CONTROL & DIAGNOSTIC DASHBOARD ONLINE")
    print(f"  Access UI at: http://localhost:{port}")
    print(f"==================================================")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
