#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped, TransformStamped
from tf2_ros import TransformBroadcaster
import math

def quat_slerp(q0, q1, t):
    """Spherical linear interpolation between two quaternions [w, x, y, z]"""
    # Ensure dot product is positive (shortest path)
    dot = q0[0]*q1[0] + q0[1]*q1[1] + q0[2]*q1[2] + q0[3]*q1[3]
    if dot < 0.0:
        q1 = [-q1[0], -q1[1], -q1[2], -q1[3]]
        dot = -dot
        
    if dot > 0.9995:
        # Linear interpolation if almost identical
        result = [q0[i] + t * (q1[i] - q0[i]) for i in range(4)]
        norm = math.sqrt(sum(x*x for x in result))
        return [x / norm for x in result]
        
    theta_0 = math.acos(dot)
    sin_theta_0 = math.sin(theta_0)
    theta = theta_0 * t
    sin_theta = math.sin(theta)
    
    s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
    s1 = sin_theta / sin_theta_0
    
    return [s0 * q0[i] + s1 * q1[i] for i in range(4)]

def quat_rotate_vector(q, v):
    qw, qx, qy, qz = q
    vx, vy, vz = v
    tx = 2.0 * (qy * vz - qz * vy)
    ty = 2.0 * (qz * vx - qx * vz)
    tz = 2.0 * (qx * vy - qy * vx)
    rx = vx + qw * tx + (qy * tz - qz * ty)
    ry = vy + qw * ty + (qz * tx - qx * tz)
    rz = vz + qw * tz + (qx * ty - qy * tx)
    return [rx, ry, rz]

def compute_gravity_vector(q, g_mag=9.53):
    qw, qx, qy, qz = q
    gx = 2.0 * (qx * qz - qw * qy) * g_mag
    gy = 2.0 * (qy * qz + qw * qx) * g_mag
    gz = (qw * qw - qx * qx - qy * qy + qz * qz) * g_mag
    return [gx, gy, gz]

