import os
from ament_index_python.packages import get_package_share_directory as share
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    resources = ':'.join([os.path.dirname(share('turtlebot4_description')),
                          os.path.dirname(share('irobot_create_description'))])
    return LaunchDescription([
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', resources),
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),
        SetEnvironmentVariable('EGL_PLATFORM', 'x11'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(
            os.path.join(share('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
            launch_arguments={'gz_args': os.path.join(share('tb4_gesture_control'), 'worlds',
                'gesture_arena.sdf') + ' -r --render-engine-server ogre2'}.items()),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            share('turtlebot4_gz_bringup'), 'launch', 'turtlebot4_spawn.launch.py')),
            launch_arguments={'world': 'gesture_arena', 'model': 'standard', 'rviz': 'false', 'nav2': 'false',
                              'slam': 'false', 'localization': 'false'}.items()),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock']),
    ])
