import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout
child.expect([r'[pP]assword:'], timeout=15)
child.sendline("Askaban78@#")
child.expect([r'arduino@blissy:\~\$ '], timeout=15)

child.sendline("docker exec -it rplidar bash -c 'source /opt/ros/jazzy/setup.bash && source /ros_ws/install/setup.bash && export ROS_DOMAIN_ID=42 && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && ros2 pkg list | grep rplidar'")
child.expect([r'arduino@blissy:\~\$ '], timeout=20)

child.sendline("exit")
child.expect(pexpect.EOF)
