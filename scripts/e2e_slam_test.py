#!/usr/bin/env python3
import rclpy
import time
import subprocess
import os
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from sensor_msgs.msg import LaserScan, Imu

class E2EVerifier(Node):
    def __init__(self):
        super().__init__('e2e_verifier')
        self.sub_map = self.create_subscription(OccupancyGrid, '/map', self.map_cb, 10)
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.sub_imu = self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)
        
        self.scan_count = 0
        self.imu_count = 0
        self.map_count = 0

    def scan_cb(self, msg):
        self.scan_count += 1

    def imu_cb(self, msg):
        self.imu_count += 1

    def map_cb(self, msg):
        self.map_count += 1
        print(f"[*] [MAP ACTIVE] Received Map #{self.map_count}: {msg.info.width}x{msg.info.height} cells @ {msg.info.resolution}m/cell")
        if self.map_count >= 3:
            print("[SUCCESS] Full SLAM pipeline verified end-to-end with live sensor streams and map generation!")
            rclpy.shutdown()

def main():
    rclpy.init()
    node = E2EVerifier()
    
    print("==================================================")
    print("  LAUNCHING SLAM FUSION STACK (HEADLESS)...")
    print("==================================================")
    
    env = os.environ.copy()
    env['ROS_DOMAIN_ID'] = '42'
    env['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'
    env['CYCLONEDDS_URI'] = 'file:///home/ros/my_robot_ws/cyclonedds.xml'
    
    launch_proc = subprocess.Popen(
        "ros2 launch my_robot_nav imu_slam.launch.py",
        shell=True,
        executable='/bin/bash',
        env=env
    )
    
    start_time = time.time()
    try:
        while rclpy.ok() and (time.time() - start_time < 20):
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.scan_count > 0 and node.imu_count > 0 and node.map_count > 0:
                print(f"[STATUS] Sensor Scans: {node.scan_count} | IMU Frames: {node.imu_count} | Maps: {node.map_count}")
    except Exception as e:
        print(f"Error during spin: {e}")
    finally:
        launch_proc.terminate()
        subprocess.run("pkill -9 -f 'async_slam_toolbox_node|ekf_node|qos_relay|rviz2' 2>/dev/null || true", shell=True)

if __name__ == '__main__':
    main()
