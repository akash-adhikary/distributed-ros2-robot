import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    pkg_gazebo = get_package_share_directory('my_robot_gazebo')
    pkg_description = get_package_share_directory('my_robot_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_file = os.path.join(pkg_gazebo, 'worlds', 'obstacles.sdf')

    # Launch Configurations
    headless = LaunchConfiguration('headless')

    # Declare headless launch argument (Default to true for stable container simulation)
    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='true',
        description='Run Gazebo Sim server-only (no GUI) to prevent OpenGL crashes'
    )

    # 1. Gazebo Sim (headless/server-only if headless:=true)
    gz_args_expr = PythonExpression([
        "'-r -s ' + '", world_file, "' if '", headless, "' == 'true' else '-r ' + '", world_file, "'"
    ])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': gz_args_expr}.items()
    )

    # 2. Robot State Publisher
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_description, 'launch', 'rsp.launch.py')
        ),
        launch_arguments={'use_sim_time': 'true'}.items()
    )

    # 3. Spawn robot (delayed 3s so Gazebo world loads first)
    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-topic', 'robot_description',
                    '-name', 'my_robot',
                    '-x', '0.0', '-y', '0.0', '-z', '0.05'
                ],
                output='screen'
            )
        ]
    )

    # 4. ROS-Gazebo bridge (delayed 5s so robot is spawned first)
    #    Bridges direct root-level topics between ROS and Gazebo.
    gz_bridge = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                arguments=[
                    '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                    '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                    '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                    '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                    '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
                    '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
                ],
                parameters=[{'use_sim_time': True}],
                output='screen'
            )
        ]
    )

    # 5. Static TF link to bridge Gazebo nested sensor frame to ROS TF tree
    static_tf_laser = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_laser',
        arguments=['0', '0', '0', '0', '0', '0', 'laser_frame', 'my_robot/base_footprint/laser_frame'],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        declare_headless,
        gz_sim,
        rsp,
        static_tf_laser,
        spawn_robot,
        gz_bridge,
    ])
