import pexpect, sys

bash_script = """
set -e
rm -f ~/BnoTest/*.ino
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>

// Software I2C ping test on Uno Q pins
// SDA = 18 (A4), SCL = 19 (A5)
const int PIN_SDA = 18;
const int PIN_SCL = 19;

int i2c_ping_addr(uint8_t addr) {
  pinMode(PIN_SDA, OUTPUT);
  pinMode(PIN_SCL, OUTPUT);
  digitalWrite(PIN_SDA, HIGH);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(10);
  
  // START
  digitalWrite(PIN_SDA, LOW);
  delayMicroseconds(10);
  digitalWrite(PIN_SCL, LOW);
  delayMicroseconds(10);
  
  // Send byte (addr << 1 | 0 for write)
  uint8_t b = (addr << 1);
  for (int i = 7; i >= 0; i--) {
    if (b & (1 << i)) digitalWrite(PIN_SDA, HIGH);
    else digitalWrite(PIN_SDA, LOW);
    delayMicroseconds(5);
    digitalWrite(PIN_SCL, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_SCL, LOW);
    delayMicroseconds(5);
  }
  
  // Read ACK
  pinMode(PIN_SDA, INPUT_PULLUP);
  delayMicroseconds(5);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(10);
  int ack = digitalRead(PIN_SDA); // 0 = ACK, 1 = NACK
  digitalWrite(PIN_SCL, LOW);
  delayMicroseconds(5);
  
  // STOP
  pinMode(PIN_SDA, OUTPUT);
  digitalWrite(PIN_SDA, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_SCL, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_SDA, HIGH);
  delayMicroseconds(10);
  
  return ack;
}

int scan_result = -1;

int get_status() {
  return scan_result;
}

void setup() {
  Bridge.begin();
  Bridge.provide("imu/status", get_status);
}

void loop() {
  int found = 0;
  if (i2c_ping_addr(0x4A) == 0) found = 0x4A;
  else if (i2c_ping_addr(0x4B) == 0) found = 0x4B;
  else if (i2c_ping_addr(0x28) == 0) found = 0x28;
  else if (i2c_ping_addr(0x68) == 0) found = 0x68;
  
  scan_result = found;
  Bridge.update();
  delay(100);
}
SKETCH

echo "Compiling..."
arduino-cli compile --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo "Uploading..."
arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest > /dev/null
echo 'Askaban78@#' | sudo -S systemctl restart arduino-router
sleep 3
python3 ~/query_imu.py
echo "ALL_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'ALL_DONE'], timeout=180)

child.sendline("exit")
child.expect(pexpect.EOF)
