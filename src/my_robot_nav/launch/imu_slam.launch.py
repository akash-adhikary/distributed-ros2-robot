import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    nav_pkg = get_package_share_directory('my_robot_nav')
    ekf_params_file = os.path.join(nav_pkg, 'config', 'ekf_imu_only.yaml')
    slam_params_file = os.path.join(nav_pkg, 'config', 'slam_toolbox_params.yaml')
    rviz_config_file = os.path.join(nav_pkg, 'config', 'fixed.rviz')
    
    return LaunchDescription([
        # QoS and Timestamp Relay
        Node(
            package='my_robot_nav',
            executable='qos_relay.py',
            name='qos_relay',
            output='screen'
        ),
        
        # Static Transforms
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'laser']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_imu',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'imu_link']
        ),
        
        # EKF Node for Odometry
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_params_file]
        ),
        
        # SLAM Toolbox
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params_file]
        ),
        
        # Activate SLAM Toolbox Lifecycle
        TimerAction(
            period=4.0,
            actions=[
                ExecuteProcess(
                    cmd=['bash', '-c',
                         'ros2 lifecycle set /slam_toolbox configure && '
                         'sleep 2 && '
                         'ros2 lifecycle set /slam_toolbox activate'],
                    output='screen'
                )
            ]
        ),
        
        # RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_file]
        )
    ])
