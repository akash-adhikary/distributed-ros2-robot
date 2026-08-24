import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import socket
import msgpack
import time

class BNO08xPublisher(Node):
    def __init__(self):
        super().__init__("bno08x_publisher")
        self.publisher_ = self.create_publisher(Imu, "/imu/data_raw", 10)
        self.sock = None
        self.connect_socket()
        self.timer = self.create_timer(0.05, self.timer_callback) # 20 Hz
        self.get_logger().info("BNO08x Hardware Bridge Publisher started.")

    def connect_socket(self):
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect("/var/run/arduino-router.sock")
            self.sock.settimeout(0.05)
            self.get_logger().info("Connected to /var/run/arduino-router.sock successfully.")
        except Exception as e:
            self.get_logger().warn(f"Waiting for arduino-router socket: {e}")
            self.sock = None

    def call_mcu(self, method):
        if not self.sock:
            self.connect_socket()
            if not self.sock:
                return None
        try:
            req = msgpack.packb([0, 1, method, []])
            self.sock.sendall(req)
            time.sleep(0.005)
            buf = self.sock.recv(1024)
            unpacker = msgpack.Unpacker()
            unpacker.feed(buf)
            for msg in unpacker:
                return msg[3]
        except Exception:
            # Reconnect on broken pipe / timeout
            self.sock = None
        return None

    def timer_callback(self):
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"

        qr = self.call_mcu("imu/qr")
        qi = self.call_mcu("imu/qi")
        qj = self.call_mcu("imu/qj")
        qk = self.call_mcu("imu/qk")

        if qr is not None and qi is not None and qj is not None and qk is not None:
            msg.orientation.w = float(qr) / 10000.0
            msg.orientation.x = float(qi) / 10000.0
            msg.orientation.y = float(qj) / 10000.0
            msg.orientation.z = float(qk) / 10000.0
        else:
            msg.orientation.w = 1.0
            msg.orientation.x = 0.0
            msg.orientation.y = 0.0
            msg.orientation.z = 0.0

        msg.orientation_covariance = [0.01, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.01]
        msg.angular_velocity_covariance = [0.01, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.01]
        msg.linear_acceleration_covariance = [0.01, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.01]
        self.publisher_.publish(msg)

    def destroy_node(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = BNO08xPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
