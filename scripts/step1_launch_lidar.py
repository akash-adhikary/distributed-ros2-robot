import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

# Ensure previous containers/processes are stopped
child.sendline("docker stop rplidar || true && docker rm rplidar || true")
child.expect([r'\$ '], timeout=30)

# Start clean container
child.sendline("docker run -d --name rplidar --net=host -v /home/arduino/pendrive/ros_ws:/ws --privileged -v /dev:/dev ros:jazzy-ros-base sleep infinity")
child.expect([r'\$ '], timeout=30)

# Launch rplidar node in background
child.sendline("docker exec -d rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp && ros2 launch rplidar_ros rplidar_c1_launch.py serial_port:=/dev/ttyUSB0'")
child.expect([r'\$ '], timeout=15)

# Check topic rate locally on Uno Q
child.sendline("docker exec rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_fastrtps_cpp && timeout 8 ros2 topic hz /scan || true'")
child.expect([r'\$ '], timeout=25)

child.sendline("exit")
child.expect(pexpect.EOF)
