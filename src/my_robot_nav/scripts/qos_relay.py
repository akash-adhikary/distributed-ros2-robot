#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class QoSRelay(Node):
    def __init__(self):
        super().__init__('qos_relay')
        # Sub: Best Effort
        sub_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        # Pub: Reliable
        pub_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        self.sub = self.create_subscription(LaserScan, '/scan', self.listener_callback, sub_qos)
        self.pub = self.create_publisher(LaserScan, '/scan_reliable', pub_qos)
        self.get_logger().info('QoS Relay started: /scan (Best Effort) -> /scan_reliable (Reliable)')

    def listener_callback(self, msg):
        # We also sync the timestamp to the laptop's current time to fix any 1-second clock drift!
        msg.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    relay = QoSRelay()
    rclpy.spin(relay)
    relay.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
