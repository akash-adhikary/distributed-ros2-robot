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
bool bnoOk = false;

void setup() {
  Bridge.begin();
  Wire.begin();
  delay(500);
  
  // Try 0x4B then 0x4A
  if (bno08x.begin_I2C(0x4B, &Wire)) {
    bnoOk = true;
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
  } else if (bno08x.begin_I2C(0x4A, &Wire)) {
    bnoOk = true;
    bno08x.enableReport(SH2_ROTATION_VECTOR, 20000);
  }
}

void loop() {
  if (bnoOk) {
    if (bno08x.getSensorEvent(&sensorValue)) {
      if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {
        // Send integer scaled by 10000
        int qr = (int)(sensorValue.un.rotationVector.real * 10000);
        int qi = (int)(sensorValue.un.rotationVector.i * 10000);
        int qj = (int)(sensorValue.un.rotationVector.j * 10000);
        int qk = (int)(sensorValue.un.rotationVector.k * 10000);
        Bridge.notify("IMU_R", qr);
        Bridge.notify("IMU_I", qi);
        Bridge.notify("IMU_J", qj);
        Bridge.notify("IMU_K", qk);
      }
    }
  } else {
    Bridge.notify("IMU_STATUS", 9999);
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
echo "ALL_DONE"
"""

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cat << 'REMOTE_SCRIPT' > ~/run_test.sh\n" + bash_script + "\nREMOTE_SCRIPT\n")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("bash ~/run_test.sh")
child.expect([r'ALL_DONE'], timeout=120)

child.sendline("exit")
child.expect(pexpect.EOF)
