import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=25)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("cat << 'XML' > /home/arduino/pendrive/ros_ws/cyclonedds.xml\n<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<CycloneDDS xmlns=\"https://cdds.io/config\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd\">\n    <Domain id=\"any\">\n        <General>\n            <Interfaces>\n                <NetworkInterface name=\"wlan0\" />\n            </Interfaces>\n        </General>\n    </Domain>\n</CycloneDDS>\nXML")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker exec rplidar pkill -f rplidar_c1_launch.py || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker exec rplidar pkill -f imu_publisher.py || true")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/humble/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && ros2 launch rplidar_ros rplidar_c1_launch.py'")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/humble/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export CYCLONEDDS_URI=file:///ws/cyclonedds.xml && python3 -u /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py'")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("exit")
child.expect(pexpect.EOF)
