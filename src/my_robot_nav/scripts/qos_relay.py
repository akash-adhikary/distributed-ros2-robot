#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Imu
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

class QoSRelay(Node):
    def __init__(self):
        super().__init__('qos_relay')
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        pub_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        self.sub_scan = self.create_subscription(LaserScan, '/scan', self.scan_cb, qos)
        self.pub_scan = self.create_publisher(LaserScan, '/scan_reliable', pub_qos)
        
        self.sub_imu = self.create_subscription(Imu, '/imu/data_raw', self.imu_cb, qos)
        self.pub_imu = self.create_publisher(Imu, '/imu_reliable', pub_qos)
        
        self.get_logger().info('QoS Relay started: timestamp sync for /scan and /imu/data')

    def scan_cb(self, msg):
        msg.header.stamp = self.get_clock().now().to_msg()
        self.pub_scan.publish(msg)
        
    def imu_cb(self, msg):
        msg.header.stamp = self.get_clock().now().to_msg()
        self.pub_imu.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    relay = QoSRelay()
    rclpy.spin(relay)
    relay.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
