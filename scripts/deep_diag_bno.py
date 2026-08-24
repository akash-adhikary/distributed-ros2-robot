import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

diag_sketch = """cat << 'SKETCH' > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>

int i2c_4a_found = 0;
int i2c_4b_found = 0;
int raw_bytes_read = 0;
int raw_byte_0 = 0;
int raw_byte_1 = 0;
int raw_byte_2 = 0;
int raw_byte_3 = 0;

int get_4a() { return i2c_4a_found; }
int get_4b() { return i2c_4b_found; }
int get_raw_cnt() { return raw_bytes_read; }
int get_b0() { return raw_byte_0; }
int get_b1() { return raw_byte_1; }
int get_b2() { return raw_byte_2; }
int get_b3() { return raw_byte_3; }

void setup() {
  Bridge.begin();
  Bridge.provide("diag/4a", get_4a);
  Bridge.provide("diag/4b", get_4b);
  Bridge.provide("diag/cnt", get_raw_cnt);
  Bridge.provide("diag/b0", get_b0);
  Bridge.provide("diag/b1", get_b1);
  Bridge.provide("diag/b2", get_b2);
  Bridge.provide("diag/b3", get_b3);

  Wire.begin();
  delay(100);

  // Probe 0x4A
  Wire.beginTransmission(0x4A);
  if (Wire.endTransmission() == 0) i2c_4a_found = 1;

  // Probe 0x4B
  Wire.beginTransmission(0x4B);
  if (Wire.endTransmission() == 0) i2c_4b_found = 1;
}

void loop() {
  uint8_t target = i2c_4b_found ? 0x4B : (i2c_4a_found ? 0x4A : 0);
  if (target != 0) {
    uint8_t count = Wire.requestFrom(target, (uint8_t)4);
    if (count >= 4) {
      raw_bytes_read += count;
      raw_byte_0 = Wire.read();
      raw_byte_1 = Wire.read();
      raw_byte_2 = Wire.read();
      raw_byte_3 = Wire.read();
    }
  }
  Bridge.update();
  delay(50);
}
SKETCH

arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 2

cat << 'PYEOF' > ~/read_raw_diag.py
import socket, msgpack, time

def call_mcu(s, m):
    try:
        s.sendall(msgpack.packb([0, 1, m, []]))
        time.sleep(0.01)
        buf = s.recv(1024)
        u = msgpack.Unpacker()
        u.feed(buf)
        for msg in u: return msg[3]
    except: pass
    return None

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/arduino-router.sock')
print('--- HARDWARE I2C BUS DIAGNOSTIC ---')
print('Probe 0x4A ACK:', call_mcu(s, 'diag/4a'))
print('Probe 0x4B ACK:', call_mcu(s, 'diag/4b'))
print('Total Raw Bytes Read:', call_mcu(s, 'diag/cnt'))
print('Header Bytes [0, 1, 2, 3]:', [hex(call_mcu(s, f'diag/b{i}') or 0) for i in range(4)])
s.close()
PYEOF
python3 ~/read_raw_diag.py
"""
child.sendline(diag_sketch)
child.expect([r'--- HARDWARE I2C BUS DIAGNOSTIC ---'], timeout=60)
child.expect([r'Header Bytes'], timeout=15)
child.expect([r'\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
