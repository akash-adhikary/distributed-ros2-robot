#!/usr/bin/env python3
"""Waits for slam_toolbox to start, then triggers configure + activate."""
import subprocess, time, sys

time.sleep(5)  # Wait for slam_toolbox to fully initialize

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"[lifecycle_activator] {cmd} -> {r.stdout.strip()}")
    return r.returncode == 0

run("ros2 lifecycle set /slam_toolbox configure")
time.sleep(2)
run("ros2 lifecycle set /slam_toolbox activate")
print("[lifecycle_activator] SLAM Toolbox activated successfully!")

# Keep alive so launch doesn't think we crashed
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    sys.exit(0)