class PureImuDeadReckoningNode(Node):
    def __init__(self):
        super().__init__('imu_dead_reckoning_pure')
        
        self.sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, '/imu/dead_reckoning/odom', 10)
        self.path_pub = self.create_publisher(Path, '/imu/dead_reckoning/path', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # State variables
        self.pos = [0.0, 0.0, 0.0]
        self.vel = [0.0, 0.0, 0.0]
        self.last_time = None
        
        # Smooth filtered states
        self.filt_quat = [1.0, 0.0, 0.0, 0.0]
        self.filt_acc = [0.0, 0.0, 0.0]
        
        # Gravity auto-calibration
        self.gravity_mag = 9.53
        self.calib_samples = []
        self.calibrated = False
        
        # Filter tuning parameters
        self.quat_smooth_alpha = 0.35  # Slerp factor (0.0 = old, 1.0 = raw)
        self.acc_smooth_alpha = 0.40   # Low-pass EMA
        self.acc_deadband = 0.18       # m/s^2 (noise gate)
        self.gyro_deadband = 0.08      # rad/s
        self.max_angular_jump = 0.6    # Outlier threshold (rad)
        self.max_acc_magnitude = 25.0  # Outlier threshold (m/s^2)
        self.stationary_ticks = 0
        
        self.path_msg = Path()
        self.path_msg.header.frame_id = 'odom'
        self.last_path_publish_time = 0.0

        self.get_logger().info("Jitter-Filtered Omnidirectional IMU Dead Reckoning active.")

    def imu_callback(self, msg):
        now = self.get_clock().now()
        curr_time = now.nanoseconds * 1e-9
        
        if self.last_time is None:
            self.last_time = curr_time
            self.filt_quat = [msg.orientation.w, msg.orientation.x, msg.orientation.y, msg.orientation.z]
            return

        dt = curr_time - self.last_time
        self.last_time = curr_time
        
        if dt <= 0.0 or dt > 0.1:
            dt = 0.01

        # 1. Raw inputs
        q_raw = [msg.orientation.w, msg.orientation.x, msg.orientation.y, msg.orientation.z]
        a_raw = [msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z]

        # 2. Outlier Rejection (Glitch Gate)
        # Check for unphysical instantaneous quaternion jumps (>35 degrees in 10ms)
        dot = self.filt_quat[0]*q_raw[0] + self.filt_quat[1]*q_raw[1] + self.filt_quat[2]*q_raw[2] + self.filt_quat[3]*q_raw[3]
        if abs(dot) < (1.0 - self.max_angular_jump):
            # Outlier / torn packet: reject and reuse previous valid quaternion
            q_raw = self.filt_quat

        # Check for unphysical acceleration spikes (> 25 m/s^2)
        acc_raw_mag = math.sqrt(a_raw[0]**2 + a_raw[1]**2 + a_raw[2]**2)
        if acc_raw_mag > self.max_acc_magnitude:
            return  # Reject anomalous burst

        # 3. Quaternion SLERP Smoothing (eliminates angle jitter)
        q = quat_slerp(self.filt_quat, q_raw, self.quat_smooth_alpha)
        self.filt_quat = q

        # 4. Acceleration Low-Pass Filtering
        for i in range(3):
            self.filt_acc[i] = self.filt_acc[i] * (1.0 - self.acc_smooth_alpha) + a_raw[i] * self.acc_smooth_alpha

        # 5. Background Gravity Calibration
        if not self.calibrated:
            self.calib_samples.append(acc_raw_mag)
            if len(self.calib_samples) >= 30:
                self.gravity_mag = sum(self.calib_samples) / len(self.calib_samples)
                self.calibrated = True

        # 6. Omnidirectional 3D Gravity Compensation
        g_body = compute_gravity_vector(q, self.gravity_mag)
        a_linear_body = [
            self.filt_acc[0] - g_body[0],
            self.filt_acc[1] - g_body[1],
            self.filt_acc[2] - g_body[2]
        ]

        # 7. Rotate linear acceleration into world coordinate frame
        a_world = quat_rotate_vector(q, a_linear_body)

        w_mag = math.sqrt(msg.angular_velocity.x**2 + msg.angular_velocity.y**2 + msg.angular_velocity.z**2)
        a_mag = math.sqrt(a_world[0]**2 + a_world[1]**2 + a_world[2]**2)

        # 8. Zero Velocity Update (ZUPT) - Stationary clamp
        if a_mag < self.acc_deadband and w_mag < self.gyro_deadband:
            self.stationary_ticks += 1
            if self.stationary_ticks > 3:
                self.vel = [0.0, 0.0, 0.0]
                a_world = [0.0, 0.0, 0.0]
        else:
            self.stationary_ticks = 0
            for i in range(3):
                if abs(a_world[i]) < self.acc_deadband:
                    a_world[i] = 0.0

        # 9. Velocity Integration (v = v + a * dt)
        self.vel[0] += a_world[0] * dt
        self.vel[1] += a_world[1] * dt
        self.vel[2] += a_world[2] * dt

        # 10. Cumulative Position Integration (p = p + v * dt)
        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt
        self.pos[2] += self.vel[2] * dt

        now_msg = now.to_msg()

        # 11. Dynamic TF Broadcast: odom -> base_link -> imu_link
        t_odom = TransformStamped()
        t_odom.header.stamp = now_msg
        t_odom.header.frame_id = 'odom'
        t_odom.child_frame_id = 'base_link'
        t_odom.transform.translation.x = self.pos[0]
        t_odom.transform.translation.y = self.pos[1]
        t_odom.transform.translation.z = self.pos[2]
        t_odom.transform.rotation.w = q[0]
        t_odom.transform.rotation.x = q[1]
        t_odom.transform.rotation.y = q[2]
        t_odom.transform.rotation.z = q[3]

        t_imu = TransformStamped()
        t_imu.header.stamp = now_msg
        t_imu.header.frame_id = 'base_link'
        t_imu.child_frame_id = 'imu_link'
        t_imu.transform.rotation.w = 1.0

        self.tf_broadcaster.sendTransform([t_odom, t_imu])

        # 12. Publish Odometry
        odom = Odometry()
        odom.header.stamp = now_msg
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.pos[0]
        odom.pose.pose.position.y = self.pos[1]
        odom.pose.pose.position.z = self.pos[2]
        odom.pose.pose.orientation.w = q[0]
        odom.pose.pose.orientation.x = q[1]
        odom.pose.pose.orientation.y = q[2]
        odom.pose.pose.orientation.z = q[3]
        odom.twist.twist.linear.x = self.vel[0]
        odom.twist.twist.linear.y = self.vel[1]
        odom.twist.twist.linear.z = self.vel[2]
        self.odom_pub.publish(odom)

        # 13. Append to 3D visual Path
        if curr_time - self.last_path_publish_time > 0.05:
            self.last_path_publish_time = curr_time
            pose = PoseStamped()
            pose.header.stamp = now_msg
            pose.header.frame_id = 'odom'
            pose.pose = odom.pose.pose
            self.path_msg.poses.append(pose)
            if len(self.path_msg.poses) > 1500:
                self.path_msg.poses.pop(0)
            self.path_msg.header.stamp = now_msg
            self.path_pub.publish(self.path_msg)

def main(args=None):
    rclpy.init(args=args)
    node = PureImuDeadReckoningNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
