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
        # 1. SLAM Toolbox: Real-Time Async Mapping
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params_file]
        ),

        # 2. Deterministic Lifecycle Activator (configure + activate)
        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=['bash', '-c',
                         'source /opt/ros/jazzy/setup.bash 2>/dev/null || true; '
                         'export ROS_DOMAIN_ID=42; '
                         'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp; '
                         'export CYCLONEDDS_URI=file:///home/ros/my_robot_ws/cyclonedds.xml; '
                         'ros2 lifecycle set /slam_toolbox configure 2>/dev/null || true; '
                         'sleep 1.0; '
                         'ros2 lifecycle set /slam_toolbox activate 2>/dev/null || true'],
                    output='screen'
                )
            ]
        ),

        # 3. RViz2 Visualizer (after slam_toolbox transitions to active)
        TimerAction(
            period=4.5,
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
