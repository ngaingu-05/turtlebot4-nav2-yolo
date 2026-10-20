"""Custom nodes only: start Gazebo, localization and Nav2 separately."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    defaults = {
        'use_sim_time': 'true',
        'goals_file': PathJoinSubstitution([FindPackageShare('tb4_simulation_lab'), 'config', 'navigation_goals.yaml']),
        'camera_topic': '/oakd/rgb/preview/image_raw',
        'yolo_model': 'models/yolov8n.pt',
        'confidence_threshold': '0.4', 'show_window': 'false',
    }
    shared = {'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)}
    return LaunchDescription([
        *[DeclareLaunchArgument(k, default_value=v) for k, v in defaults.items()],
        Node(package='tb4_simulation_lab', executable='navigation_node.py', output='screen',
             parameters=[shared, {'goals_file': LaunchConfiguration('goals_file')}]),
        Node(package='tb4_simulation_lab', executable='yolo_detection_node.py', output='screen',
             parameters=[shared, {
                 'camera_topic': LaunchConfiguration('camera_topic'),
                 'model_path': LaunchConfiguration('yolo_model'),
                 'confidence_threshold': ParameterValue(LaunchConfiguration('confidence_threshold'), value_type=float),
                 'show_window': ParameterValue(LaunchConfiguration('show_window'), value_type=bool),
             }]),
    ])
