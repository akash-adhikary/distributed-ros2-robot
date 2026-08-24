import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("sudo chown -R arduino:arduino /home/arduino/pendrive")
child.expect([r'\[sudo\] password for arduino:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("mkdir -p /home/arduino/pendrive/ros_ws/src")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cd /home/arduino/pendrive/ros_ws/src && git clone https://github.com/Slamtec/rplidar_ros.git -b humble-devel || git clone https://github.com/Slamtec/sllidar_ros2.git rplidar_ros -b main")
child.expect([r'arduino@blissy:\~\$ '], timeout=30)

child.sendline("cd /home/arduino/pendrive/ros_ws/src && git clone https://github.com/flynneva/bno08x_ros.git || git clone https://github.com/flynneva/bno08x_ros2.git bno08x_ros || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=30)

child.sendline("cd /home/arduino/pendrive/ros_ws && cat << 'XML' > cyclonedds.xml\n<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<CycloneDDS xmlns=\"https://cdds.io/config\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd\">\n    <Domain id=\"any\">\n        <General>\n            <NetworkInterfaceAddress>wlan0</NetworkInterfaceAddress>\n            <AllowMulticast>true</AllowMulticast>\n        </General>\n    </Domain>\n</CycloneDDS>\nXML")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

# Recreate Docker container
child.sendline("docker run -d --name rplidar -v /home/arduino/pendrive/ros_ws:/ws --privileged -v /dev:/dev ros:humble-ros-base sleep infinity")
child.expect([r'arduino@blissy:\~\$ '], timeout=600)

child.sendline("docker exec rplidar apt-get update")
child.expect([r'arduino@blissy:\~\$ '], timeout=120)

child.sendline("docker exec rplidar apt-get install -y python3-msgpack python3-colcon-common-extensions")
child.expect([r'arduino@blissy:\~\$ '], timeout=120)

child.sendline("docker exec rplidar bash -c 'cd /ws && source /opt/ros/humble/setup.bash && colcon build'")
child.expect([r'arduino@blissy:\~\$ '], timeout=600)

child.sendline("exit")
child.expect(pexpect.EOF)
