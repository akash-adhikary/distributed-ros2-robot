#!/usr/bin/env python3
"""
QoS Relay Node - Distributed Robot SLAM Bridge
===============================================
Responsibilities:
  1. Publish continuous 50 Hz odom->base_link dynamic TF (ensures RViz never sees missing frame)
  2. Publish static TFs: base_link->laser, base_link->laser_frame, base_link->imu_link
  3. Pass-through /scan and /imu/data as /scan_reliable and /imu_reliable WITHOUT re-stamping
     (re-stamping causes slam_toolbox to reject scans due to timestamp/TF lookup mismatch)

CRITICAL: Do NOT re-stamp message headers. slam_toolbox uses the scan timestamp to
          look up the odom->base_link TF. If we re-stamp, the TF lookup fails.
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Imu
from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
from tf2_ros.transform_broadcaster import TransformBroadcaster
import math

class QoSRelay(Node):
    def __init__(self):
        super().__init__('qos_relay')

        # Subscribe /scan with depth 5 (RELIABLE matches rplidar_node's RELIABLE publisher)
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.pub_scan = self.create_publisher(LaserScan, '/scan_reliable', 10)

        # Subscribe /imu/data
        self.sub_imu = self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)
        self.pub_imu = self.create_publisher(Imu, '/imu_reliable', 10)

        # Static Transforms for Sensor Mounting Geometry
        self.tf_static_broadcaster = StaticTransformBroadcaster(self)
        self.publish_static_transforms()

        # Dynamic Odometry Transform Broadcaster (odom -> base_link)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Filtered yaw heading from IMU (planar 2D mode)
        self._yaw = 0.0
        self._smooth_alpha = 0.3  # exponential smoothing

        # 50 Hz continuous odom->base_link broadcast
        self.create_timer(0.02, self.broadcast_odom_tf)

        self.get_logger().info('QoS Relay: odom->base_link @ 50Hz, static TFs published.')

    def publish_static_transforms(self):
        """Publish static sensor geometry transforms once (latched)."""
        now = self.get_clock().now().to_msg()

        # base_link -> laser (RPLidar mounted 10cm above base)
        t1 = TransformStamped()
        t1.header.stamp = now
        t1.header.frame_id = 'base_link'
        t1.child_frame_id = 'laser'
        t1.transform.translation.z = 0.1
        t1.transform.rotation.w = 1.0

        # base_link -> laser_frame (alias for rplidar_ros compatibility)
        t2 = TransformStamped()
        t2.header.stamp = now
        t2.header.frame_id = 'base_link'
        t2.child_frame_id = 'laser_frame'
        t2.transform.translation.z = 0.1
        t2.transform.rotation.w = 1.0

        # base_link -> imu_link (BNO086 mounted 5cm above base)
        t3 = TransformStamped()
        t3.header.stamp = now
        t3.header.frame_id = 'base_link'
        t3.child_frame_id = 'imu_link'
        t3.transform.translation.z = 0.05
        t3.transform.rotation.w = 1.0

        self.tf_static_broadcaster.sendTransform([t1, t2, t3])

    def broadcast_odom_tf(self):
        """
        Broadcast odom->base_link at 50Hz.
        Uses current clock - NO forward time buffering, as that causes TF extrapolation
        warnings in slam_toolbox. slam_toolbox uses transform_timeout param instead.
        """
        now = self.get_clock().now().to_msg()
        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.0

        # Planar yaw from filtered IMU heading
        half_yaw = self._yaw * 0.5
        t.transform.rotation.w = math.cos(half_yaw)
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = math.sin(half_yaw)

        self.tf_broadcaster.sendTransform(t)

    def scan_cb(self, msg):
        """
        Pass-through LaserScan WITHOUT re-stamping.
        slam_toolbox MUST receive the original scan timestamp to correctly
        look up odom->base_link in its TF buffer.
        """
        self.pub_scan.publish(msg)

    def imu_cb(self, msg):
        """
        Pass-through IMU data. Update internal yaw estimate with exponential smoothing.
        """
        w = msg.orientation.w
        x = msg.orientation.x
        y = msg.orientation.y
        z = msg.orientation.z

        # Extract yaw from quaternion
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        raw_yaw = math.atan2(siny_cosp, cosy_cosp)

        # Exponential smoothing to reduce jitter
        self._yaw = self._smooth_alpha * raw_yaw + (1.0 - self._smooth_alpha) * self._yaw

        self.pub_imu.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    relay = QoSRelay()
    rclpy.spin(relay)
    relay.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
