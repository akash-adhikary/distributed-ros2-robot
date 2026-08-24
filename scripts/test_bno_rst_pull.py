import pexpect, sys

bash_script = """
set -e
rm -f ~/BnoTest/*.ino
cat << "SKETCH" > ~/BnoTest/BnoTest.ino
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include <Adafruit_BNO08x.h>

Adafruit_BNO08x bno08x;
sh2_SensorValue_t sensorValue;
int imu_status = -1;

int get_status() {
  return imu_status;
}

void setup() {
  Bridge.begin();
  Bridge.provide("imu/status", get_status);
  
  Wire.begin();
  Wire.setClock(100000); // Standard 100kHz I2C
  delay(300);
  
  // Try 0x4A and 0x4B
  if (bno08x.begin_I2C(0x4A, &Wire)) {
    imu_status = 2;
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
  } else if (bno08x.begin_I2C(0x4B, &Wire)) {
    imu_status = 1;
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
  } else {
    imu_status = 0;
  }
}

void loop() {
  if (imu_status > 0) {
    bno08x.getSensorEvent(&sensorValue);
  }
  Bridge.update();
  delay(20);
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
child.expect([r'ALL_DONE'], timeout=120)

child.sendline("exit")
child.expect(pexpect.EOF)
