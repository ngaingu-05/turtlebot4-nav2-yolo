from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import os


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('python', default_value=os.path.expanduser('~/turtlebot4/.venv-gesture/bin/python')),
        DeclareLaunchArgument('gesture_model', default_value=os.path.expanduser('~/turtlebot4/models/gesture_recognizer.task')),
        DeclareLaunchArgument('camera', default_value='0'),
        DeclareLaunchArgument('confidence', default_value='0.65'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('stamped', default_value='true'),
        Node(package='tb4_gesture_control', executable='gesture_recognition_node',
             prefix=[LaunchConfiguration('python'), ' '], output='screen',
             parameters=[{'model': LaunchConfiguration('gesture_model'),
                          'confidence': ParameterValue(LaunchConfiguration('confidence'), value_type=float),
                          'camera': ParameterValue(LaunchConfiguration('camera'), value_type=int)}]),
        Node(package='tb4_gesture_control', executable='robot_behavior_node', output='screen',
             parameters=[{'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
                          'stamped': ParameterValue(LaunchConfiguration('stamped'), value_type=bool)}]),
    ])
