import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    nav_pkg = get_package_share_directory('my_robot_nav')
    ekf_params_file = os.path.join(nav_pkg, 'config', 'ekf_imu_only.yaml')
    slam_params_file = os.path.join(nav_pkg, 'config', 'slam_toolbox_params.yaml')
    rviz_config_file = os.path.join(nav_pkg, 'config', 'mapping.rviz')
    
    return LaunchDescription([
        # 1. QoS, Local Timestamp & SLERP Jitter Filter Relay
        Node(
            package='my_robot_nav',
            executable='qos_relay.py',
            name='qos_relay',
            output='screen'
        ),
        
        # 2. Static Transform Publishers (base_link to sensors)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser',
            arguments=['0', '0', '0.1', '0', '0', '0', 'base_link', 'laser']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser_frame',
            arguments=['0', '0', '0.1', '0', '0', '0', 'base_link', 'laser_frame']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_imu',
            arguments=['0', '0', '0.05', '0', '0', '0', 'base_link', 'imu_link']
        ),
        
        # 3. EKF Node for Odometry & Rotational Heading (odom -> base_link)
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_params_file]
        ),
        
        # 4. SLAM Toolbox: Real-Time Async Mapping & Loop Closure (map -> odom)
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params_file]
        ),
        
        # 5. Deterministic Lifecycle Activator (Transitions slam_toolbox to ACTIVE state)
        TimerAction(
            period=1.5,
            actions=[
                ExecuteProcess(
                    cmd=['bash', '-c',
                         'ros2 lifecycle set /slam_toolbox configure 2>/dev/null || true; '
                         'sleep 0.8; '
                         'ros2 lifecycle set /slam_toolbox activate 2>/dev/null || true'],
                    output='screen'
                )
            ]
        ),
        
        # 6. RViz2 Visualizer (Starts after SLAM is ACTIVE to guarantee 'map' frame exists)
        TimerAction(
            period=3.5,
            actions=[
                Node(
                    package='rviz2',
                    executable='rviz2',
                    name='rviz2',
                    output='screen',
                    arguments=['-d', rviz_config_file]
                )
            ]
        )
    ])
