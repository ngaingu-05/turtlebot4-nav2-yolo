"""One launch session for the arena and live gesture control."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    directory = os.path.join(get_package_share_directory('tb4_gesture_control'), 'launch')
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(directory, 'simulation.launch.py'))),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(directory, 'gesture.launch.py'))),
    ])
