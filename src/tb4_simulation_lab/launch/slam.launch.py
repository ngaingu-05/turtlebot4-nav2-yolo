"""Run the upstream asynchronous SLAM launch with the lab parameters."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("params_file", default_value=PathJoinSubstitution([
            FindPackageShare("tb4_simulation_lab"), "config", "slam_toolbox_params.yaml",
        ])),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("autostart", default_value="true"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                FindPackageShare("slam_toolbox"), "launch", "online_async_launch.py",
            ])),
            launch_arguments={
                "slam_params_file": LaunchConfiguration("params_file"),
                "use_sim_time": LaunchConfiguration("use_sim_time"),
                "autostart": LaunchConfiguration("autostart"),
                "use_lifecycle_manager": "false",
            }.items(),
        ),
    ])
