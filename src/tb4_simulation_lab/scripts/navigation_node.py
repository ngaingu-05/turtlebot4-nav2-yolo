#!/usr/bin/env python3
"""Bounded, fail-fast sequential navigation with BasicNavigator (Jazzy)."""
import math
from pathlib import Path
import sys
import time
import yaml
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from irobot_create_msgs.msg import DockStatus
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import NavigateToPose
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def load_goals(filename):
    with open(filename, encoding='utf-8') as stream:
        data = yaml.safe_load(stream)
    goals = data.get('goals') if isinstance(data, dict) else None
    if not isinstance(goals, list) or len(goals) < 3:
        raise ValueError('Configure at least THREE goals in goals_file')
    for i, goal in enumerate(goals, 1):
        if not isinstance(goal, dict) or any(
            isinstance(goal.get(k), bool) or not isinstance(goal.get(k), (int, float))
            or not math.isfinite(goal[k]) for k in ('x', 'y', 'yaw')
        ):
            raise ValueError(f'Goal {i} unset/invalid. Collect x,y using RViz Publish Point; yaw in radians. Edit goals_file.')
    return goals


class NavigationNode(BasicNavigator):
    def __init__(self):
        super().__init__(node_name='navigation_node')
        # Respect launch/CLI override; default to simulation time.
        if not self.has_parameter('use_sim_time'):
            self.declare_parameter('use_sim_time', True)
        elif 'use_sim_time' not in self._parameter_overrides:
            self.set_parameters([Parameter('use_sim_time', value=True)])
        defaults = {
            'goals_file': str(Path(get_package_share_directory('tb4_simulation_lab')) / 'config/navigation_goals.yaml'),
            'startup_timeout': 180.0, 'goal_timeout': 180.0,
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)
        self.dock_status = None
        self.dock_received_at = 0.0
        self.create_subscription(DockStatus, 'dock_status', self.on_dock, qos_profile_sensor_data)

    def on_dock(self, msg):
        self.dock_status = msg.is_docked
        self.dock_received_at = time.monotonic()

    def check_deadline(self, deadline):
        if not rclpy.ok():
            raise KeyboardInterrupt
        if time.monotonic() >= deadline:
            raise TimeoutError('Deadline exceeded. Check Nav2 lifecycle, AMCL initial pose, /clock and action server.')

    def await_future(self, future, deadline):
        while not future.done():
            self.check_deadline(deadline)
            rclpy.spin_once(self, timeout_sec=0.1)
        return future.result()

    def waitUntilNav2Active(self, navigator='bt_navigator', localizer='amcl'):
        # Upstream wait is unbounded and republishes a default initial pose.
        # Wait for user-localized AMCL instead, with a wall-clock deadline.
        deadline = time.monotonic() + self.get_parameter('startup_timeout').value
        for name in (localizer, navigator, 'planner_server', 'controller_server'):
            client = self.create_client(GetState, f'{name}/get_state')
            try:
                while True:
                    self.check_deadline(deadline)
                    if not client.wait_for_service(timeout_sec=0.2):
                        continue
                    response = self.await_future(client.call_async(GetState.Request()), deadline)
                    if response.current_state.id == 3:
                        break
                    rclpy.spin_once(self, timeout_sec=0.2)
            finally:
                self.destroy_client(client)
        while not self.initial_pose_received or self.get_clock().now().nanoseconds == 0 or self.dock_status is None:
            self.check_deadline(deadline)
            rclpy.spin_once(self, timeout_sec=0.1)
        self.require_undocked()

    def require_undocked(self):
        if self.dock_status is not False or time.monotonic() - self.dock_received_at > 5.0:
            raise RuntimeError('Docked or stale /dock_status. Run /undock action and wait for success before navigation.')

    def goToPose(self, pose, behavior_tree=''):
        deadline = time.monotonic() + 10.0
        while not self.nav_to_pose_client.wait_for_server(timeout_sec=0.2):
            self.check_deadline(deadline)
        goal = NavigateToPose.Goal()
        goal.pose, goal.behavior_tree = pose, behavior_tree
        self.goal_handle = self.await_future(self.nav_to_pose_client.send_goal_async(goal), deadline)
        if not self.goal_handle.accepted:
            raise RuntimeError('Nav2 rejected goal; stopping sequence')
        self.result_future = self.goal_handle.get_result_async()
        return True

    def cancel_bounded(self):
        if self.goal_handle and self.goal_handle.accepted and rclpy.ok():
            self.await_future(self.goal_handle.cancel_goal_async(), time.monotonic() + 3.0)

    def run(self):
        goals = load_goals(self.get_parameter('goals_file').value)
        for key in ('startup_timeout', 'goal_timeout'):
            value = self.get_parameter(key).value
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f'{key} must be finite and positive')
        self.info('[NAV] Waiting for Nav2... Set 2D Pose Estimate in RViz and undock.')
        self.waitUntilNav2Active()
        self.info('[NAV] Nav2 active')
        for i, goal in enumerate(goals, 1):
            self.require_undocked()
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x, pose.pose.position.y = float(goal['x']), float(goal['y'])
            pose.pose.orientation.z = math.sin(goal['yaw'] / 2.0)
            pose.pose.orientation.w = math.cos(goal['yaw'] / 2.0)
            self.info(f'[NAV] Navigating to Goal {i}')
            self.goToPose(pose)
            deadline = time.monotonic() + self.get_parameter('goal_timeout').value
            while not self.isTaskComplete():
                self.check_deadline(deadline)
            result = self.getResult()
            if result != TaskResult.SUCCEEDED:
                raise RuntimeError(f'[NAV] Goal {i} failed: {result}; sequence stopped')
            self.info(f'[NAV] Goal {i} succeeded')
        self.info('[NAV] All navigation goals completed successfully')


def main(args=None):
    # Keep context alive on SIGINT long enough to request action cancellation.
    from rclpy.signals import SignalHandlerOptions
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = None
    code = 0
    try:
        node = NavigationNode()
        node.run()
    except (KeyboardInterrupt, ExternalShutdownException):
        code = 130
    except Exception as exc:
        if node:
            node.get_logger().error(str(exc))
        else:
            print(str(exc), file=sys.stderr)
        code = 1
    finally:
        if node:
            try:
                if code:
                    node.cancel_bounded()
            except Exception as exc:
                node.get_logger().error(f'Cancellation unconfirmed: {exc}')
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return code


if __name__ == '__main__':
    sys.exit(main())
