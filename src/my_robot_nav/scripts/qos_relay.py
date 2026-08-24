#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Imu
from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster
from tf2_ros.transform_broadcaster import TransformBroadcaster
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import math

def quat_slerp(q0, q1, t):
    """Spherical linear interpolation between two quaternions [w, x, y, z]"""
    dot = q0[0]*q1[0] + q0[1]*q1[1] + q0[2]*q1[2] + q0[3]*q1[3]
    if dot < 0.0:
        q1 = [-q1[0], -q1[1], -q1[2], -q1[3]]
        dot = -dot
        
    if dot > 0.9995:
        result = [q0[i] + t * (q1[i] - q0[i]) for i in range(4)]
        norm = math.sqrt(sum(x*x for x in result))
        return [x / norm for x in result]
        
    theta_0 = math.acos(max(-1.0, min(1.0, dot)))
    sin_theta_0 = math.sin(theta_0)
    theta = theta_0 * t
    sin_theta = math.sin(theta)
    
    s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
    s1 = sin_theta / sin_theta_0
    
    return [s0 * q0[i] + s1 * q1[i] for i in range(4)]

class QoSRelay(Node):
    def __init__(self):
        super().__init__('qos_relay')
        
        # QoS Profiles
        sub_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        pub_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.pub_scan = self.create_publisher(LaserScan, '/scan_reliable', 10)
        
        self.sub_imu = self.create_subscription(Imu, '/imu/data', self.imu_cb, 10)
        self.pub_imu = self.create_publisher(Imu, '/imu_reliable', 10)
        
        # Static Transforms for Sensor Mounting Geometry
        self.tf_static_broadcaster = StaticTransformBroadcaster(self)
        self.publish_static_transforms()
        
        # Dynamic Odometry Transform Broadcaster (odom -> base_link)
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Jitter filter state
        self.filt_quat = [1.0, 0.0, 0.0, 0.0]
        self.quat_smooth_alpha = 0.35
        self.max_angular_jump = 0.6
        
        # 50 Hz continuous broadcast timer ensuring odom frame is ALWAYS active
        self.create_timer(0.02, self.broadcast_odom_tf)
        
        self.get_logger().info('QoS Relay active: Broadcasting continuous odom -> base_link and static sensor TFs.')

    def publish_static_transforms(self):
        now = self.get_clock().now().to_msg()
        
        # base_link -> laser
        t1 = TransformStamped()
        t1.header.stamp = now
        t1.header.frame_id = 'base_link'
        t1.child_frame_id = 'laser'
        t1.transform.translation.z = 0.1
        t1.transform.rotation.w = 1.0
        
        # base_link -> laser_frame
        t2 = TransformStamped()
        t2.header.stamp = now
        t2.header.frame_id = 'base_link'
        t2.child_frame_id = 'laser_frame'
        t2.transform.translation.z = 0.1
        t2.transform.rotation.w = 1.0
        
        # base_link -> imu_link
        t3 = TransformStamped()
        t3.header.stamp = now
        t3.header.frame_id = 'base_link'
        t3.child_frame_id = 'imu_link'
        t3.transform.translation.z = 0.05
        t3.transform.rotation.w = 1.0
        
        self.tf_static_broadcaster.sendTransform([t1, t2, t3])

    def broadcast_odom_tf(self):
        # Broadcast odom -> base_link with forward time buffer (+50ms) to prevent extrapolation errors
        now = self.get_clock().now()
        stamp = (now + rclpy.duration.Duration(seconds=0.05)).to_msg()
        
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.0
        
        # Lock yaw heading from IMU filtered quaternion (2D planar mode: only yaw rotation)
        w, x, y, z = self.filt_quat
        siny_cosp = 2.0 * (w * z + x * y)
        cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        # Convert planar yaw to quaternion
        half_yaw = yaw * 0.5
        t.transform.rotation.w = math.cos(half_yaw)
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = math.sin(half_yaw)
        
        self.tf_broadcaster.sendTransform(t)

    def scan_cb(self, msg):
        msg.header.stamp = self.get_clock().now().to_msg()
        self.pub_scan.publish(msg)
        
    def imu_cb(self, msg):
        now_msg = self.get_clock().now().to_msg()
        msg.header.stamp = now_msg
        
        q_raw = [msg.orientation.w, msg.orientation.x, msg.orientation.y, msg.orientation.z]
        
        # 1. Outlier Rejection
        dot = self.filt_quat[0]*q_raw[0] + self.filt_quat[1]*q_raw[1] + self.filt_quat[2]*q_raw[2] + self.filt_quat[3]*q_raw[3]
        if abs(dot) < (1.0 - self.max_angular_jump):
            q_raw = self.filt_quat
            
        # 2. SLERP Jitter Smoothing
        q_smooth = quat_slerp(self.filt_quat, q_raw, self.quat_smooth_alpha)
        self.filt_quat = q_smooth
        
        msg.orientation.w = q_smooth[0]
        msg.orientation.x = q_smooth[1]
        msg.orientation.y = q_smooth[2]
        msg.orientation.z = q_smooth[3]
        
        self.pub_imu.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    relay = QoSRelay()
    rclpy.spin(relay)
    relay.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
