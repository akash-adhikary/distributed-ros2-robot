import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import math

class BNO08xPublisher(Node):
    def __init__(self):
        super().__init__("bno08x_publisher")
        self.publisher_ = self.create_publisher(Imu, "/imu/data_raw", 10)
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info("BNO08x Dummy Publisher Started")

    def timer_callback(self):
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"
        msg.orientation.w = 1.0
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = BNO08xPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
