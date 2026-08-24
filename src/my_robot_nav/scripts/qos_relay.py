#!/usr/bin/env python3
"""
QoS Relay & Tilt-Compensated SLAM Bridge
========================================
Responsibilities:
  1. Publish continuous 50 Hz odom->base_link dynamic TF using smoothed planar yaw.
  2. Publish static sensor mounting geometry TFs (base_link -> laser/imu).
  3. Tilt-Aware Scan Filtering: Detects handheld tilt from IMU orientation.
     Filters out laser rays that intersect floor/ceiling planes when tilted.
  4. Preserves original timestamps to guarantee zero-latency TF lookup.
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

        # Subscriptions & Publishers
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.pub_scan = self.create_publisher(LaserScan, '/scan_reliable', 10)

        self.sub_imu = self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)
        self.pub_imu = self.create_publisher(Imu, '/imu_reliable', 10)

        # Static Transforms for Sensor Mounting Geometry
        self.tf_static_broadcaster = StaticTransformBroadcaster(self)
        self.publish_static_transforms()

        # Dynamic Odometry Transform Broadcaster (odom -> base_link)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Motion & Tilt Tracking
        self._yaw = 0.0
        self._roll = 0.0
        self._pitch = 0.0
        self._tilt_deg = 0.0
        self._smooth_alpha = 0.35

        # 50 Hz continuous odom->base_link broadcast
        self.create_timer(0.02, self.broadcast_odom_tf)

        self.get_logger().info('QoS Relay: odom->base_link @ 50Hz with Tilt-Compensated Scan Gating.')

    def publish_static_transforms(self):
        """Publish static sensor geometry transforms once (latched)."""
        now = self.get_clock().now().to_msg()

        t1 = TransformStamped()
        t1.header.stamp = now
        t1.header.frame_id = 'base_link'
        t1.child_frame_id = 'laser'
        t1.transform.translation.z = 0.1
        t1.transform.rotation.w = 1.0

        t2 = TransformStamped()
        t2.header.stamp = now
        t2.header.frame_id = 'base_link'
        t2.child_frame_id = 'laser_frame'
        t2.transform.translation.z = 0.1
        t2.transform.rotation.w = 1.0

        t3 = TransformStamped()
        t3.header.stamp = now
        t3.header.frame_id = 'base_link'
        t3.child_frame_id = 'imu_link'
        t3.transform.translation.z = 0.05
        t3.transform.rotation.w = 1.0

        self.tf_static_broadcaster.sendTransform([t1, t2, t3])

    def broadcast_odom_tf(self):
        """Broadcast continuous 50 Hz odom->base_link planar transform."""
        now = self.get_clock().now().to_msg()
        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.0

        half_yaw = self._yaw * 0.5
        t.transform.rotation.w = math.cos(half_yaw)
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = math.sin(half_yaw)

        self.tf_broadcaster.sendTransform(t)

    def scan_cb(self, msg: LaserScan):
        """
        Gates tilted rays to prevent floor/ceiling hits from warping 2D SLAM maps.
        """
        # If tilt is moderate (> 7.5 deg), filter points whose vertical deviation hits floor/ceiling
        if self._tilt_deg > 7.5:
            tilt_rad = math.radians(self._tilt_deg)
            sin_tilt = math.sin(tilt_rad)
            filtered_ranges = list(msg.ranges)
            
            for i, r in enumerate(filtered_ranges):
                if msg.range_min < r < msg.range_max:
                    # Vertical height offset at distance r
                    z_offset = abs(r * sin_tilt)
                    if z_offset > 0.40: # ray hits ceiling or floor (>40cm height change)
                        filtered_ranges[i] = float('inf')
            
            msg.ranges = filtered_ranges

        self.pub_scan.publish(msg)

    def imu_cb(self, msg: Imu):
        """Extracts yaw, roll, pitch and updates orientation state."""
        w = msg.orientation.w
        x = msg.orientation.x
        y = msg.orientation.y
        z = msg.orientation.z

        sinr_cosp = 2.0 * (w * x + y * z)
        cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
        raw_roll = math.atan2(sinr_cosp, cosr_cosp)

        sinp = 2.0 * (w * y - z * x)
        raw_pitch = math.asin(max(-1.0, min(1.0, sinp)))

        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        raw_yaw = math.atan2(siny_cosp, cosy_cosp)

        # Smooth orientation
        self._yaw = self._smooth_alpha * raw_yaw + (1.0 - self._smooth_alpha) * self._yaw
        self._roll = self._smooth_alpha * raw_roll + (1.0 - self._smooth_alpha) * self._roll
        self._pitch = self._smooth_alpha * raw_pitch + (1.0 - self._smooth_alpha) * self._pitch

        self._tilt_deg = math.degrees(math.sqrt(self._roll**2 + self._pitch**2))
        self.pub_imu.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    relay = QoSRelay()
    rclpy.spin(relay)
    relay.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
