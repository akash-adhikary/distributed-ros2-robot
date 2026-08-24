import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

# Skip the broken git clone, just proceed
child.sendline("cd /home/arduino/pendrive/ros_ws && cat << 'XML' > cyclonedds.xml\n<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<CycloneDDS xmlns=\"https://cdds.io/config\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd\">\n    <Domain id=\"any\">\n        <General>\n            <NetworkInterfaceAddress>wlan0</NetworkInterfaceAddress>\n            <AllowMulticast>true</AllowMulticast>\n        </General>\n    </Domain>\n</CycloneDDS>\nXML")
child.expect([r'\$ '], timeout=15)

# Recreate Docker container
child.sendline("docker stop rplidar || true")
child.expect([r'\$ '], timeout=30)
child.sendline("docker rm rplidar || true")
child.expect([r'\$ '], timeout=30)

child.sendline("docker run -d --name rplidar -v /home/arduino/pendrive/ros_ws:/ws --privileged -v /dev:/dev ros:humble-ros-base sleep infinity")
child.expect([r'\$ '], timeout=600)

child.sendline("docker exec rplidar apt-get update")
child.expect([r'\$ '], timeout=120)

child.sendline("docker exec rplidar apt-get install -y python3-msgpack python3-colcon-common-extensions")
child.expect([r'\$ '], timeout=120)

child.sendline("docker exec rplidar bash -c 'cd /ws && source /opt/ros/humble/setup.bash && colcon build'")
child.expect([r'\$ '], timeout=600)

child.sendline("exit")
child.expect(pexpect.EOF)
