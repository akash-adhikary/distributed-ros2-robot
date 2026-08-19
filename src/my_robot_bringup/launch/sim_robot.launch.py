import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('my_robot_bringup')
    pkg_gazebo = get_package_share_directory('my_robot_gazebo')
    
    use_rviz = LaunchConfiguration('use_rviz')
    headless = LaunchConfiguration('headless')
    
    # 1. Include Gazebo simulation launch (spawns robot & ROS-Gazebo bridge)
    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'sim.launch.py')
        ),
        launch_arguments={'headless': headless}.items()
    )
    
    # 2. RViz2 visualization
    rviz_config_file = os.path.join(pkg_bringup, 'config', 'robot_sim.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
        output='screen'
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Launch RViz2 for visualization'
        ),
        DeclareLaunchArgument(
            'headless',
            default_value='true',
            description='Run Gazebo Sim server-only (no GUI) to prevent OpenGL crashes'
        ),
        sim,
        rviz
    ])
