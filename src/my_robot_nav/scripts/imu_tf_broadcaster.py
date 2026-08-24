#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster

class ImuTfBroadcaster(Node):
    def __init__(self):
        super().__init__('imu_tf_broadcaster')
        self.tf_broadcaster = TransformBroadcaster(self)
        self.sub = self.create_subscription(Imu, '/imu/data_raw', self.imu_callback, 10)
        self.get_logger().info('IMU-to-TF dynamic broadcaster started. Live orientation active.')

    def imu_callback(self, msg):
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'imu_link'
        
        t.transform.translation.x = 0.0
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.0
        
        t.transform.rotation = msg.orientation
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = ImuTfBroadcaster()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
