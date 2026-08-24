import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("""cat << 'PYEOF' > ~/my_robot_ws/src/unoq_driver/unoq_driver/imu_node.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import socket
import msgpack
import time
import math

class UnoQImuNode(Node):
    def __init__(self):
        super().__init__('unoq_imu_node')
        self.publisher_ = self.create_publisher(Imu, 'imu/data', 10)
        self.raw_publisher_ = self.create_publisher(Imu, 'imu/data_raw', 10)
        
        self.socket_path = '/var/run/arduino-router.sock'
        self.sock = None
        self.connect_socket()
        
        # Publish at 50 Hz
        self.timer = self.create_timer(0.02, self.publish_imu)
        self.get_logger().info("Uno Q IMU Driver (BNO086) initialized successfully.")

    def connect_socket(self):
        try:
            if self.sock:
                self.sock.close()
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.socket_path)
            self.sock.settimeout(0.05)
        except Exception as e:
            self.get_logger().warn(f"Failed to connect to router socket: {e}")
            self.sock = None

    def call_mcu(self, method):
        if not self.sock:
            self.connect_socket()
            if not self.sock:
                return None
        try:
            self.sock.sendall(msgpack.packb([0, 1, method, []]))
            buf = self.sock.recv(1024)
            u = msgpack.Unpacker()
            u.feed(buf)
            for msg in u:
                return msg[3]
        except Exception:
            self.connect_socket()
            return None

    def publish_imu(self):
        qr = self.call_mcu('imu/qr')
        qi = self.call_mcu('imu/qi')
        qj = self.call_mcu('imu/qj')
        qk = self.call_mcu('imu/qk')
        ax = self.call_mcu('imu/ax')
        ay = self.call_mcu('imu/ay')
        az = self.call_mcu('imu/az')
        gx = self.call_mcu('imu/gx')
        gy = self.call_mcu('imu/gy')
        gz = self.call_mcu('imu/gz')

        if qr is None or qi is None or qj is None or qk is None:
            return

        w = qr / 10000.0
        x = qi / 10000.0
        y = qj / 10000.0
        z = qk / 10000.0

        # Normalization guard
        norm = math.sqrt(w*w + x*x + y*y + z*z)
        if norm > 0.0001:
            w /= norm
            x /= norm
            y /= norm
            z /= norm
        else:
            w, x, y, z = 1.0, 0.0, 0.0, 0.0

        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'imu_link'

        msg.orientation.w = float(w)
        msg.orientation.x = float(x)
        msg.orientation.y = float(y)
        msg.orientation.z = float(z)

        if ax is not None and ay is not None and az is not None:
            msg.linear_acceleration.x = float(ax) / 100.0
            msg.linear_acceleration.y = float(ay) / 100.0
            msg.linear_acceleration.z = float(az) / 100.0

        if gx is not None and gy is not None and gz is not None:
            msg.angular_velocity.x = (float(gx) / 1000.0) * (math.pi / 180.0)
            msg.angular_velocity.y = (float(gy) / 1000.0) * (math.pi / 180.0)
            msg.angular_velocity.z = (float(gz) / 1000.0) * (math.pi / 180.0)

        # Covariances for EKF
        msg.orientation_covariance = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001]
        msg.angular_velocity_covariance = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001]
        msg.linear_acceleration_covariance = [0.01, 0.0, 0.0, 0.0, 0.01, 0.0, 0.0, 0.0, 0.01]

        self.publisher_.publish(msg)
        self.raw_publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = UnoQImuNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
PYEOF
""")
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
