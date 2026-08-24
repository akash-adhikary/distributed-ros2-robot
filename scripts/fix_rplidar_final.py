import pexpect, sys

child = pexpect.spawn("ssh -o StrictHostKeyChecking=no arduino@192.168.1.17", encoding='utf-8')
child.logfile = sys.stdout

child.expect([r'[pP]assword:'], timeout=60)
child.sendline("Askaban78@#")
child.expect([r'\$ '], timeout=15)

# Lidar: The issue with CycloneDDS on sllidar_ros2 might be solvable by just passing standard fastrtps.
# But wait, CycloneDDS on ARM64 has a bug. Let's just use sllidar_ros2 from `main` branch. 
# Wait, sllidar_ros2 was what caused the bug in the first place!
# Let's clone rplidar_ros branch `ros2`
child.sendline("docker exec rplidar bash -c 'cd /ws/src && git clone https://github.com/Slamtec/rplidar_ros.git -b ros2'")
child.expect([r'\$ '], timeout=60)

# Fix IMU python script escaping
child.sendline("docker exec rplidar bash -c 'cat << \"PYTHON\" > /ws/src/bno08x_ros/bno08x_ros/imu_publisher.py\nimport rclpy\nfrom rclpy.node import Node\nfrom sensor_msgs.msg import Imu\nimport math\n\nclass BNO08xPublisher(Node):\n    def __init__(self):\n        super().__init__(\"bno08x_publisher\")\n        self.publisher_ = self.create_publisher(Imu, \"/imu/data_raw\", 10)\n        self.timer = self.create_timer(0.1, self.timer_callback)\n        self.get_logger().info(\"BNO08x Dummy Publisher Started\")\n\n    def timer_callback(self):\n        msg = Imu()\n        msg.header.stamp = self.get_clock().now().to_msg()\n        msg.header.frame_id = \"imu_link\"\n        msg.orientation.w = 1.0\n        self.publisher_.publish(msg)\n\ndef main(args=None):\n    rclpy.init(args=args)\n    node = BNO08xPublisher()\n    rclpy.spin(node)\n    node.destroy_node()\n    rclpy.shutdown()\n\nif __name__ == \"__main__\":\n    main()\nPYTHON'")
child.expect([r'\$ '], timeout=15)

child.sendline("docker exec rplidar bash -c 'cd /ws && source /opt/ros/humble/setup.bash && colcon build'")
child.expect([r'\$ '], timeout=300)

child.sendline("exit")
child.expect(pexpect.EOF)
