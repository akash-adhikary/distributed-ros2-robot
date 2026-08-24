#!/usr/bin/env python3
import os
import sys
import json
import time
import pexpect
import subprocess
import socket
import threading
from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS

TELEMETRY_FILE = '/tmp/robot_telemetry.json'

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

robot_config = {
    'ip': os.environ.get('UNOQ_IP', '192.168.1.17'),
    'user': 'arduino',
    'pass': 'Askaban78@#'
}

active_processes = {}

def ensure_telemetry_bridge():
    """Supervisor thread to guarantee telemetry_bridge.py is always running"""
    ws_dir = '/home/ros/my_robot_ws' if os.path.exists('/home/ros/my_robot_ws') else '/home/bliss/my_robot_ws'
    bridge_path = os.path.join(ws_dir, 'src/my_robot_dashboard/telemetry_bridge.py')
    
    while True:
        if 'bridge' not in active_processes or active_processes['bridge'].poll() is not None:
            env = get_exec_env()
            cmd = f"source /opt/ros/jazzy/setup.bash && source {ws_dir}/install/setup.bash 2>/dev/null || true && python3 {bridge_path}"
            proc = subprocess.Popen(cmd, shell=True, executable='/bin/bash', env=env)
            active_processes['bridge'] = proc
        time.sleep(2)

def get_latest_telemetry():
    if os.path.exists(TELEMETRY_FILE):
        try:
            with open(TELEMETRY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
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

def ssh_unoq_cmd(cmd, timeout=15):
    ip = robot_config['ip']
    try:
        child = pexpect.spawn(f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 {robot_config['user']}@{ip}", encoding='utf-8')
        res = child.expect([r'[pP]assword:', pexpect.TIMEOUT, pexpect.EOF], timeout=5)
        if res != 0:
            return False, f"Could not connect to {ip} (Timeout / Unreachable)"
        child.sendline(robot_config['pass'])
        child.expect([r'\$ '], timeout=8)
        child.sendline(cmd)
        child.expect([r'\$ '], timeout=timeout)
        output = child.before
        child.sendline("exit")
        child.expect(pexpect.EOF)
        return True, output
    except Exception as e:
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

# Start supervisor thread
supervisor_thread = threading.Thread(target=ensure_telemetry_bridge, daemon=True)
supervisor_thread.start()

# ----------------- REST API ROUTES ----------------- #

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config/ip', methods=['POST'])
def set_ip():
    new_ip = request.json.get('ip', '').strip()
    if new_ip:
        robot_config['ip'] = new_ip
        return jsonify({'success': True, 'message': f'Robot IP updated to {new_ip}'})
    return jsonify({'success': False, 'message': 'Invalid IP address'})

@app.route('/api/telemetry')
def get_telemetry():
    return jsonify(get_latest_telemetry())

@app.route('/api/stream')
def sse_stream():
    def event_stream():
        while True:
            try:
                data = json.dumps(get_latest_telemetry())
                yield f"data: {data}\n\n"
                time.sleep(0.04) # Steady 25 FPS SSE stream with zero GIL contention
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
    # Clean up previous SLAM instances without killing telemetry bridge
    subprocess.run("pkill -9 -f 'async_slam_toolbox_node|ekf_node|qos_relay|rviz2|imu_slam.launch.py' 2>/dev/null || true", shell=True)
    
    ws_dir = '/home/ros/my_robot_ws' if os.path.exists('/home/ros/my_robot_ws') else '/home/bliss/my_robot_ws'
    cmd = f"source /opt/ros/jazzy/setup.bash && source {ws_dir}/install/setup.bash 2>/dev/null || true && ros2 launch my_robot_nav imu_slam.launch.py"
    proc = subprocess.Popen(cmd, shell=True, executable='/bin/bash', env=get_exec_env())
    active_processes['slam'] = proc
    return jsonify({'success': True, 'message': 'SLAM Mapping pipeline & RViz window launched'})

@app.route('/api/slam/stop', methods=['POST'])
def stop_slam():
    global active_processes
    subprocess.run("pkill -9 -f 'async_slam_toolbox_node|ekf_node|qos_relay|rviz2|imu_slam.launch.py' 2>/dev/null || true", shell=True)
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
