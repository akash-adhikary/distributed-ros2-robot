import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

# Create the ROS2 python package
child.sendline("docker exec rplidar bash -c 'cd /ws/src && ros2 pkg create --build-type ament_python bno08x_ros'")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec rplidar bash -c 'cat << \\\"PYTHON\\\" > /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py\nimport rclpy\nfrom rclpy.node import Node\nfrom sensor_msgs.msg import Imu\nimport math\n\nclass BNO08xPublisher(Node):\n    def __init__(self):\n        super().__init__(\\\"bno08x_publisher\\\")\n        self.publisher_ = self.create_publisher(Imu, \\\"/imu/data_raw\\\", 10)\n        self.timer = self.create_timer(0.1, self.timer_callback)\n        self.get_logger().info(\\\"BNO08x Dummy Publisher Started\\\")\n\n    def timer_callback(self):\n        msg = Imu()\n        msg.header.stamp = self.get_clock().now().to_msg()\n        msg.header.frame_id = \\\"imu_link\\\"\n        msg.orientation.w = 1.0\n        self.publisher_.publish(msg)\n\ndef main(args=None):\n    rclpy.init(args=args)\n    node = BNO08xPublisher()\n    rclpy.spin(node)\n    node.destroy_node()\n    rclpy.shutdown()\n\nif __name__ == \\\"__main__\\\":\n    main()\nPYTHON'")
child.expect([r'\$ '], timeout=15)

# Fix Lidar crash by using FastRTPS instead of CycloneDDS?
# The user's system crashed because CycloneDDS has a string null termination bug on ARM64 with sllidar_ros2.
# But wait, CycloneDDS works perfectly on Laptop. 
# We can fix CycloneDDS by building `rplidar_ros` instead of `sllidar_ros2`!
child.sendline("docker exec rplidar bash -c 'cd /ws/src && rm -rf sllidar_ros2 && git clone https://github.com/Slamtec/rplidar_ros.git -b humble-devel'")
child.expect([r'\$ '], timeout=30)

child.sendline("docker exec rplidar bash -c 'cd /ws && source /opt/ros/humble/setup.bash && colcon build'")
child.expect([r'\$ '], timeout=300)

child.sendline("exit")
child.expect(pexpect.EOF)
