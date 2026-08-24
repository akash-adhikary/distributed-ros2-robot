#!/usr/bin/env python3
import time
import rclpy
from rclpy.node import Node
from lifecycle_msgs.srv import ChangeState, GetState
from lifecycle_msgs.msg import Transition

class SlamLifecycleActivator(Node):
    def __init__(self):
        super().__init__('slam_lifecycle_activator')
        self.get_logger().info('SLAM Lifecycle Activator started. Waiting for /slam_toolbox service...')
        self.client_change = self.create_client(ChangeState, '/slam_toolbox/change_state')
        self.client_get = self.create_client(GetState, '/slam_toolbox/get_state')
        self.timer = self.create_timer(1.0, self.check_and_transition)
        self.state_step = 0

    def check_and_transition(self):
        if not self.client_change.service_is_ready():
            self.get_logger().info('Waiting for /slam_toolbox/change_state service...')
            return

        if self.state_step == 0:
            self.get_logger().info('Triggering CONFIGURE for /slam_toolbox...')
            req = ChangeState.Request()
            req.transition.id = Transition.TRANSITION_CONFIGURE
            future = self.client_change.call_async(req)
            future.add_done_callback(self.configure_done)
            self.state_step = 1

        elif self.state_step == 2:
            self.get_logger().info('Triggering ACTIVATE for /slam_toolbox...')
            req = ChangeState.Request()
            req.transition.id = Transition.TRANSITION_ACTIVATE
            future = self.client_change.call_async(req)
            future.add_done_callback(self.activate_done)
            self.state_step = 3

    def configure_done(self, future):
        res = future.result()
        if res and res.success:
            self.get_logger().info('Successfully CONFIGURED /slam_toolbox.')
            self.state_step = 2
        else:
            self.get_logger().warn('Failed to configure /slam_toolbox, retrying...')
            self.state_step = 0

    def activate_done(self, future):
        res = future.result()
        if res and res.success:
            self.get_logger().info('Successfully ACTIVATED /slam_toolbox. Mapping active!')
            self.timer.cancel()
        else:
            self.get_logger().warn('Failed to activate /slam_toolbox, retrying...')
            self.state_step = 2

def main(args=None):
    rclpy.init(args=args)
    node = SlamLifecycleActivator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
