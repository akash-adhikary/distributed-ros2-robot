import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("""cat << 'PYEOF' > /home/arduino/pendrive/ros_ws/src/bno08x_ros/bno08x_ros/imu_publisher.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import socket
import msgpack
import math

class BNO08xPublisher(Node):
    def __init__(self):
        super().__init__("bno08x_publisher")
        self.publisher_ = self.create_publisher(Imu, "/imu/data", 10)
        self.raw_publisher_ = self.create_publisher(Imu, "/imu/data_raw", 10)
        self.sock = None
        self.connect_socket()
        self.timer = self.create_timer(0.01, self.timer_callback) # 100 Hz
        self.last_quat = [1.0, 0.0, 0.0, 0.0]
        self.get_logger().info("Rocksolid 100Hz BNO08x Publisher active.")

    def connect_socket(self):
        try:
            if self.sock:
                self.sock.close()
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect("/var/run/arduino-router.sock")
            self.sock.settimeout(0.01)
        except Exception:
            self.sock = None

    def call_mcu_fast(self):
        if not self.sock:
            self.connect_socket()
            if not self.sock:
                return None
        try:
            self.sock.sendall(msgpack.packb([0, 1, "imu/raw", []]))
            buf = self.sock.recv(512)
            u = msgpack.Unpacker()
            u.feed(buf)
            for msg in u:
                raw_str = msg[3]
                if raw_str:
                    parts = [int(p) for p in raw_str.split(',')]
                    if len(parts) >= 10:
                        return parts
        except Exception:
            self.sock = None
        return None

    def timer_callback(self):
        parts = self.call_mcu_fast()
        if not parts:
            return

        qr, qi, qj, qk, ax, ay, az, gx, gy, gz = parts[:10]

        w = float(qr) / 10000.0
        x = float(qi) / 10000.0
        y = float(qj) / 10000.0
        z = float(qk) / 10000.0

        norm = math.sqrt(w*w + x*x + y*y + z*z)
        if norm > 0.0001:
            w /= norm
            x /= norm
            y /= norm
            z /= norm
        else:
            w, x, y, z = self.last_quat

        # Sign consistency
        dot = w*self.last_quat[0] + x*self.last_quat[1] + y*self.last_quat[2] + z*self.last_quat[3]
        if dot < 0.0:
            w, x, y, z = -w, -x, -y, -z

        self.last_quat = [w, x, y, z]

        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "imu_link"

        msg.orientation.w = float(w)
        msg.orientation.x = float(x)
        msg.orientation.y = float(y)
        msg.orientation.z = float(z)

        # Accelerations in m/s^2
        msg.linear_acceleration.x = float(ax) / 100.0
        msg.linear_acceleration.y = float(ay) / 100.0
        msg.linear_acceleration.z = float(az) / 100.0

        # Angular velocity in rad/s
        msg.angular_velocity.x = (float(gx) / 1000.0) * (math.pi / 180.0)
        msg.angular_velocity.y = (float(gy) / 1000.0) * (math.pi / 180.0)
        msg.angular_velocity.z = (float(gz) / 1000.0) * (math.pi / 180.0)

        msg.orientation_covariance = [0.0001, 0.0, 0.0, 0.0, 0.0001, 0.0, 0.0, 0.0, 0.0001]
        msg.angular_velocity_covariance = [0.0001, 0.0, 0.0, 0.0, 0.0001, 0.0, 0.0, 0.0, 0.0001]
        msg.linear_acceleration_covariance = [0.001, 0.0, 0.0, 0.0, 0.001, 0.0, 0.0, 0.0, 0.001]

        self.publisher_.publish(msg)
        self.raw_publisher_.publish(msg)

    def destroy_node(self):
        if self.sock:
            try: self.sock.close()
            except: pass
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = BNO08xPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
PYEOF
docker restart bno08x_ros
""")
child.expect([r'\$ '], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
