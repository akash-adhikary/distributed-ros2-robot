import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
idx = child.expect([r'password:', r'Password:'], timeout=10)
child.sendline("Askaban78@#")
child.expect(r'\$', timeout=10)

# Install SparkFun BNO08x library as well for full quaternion & sensor reporting
child.sendline('arduino-cli lib install "SparkFun BNO08x Cortex Based IMU"')
child.expect(r'\$', timeout=45)

# Flash full IMU reader firmware that provides getQuat and getGyro via RPC
child.sendline('cat << "SKETCH" > ~/BnoTest/BnoTest.ino\n'
'#include <Arduino_RouterBridge.h>\n'
'#include <Wire.h>\n'
'#include <SparkFun_BNO08x_Arduino_Library.h>\n'
'\n'
'BNO08x myIMU;\n'
'bool imuReady = false;\n'
'\n'
'bool initIMU() {\n'
'  Wire.begin();\n'
'  if (myIMU.begin(0x4B, Wire)) {\n'
'    myIMU.enableRotationVector(20); // 50Hz update rate\n'
'    myIMU.enableGyro(20);\n'
'    imuReady = true;\n'
'    return true;\n'
'  }\n'
'  return false;\n'
'}\n'
'\n'
'msgpack::type::tuple<float, float, float, float, float, float, float> getIMUData() {\n'
'  float qx = 0, qy = 0, qz = 0, qw = 1.0;\n'
'  float gx = 0, gy = 0, gz = 0;\n'
'  if (imuReady && myIMU.dataAvailable()) {\n'
'    qx = myIMU.getQuatI();\n'
'    qy = myIMU.getQuatJ();\n'
'    qz = myIMU.getQuatK();\n'
'    qw = myIMU.getQuatReal();\n'
'    gx = myIMU.getGyroX();\n'
'    gy = myIMU.getGyroY();\n'
'    gz = myIMU.getGyroZ();\n'
'  }\n'
'  return msgpack::type::make_tuple(qx, qy, qz, qw, gx, gy, gz);\n'
'}\n'
'\n'
'void setup() {\n'
'  Bridge.begin();\n'
'  Bridge.provide("initIMU", initIMU);\n'
'  Bridge.provide("getIMUData", getIMUData);\n'
'  initIMU();\n'
'}\n'
'\n'
'void loop() {\n'
'  Bridge.update();\n'
'}\n'
'SKETCH\n')
child.expect(r'\$', timeout=10)

# Compile & upload to MCU
child.sendline("arduino-cli compile -v --fqbn arduino:zephyr:unoq ~/BnoTest && arduino-cli upload -v -p 127.0.0.1 --fqbn arduino:zephyr:unoq ~/BnoTest")
child.expect(r'\$', timeout=180)

# Restart router
child.sendline("sudo systemctl restart arduino-router")
idx = child.expect([r'password for arduino:', r'\$'], timeout=10)
if idx == 0:
    child.sendline("Askaban78@#")
    child.expect(r'\$', timeout=10)

child.sendline("exit")
child.expect(pexpect.EOF)
