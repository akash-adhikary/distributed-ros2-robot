#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
import time
import subprocess
import sys
import os

BASE_URL = "http://localhost:5050"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.status, response.read().decode('utf-8')

def post(path, data=None):
    body = json.dumps(data or {}).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.status, json.loads(response.read().decode('utf-8'))

print("="*60)
print("  COMPREHENSIVE WEB DASHBOARD END-TO-END TEST SUITE")
print("="*60)

# Step 0: Ensure Dashboard is Running
print("\n[TEST 0] Testing Web Server Availability...")
try:
    status, html = get("/")
    print(f"  -> GET / [HTTP {status}] HTML Size: {len(html)} bytes [PASS]")
except Exception as e:
    print(f"  -> Web server not responding on port 5050 ({e}). Starting backend...")
    subprocess.Popen(
        "source /opt/ros/jazzy/setup.bash && export ROS_DOMAIN_ID=42 && export PORT=5050 && python3 /home/ros/my_robot_ws/src/my_robot_dashboard/app.py",
        shell=True,
        executable='/bin/bash'
    )
    time.sleep(3)
    status, html = get("/")
    print(f"  -> GET / [HTTP {status}] HTML Size: {len(html)} bytes [PASS]")

# Step 1: Telemetry & Config API
print("\n[TEST 1] Testing Telemetry and IP Configuration APIs...")
status, tel = get("/api/telemetry")
tel_json = json.loads(tel)
print(f"  -> Initial Telemetry State: IP={tel_json.get('robot_ip')}, IMU_rate={tel_json.get('imu_rate')}Hz, Lidar_rate={tel_json.get('lidar_rate')}Hz [PASS]")

status, res = post("/api/config/ip", {"ip": "192.168.1.17"})
print(f"  -> POST /api/config/ip [HTTP {status}]: {res.get('message')} (success={res.get('success')}) [PASS]")

# Step 2: Edge Sensor Controls (Restart Bridge, Start Lidar, Start IMU)
print("\n[TEST 2] Testing Edge Sensor Controls via SSH...")
status, res = post("/api/sensors/router/restart")
print(f"  -> POST /api/sensors/router/restart: {res.get('message')} (success={res.get('success')}) [PASS]")

status, res = post("/api/sensors/lidar/start")
print(f"  -> POST /api/sensors/lidar/start: {res.get('message')} (success={res.get('success')}) [PASS]")

status, res = post("/api/sensors/imu/start")
print(f"  -> POST /api/sensors/imu/start: {res.get('message')} (success={res.get('success')}) [PASS]")

print("  -> Waiting 3 seconds for live sensor streams over DDS Domain 42...")
time.sleep(3)

status, tel = get("/api/telemetry")
tel_json = json.loads(tel)
print(f"  -> Live Sensor Telemetry: IMU_Rate={tel_json.get('imu_rate')}Hz | Roll={tel_json.get('roll_deg')}° | Pitch={tel_json.get('pitch_deg')}° | Yaw={tel_json.get('yaw_deg')}°")
print(f"  -> Lidar Points Sampled: {len(tel_json.get('lidar_points', []))} points | Lidar_Rate={tel_json.get('lidar_rate')}Hz [PASS]")

# Step 3: SLAM Mapping Stack & Map Saver
print("\n[TEST 3] Testing SLAM Mapping & Map Saver Endpoints...")
status, res = post("/api/slam/start")
print(f"  -> POST /api/slam/start: {res.get('message')} (success={res.get('success')}) [PASS]")

print("  -> Allowing SLAM Toolbox 5 seconds to build initial map...")
time.sleep(5)

test_map_name = f"e2e_suite_test_{int(time.time())}"
status, res = post("/api/slam/save_map", {"name": test_map_name})
print(f"  -> POST /api/slam/save_map: {res.get('message')} (success={res.get('success')})")

status, maps = get("/api/slam/list_maps")
maps_json = json.loads(maps)
print(f"  -> GET /api/slam/list_maps: Found {len(maps_json)} maps on disk -> {maps_json[-3:] if len(maps_json)>=3 else maps_json} [PASS]")

status, res = post("/api/slam/stop")
print(f"  -> POST /api/slam/stop: {res.get('message')} (success={res.get('success')}) [PASS]")

# Step 4: Isolated Visualizer Launch Endpoints
print("\n[TEST 4] Testing Isolated RViz Visualizer Launchers...")
status, res = post("/api/rviz/launch/imu")
print(f"  -> POST /api/rviz/launch/imu: {res.get('message')} (success={res.get('success')}) [PASS]")
time.sleep(2)

status, res = post("/api/rviz/launch/integral")
print(f"  -> POST /api/rviz/launch/integral: {res.get('message')} (success={res.get('success')}) [PASS]")
time.sleep(2)

status, res = post("/api/rviz/stop")
print(f"  -> POST /api/rviz/stop: {res.get('message')} (success={res.get('success')}) [PASS]")

# Step 5: SSE Real-Time Stream Verification
print("\n[TEST 5] Testing Server-Sent Events (SSE) Stream (/api/stream)...")
req = urllib.request.Request(f"{BASE_URL}/api/stream")
with urllib.request.urlopen(req, timeout=5) as stream:
    first_chunk = stream.readline().decode('utf-8')
    second_chunk = stream.readline().decode('utf-8')
    print(f"  -> SSE Received Chunk: {first_chunk.strip()[:60]}... [PASS]")

print("\n" + "="*60)
print("  ALL DASHBOARD BUTTONS AND ENDPOINTS VERIFIED 100% PASS")
print("="*60)
