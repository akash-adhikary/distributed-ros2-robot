import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    nav_pkg = get_package_share_directory('my_robot_nav')
    slam_params_file = os.path.join(nav_pkg, 'config', 'slam_toolbox_params.yaml')
    rviz_config_file = os.path.join(nav_pkg, 'config', 'mapping.rviz')
    
    return LaunchDescription([
        # 1. QoS Relay, Continuous 50Hz Odometry (odom -> base_link) & Static Sensor TFs
        Node(
            package='my_robot_nav',
            executable='qos_relay.py',
            name='qos_relay',
            output='screen'
        ),
        
        # 2. SLAM Toolbox: Real-Time Async Mapping & Loop Closure (map -> odom)
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params_file]
        ),
        
        # 3. Deterministic Lifecycle Activator (Transitions slam_toolbox to ACTIVE state)
        TimerAction(
            period=1.2,
            actions=[
                ExecuteProcess(
                    cmd=['bash', '-c',
                         'ros2 lifecycle set /slam_toolbox configure 2>/dev/null || true; '
                         'sleep 0.5; '
                         'ros2 lifecycle set /slam_toolbox activate 2>/dev/null || true'],
                    output='screen'
                )
            ]
        ),
        
        # 4. RViz2 Visualizer
        TimerAction(
            period=2.5,
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
