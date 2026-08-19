import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    nav_pkg = get_package_share_directory('my_robot_nav')
    slam_params_file = os.path.join(nav_pkg, 'config', 'handheld_slam_params.yaml')
    
    return LaunchDescription([
        # 1. QoS and Timestamp Relay
        Node(
            package='my_robot_nav',
            executable='qos_relay.py',
            name='qos_relay',
            output='screen'
        ),
        
        # 2. Fake Odometry
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='fake_odom_broadcaster',
            arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_footprint']
        ),
        
        # 3. Base to Laser Transform
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser_broadcaster',
            arguments=['0', '0', '0', '0', '0', '0', 'base_footprint', 'laser']
        ),
        
        # 4. SLAM Toolbox (lifecycle node, starts unconfigured)
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params_file, {'use_sim_time': False}]
        ),
        
        # 5. After 5 seconds, configure + activate SLAM via CLI
        TimerAction(
            period=5.0,
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
        
        # 6. RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen'
        )
    ])
