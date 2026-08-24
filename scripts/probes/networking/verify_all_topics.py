#!/usr/bin/env python3
"""
Probe: Automated Distributed Topic & Rate Verification over CycloneDDS
Usage: python3 scripts/probes/networking/verify_all_topics.py
"""
import subprocess, sys

def run_cmd(cmd):
    full_cmd = f"""docker exec -t thirsty_burnell bash -c '
        source /opt/ros/jazzy/setup.bash
        export ROS_DOMAIN_ID=42
        export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
        export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml
        {cmd}
    '"""
    return subprocess.run(full_cmd, shell=True, capture_output=True, text=True)

print("="*60)
print("1. DISCOVERING ROS 2 TOPICS ON DOMAIN 42...")
print("="*60)
res = run_cmd("timeout 4 ros2 topic list")
print(res.stdout)

print("="*60)
print("2. MEASURING /scan TOPIC FREQUENCY (RPLidar)...")
print("="*60)
res = run_cmd("timeout 4 ros2 topic hz /scan")
print(res.stdout)

print("="*60)
print("3. MEASURING /imu/data TOPIC FREQUENCY (BNO086)...")
print("="*60)
res = run_cmd("timeout 4 ros2 topic hz /imu/data")
print(res.stdout)

print("="*60)
print("4. SAMPLE /imu/data PAYLOAD:")
print("="*60)
res = run_cmd("timeout 4 ros2 topic echo /imu/data --once")
print(res.stdout)
print("="*60)
print("DIAGNOSTIC TEST COMPLETE.")
