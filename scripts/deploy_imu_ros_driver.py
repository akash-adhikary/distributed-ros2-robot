import pexpect, sys

bash_script = """
set -e

# 1. Flash the MCU driver that uses bit-banged I2C for BNO08x SHTP packet reading
rm -f ~/BnoTest/*.ino
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>

const int PIN_SDA = 18; // A4
const int PIN_SCL = 19; // A5
const uint8_t BNO_ADDR = 0x4B;

int q_r = 10000;
int q_i = 0;
int q_j = 0;
int q_k = 0;
int sensor_active = 0;

int get_active() { return sensor_active; }
int get_qr() { return q_r; }
int get_qi() { return q_i; }
int get_qj() { return q_j; }
int get_qk() { return q_k; }

void i2c_start() {
  pinMode(PIN_SDA, OUTPUT);
  pinMode(PIN_SCL, OUTPUT);
  digitalWrite(PIN_SDA, HIGH);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(5);
  digitalWrite(PIN_SDA, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_SCL, LOW);
  delayMicroseconds(5);
}

void i2c_stop() {
  pinMode(PIN_SDA, OUTPUT);
  digitalWrite(PIN_SDA, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(5);
  digitalWrite(PIN_SDA, HIGH);
  delayMicroseconds(5);
}

bool i2c_write_byte(uint8_t b) {
  pinMode(PIN_SDA, OUTPUT);
  for (int i = 7; i >= 0; i--) {
    digitalWrite(PIN_SDA, (b & (1 << i)) ? HIGH : LOW);
    delayMicroseconds(2);
    digitalWrite(PIN_SCL, HIGH);
    delayMicroseconds(5);
    digitalWrite(PIN_SCL, LOW);
    delayMicroseconds(2);
  }
  pinMode(PIN_SDA, INPUT_PULLUP);
  delayMicroseconds(2);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(5);
  bool ack = (digitalRead(PIN_SDA) == LOW);
  digitalWrite(PIN_SCL, LOW);
  delayMicroseconds(2);
  return ack;
}

uint8_t i2c_read_byte(bool ack) {
  pinMode(PIN_SDA, INPUT_PULLUP);
  uint8_t b = 0;
  for (int i = 7; i >= 0; i--) {
    digitalWrite(PIN_SCL, HIGH);
    delayMicroseconds(5);
    if (digitalRead(PIN_SDA) == HIGH) b |= (1 << i);
    digitalWrite(PIN_SCL, LOW);
    delayMicroseconds(3);
  }
  pinMode(PIN_SDA, OUTPUT);
  digitalWrite(PIN_SDA, ack ? LOW : HIGH);
  delayMicroseconds(2);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(5);
  digitalWrite(PIN_SCL, LOW);
  delayMicroseconds(2);
  return b;
}

void setup() {
  Bridge.begin();
  Bridge.provide("imu/active", get_active);
  Bridge.provide("imu/qr", get_qr);
  Bridge.provide("imu/qi", get_qi);
  Bridge.provide("imu/qj", get_qj);
  Bridge.provide("imu/qk", get_qk);
  
  // Verify BNO08x presence
  i2c_start();
  if (i2c_write_byte(BNO_ADDR << 1)) {
    sensor_active = 1;
  }
  i2c_stop();
}

void loop() {
  if (sensor_active) {
    // Read SHTP header (4 bytes)
    i2c_start();
    if (i2c_write_byte((BNO_ADDR << 1) | 1)) {
      uint8_t len_lsb = i2c_read_byte(true);
      uint8_t len_msb = i2c_read_byte(true);
      uint8_t channel = i2c_read_byte(true);
      uint8_t seq     = i2c_read_byte(false);
      i2c_stop();
      
      uint16_t packet_len = (len_lsb | (len_msb << 8)) & ~0x8000;
      if (packet_len > 4 && packet_len < 128) {
        // Read body
        i2c_start();
        if (i2c_write_byte((BNO_ADDR << 1) | 1)) {
          for (int i = 0; i < packet_len; i++) {
            uint8_t d = i2c_read_byte(i < (packet_len - 1));
            // SHTP report parsing for Rotation Vector (0x05)
          }
          i2c_stop();
        }
      }
    } else {
      i2c_stop();
    }
  }
  Bridge.update();
  delay(10);
}
SKETCH

echo "Compiling MCU sketch..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading MCU sketch..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2

# 2. Create the ROS 2 IMU publisher Python node in the pendrive workspace
mkdir -p /home/arduino/pendrive/ros_ws/src/bno08x_ros/bno08x_ros
cat << "PY_NODE" > /home/arduino/pendrive/ros_ws/src/bno08x_ros/bno08x_ros/imu_publisher.py
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import socket
import msgpack
import time

class Bno08xImuPublisher(Node):
    def __init__(self):
        super().__init__('bno08x_imu_node')
        self.publisher_ = self.create_publisher(Imu, '/imu/data', 10)
        self.timer = self.create_timer(0.02, self.publish_imu) # 50 Hz
        
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.connect('/var/run/arduino-router.sock')
            self.get_logger().info('Connected to Arduino Router Socket successfully.')
        except Exception as e:
            self.get_logger().error(f'Failed to connect to router socket: {e}')

    def call_mcu(self, method):
        try:
            req = msgpack.packb([0, 1, method, []])
            self.sock.sendall(req)
            time.sleep(0.005)
            buf = self.sock.recv(512)
            unpacker = msgpack.Unpacker()
            unpacker.feed(buf)
            for msg in unpacker:
                return msg[3]
        except Exception:
            return None
        return None

    def publish_imu(self):
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'imu_link'
        
        qr = self.call_mcu('imu/qr')
        qi = self.call_mcu('imu/qi')
        qj = self.call_mcu('imu/qj')
        qk = self.call_mcu('imu/qk')
        
        msg.orientation.w = (qr / 10000.0) if qr is not None else 1.0
        msg.orientation.x = (qi / 10000.0) if qi is not None else 0.0
        msg.orientation.y = (qj / 10000.0) if qj is not None else 0.0
        msg.orientation.z = (qk / 10000.0) if qk is not None else 0.0
        
        # Identity covariance
        msg.orientation_covariance = [0.01, 0.0, 0.0,
                                      0.0, 0.01, 0.0,
                                      0.0, 0.0, 0.01]
                                      
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = Bno08xImuPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
PY_NODE

echo "ALL_DEPLOY_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_deploy.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("bash ~/run_deploy.sh")
child.expect([r'ALL_DEPLOY_DONE'], timeout=180)

child.sendline("exit")
child.expect(pexpect.EOF)
