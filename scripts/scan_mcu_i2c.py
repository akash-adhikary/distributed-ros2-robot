import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

sketch_code = """
cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>

const int PIN_SDA = 18; // A4
const int PIN_SCL = 19; // A5

int found_addr = 0;
int last_error = 0;

int get_found_addr() { return found_addr; }
int get_last_error() { return last_error; }

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

void setup() {
  Bridge.begin();
  Bridge.provide("i2c/found", get_found_addr);
  Bridge.provide("i2c/err", get_last_error);

  // Scan all I2C addresses 1 to 127
  for (uint8_t addr = 1; addr < 127; addr++) {
    i2c_start();
    if (i2c_write_byte(addr << 1)) {
      found_addr = addr;
      i2c_stop();
      break;
    }
    i2c_stop();
    delayMicroseconds(100);
  }
}

void loop() {
  Bridge.update();
  delay(50);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2

python3 -c "
import socket, msgpack, time
def call_mcu(s, m):
    s.sendall(msgpack.packb([0, 1, m, []]))
    time.sleep(0.02)
    buf = s.recv(1024)
    u = msgpack.Unpacker()
    u.feed(buf)
    for msg in u: return msg[3]
    return None
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')
print('I2C FOUND ADDR (Hex):', hex(call_mcu(s, 'i2c/found') or 0))
s.close()
"
"""
child.sendline(sketch_code)
child.expect([r'I2C FOUND ADDR \(Hex\):'], timeout=60)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
