import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

child.sendline("docker stop rplidar || true && docker rm rplidar || true")
child.expect([r'\$ '], timeout=30)

child.sendline("docker run -d --name rplidar --net=host -v /home/arduino/pendrive/ros_ws:/ws --privileged -v /dev:/dev ros:jazzy-ros-base sleep infinity")
child.expect([r'\$ '], timeout=600)

child.sendline("docker exec rplidar apt-get update")
child.expect([r'\$ '], timeout=120)

child.sendline("docker exec rplidar apt-get install -y python3-msgpack python3-colcon-common-extensions ros-jazzy-rmw-cyclonedds-cpp ros-jazzy-rmw-fastrtps-cpp")
child.expect([r'\$ '], timeout=300)

# Clean build artifacts to rebuild for Jazzy
child.sendline("docker exec rplidar bash -c 'cd /ws && rm -rf build install log'")
child.expect([r'\$ '], timeout=30)

child.sendline("docker exec rplidar bash -c 'cd /ws && source /opt/ros/jazzy/setup.bash && colcon build'")
child.expect([r'\$ '], timeout=300)

child.sendline("exit")
child.expect(pexpect.EOF)
