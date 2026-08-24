#!/usr/bin/env python3
import os
import sys
import json
import time
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, LaserScan

# Configure CycloneDDS
os.environ['ROS_DOMAIN_ID'] = '42'
os.environ['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'
if os.path.exists('/home/ros/my_robot_ws/cyclonedds.xml'):
    os.environ['CYCLONEDDS_URI'] = 'file:///home/ros/my_robot_ws/cyclonedds.xml'
elif os.path.exists('/home/bliss/my_robot_ws/cyclonedds.xml'):
    os.environ['CYCLONEDDS_URI'] = 'file:///home/bliss/my_robot_ws/cyclonedds.xml'

TELEMETRY_FILE = '/tmp/robot_telemetry.json'

telemetry = {
    'robot_ip': os.environ.get('UNOQ_IP', '192.168.1.17'),
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
last_dump_time = 0.0

class TelemetryBridge(Node):
    def __init__(self):
        super().__init__('telemetry_bridge_node')
        self.sub_imu = self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.create_timer(0.033, self.timer_cb) # 30 Hz atomic disk dump
        self.get_logger().info("Dedicated Telemetry Bridge running on Domain 42.")

    def imu_cb(self, msg):
        global telemetry, imu_msg_times
        now = time.time()
        imu_msg_times.append(now)
        imu_msg_times = [t for t in imu_msg_times if now - t <= 2.0]
        telemetry['imu_rate'] = round(len(imu_msg_times) / 2.0, 1)
        telemetry['imu_running'] = (telemetry['imu_rate'] > 5.0)

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
        global telemetry, lidar_msg_times
        now = time.time()
        lidar_msg_times.append(now)
        lidar_msg_times = [t for t in lidar_msg_times if now - t <= 2.0]
        telemetry['lidar_rate'] = round(len(lidar_msg_times) / 2.0, 1)
        telemetry['lidar_running'] = (telemetry['lidar_rate'] > 2.0)

        step = max(1, len(msg.ranges) // 100)
        points = []
        for i in range(0, len(msg.ranges), step):
            r = msg.ranges[i]
            if msg.range_min < r < msg.range_max:
                angle = msg.angle_min + i * msg.angle_increment
                points.append([round(angle, 3), round(r, 2)])
        telemetry['lidar_points'] = points

    def timer_cb(self):
        try:
            tmp_path = f"{TELEMETRY_FILE}.tmp"
            with open(tmp_path, 'w') as f:
                json.dump(telemetry, f)
            os.replace(tmp_path, TELEMETRY_FILE)
        except Exception:
            pass

def main(args=None):
    rclpy.init(args=args)
    bridge = TelemetryBridge()
    rclpy.spin(bridge)
    bridge.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
