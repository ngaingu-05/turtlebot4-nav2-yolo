#!/usr/bin/env python3
"""Run on isolated ROS_DOMAIN_ID=43; synthetic inputs, never the demo."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys
import time
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped

scripts = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(scripts))
loader = importlib.machinery.SourceFileLoader('behavior', str(scripts / 'robot_behavior_node'))
spec = importlib.util.spec_from_loader('behavior', loader)
module = importlib.util.module_from_spec(spec)
loader.exec_module(module)
rclpy.init()
b = module.Behavior()
n = rclpy.create_node('synthetic_lab6_check')
executor = SingleThreadedExecutor(); executor.add_node(b); executor.add_node(n)
gestures = n.create_publisher(String, '/detected_gesture', 1)
scans = n.create_publisher(LaserScan, '/scan', qos_profile_sensor_data)
commands = []
n.create_subscription(TwistStamped, '/cmd_vel', lambda m: commands.append((m.twist.linear.x, m.twist.angular.z)), 10)


def pump(seconds, gesture=None, clear=True, scan=True):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if scan:
            m = LaserScan(); m.range_min=.05; m.range_max=10.; m.ranges=[float('inf') if clear else .2]*360
            scans.publish(m)
        if gesture is not None:
            gestures.publish(String(data=gesture))
        cycle = time.monotonic() + .05
        while time.monotonic() < cycle:
            executor.spin_once(timeout_sec=.005)


try:
    pump(2, 'None')
    pump(.7, 'Victory')
    assert b.core.selected == 'circle' and b.core.active is None
    assert commands[-1] == (0., 0.)
    pump(.7, 'Thumb_Up')
    assert commands[-1] == (.12, .3)
    pump(.15, 'Open_Palm')
    assert commands[-1] == (0., 0.) and b.core.active is None
    pump(.6, 'Pointing_Up'); pump(.6, 'Thumb_Up')
    assert commands[-1][0] > 0
    pump(1.1, None)
    assert commands[-1] == (0., 0.) and b.core.active is None
    pump(.6, 'Victory'); pump(.6, 'Thumb_Up'); pump(.2, 'Closed_Fist')
    assert commands[-1] == (0., 0.) and b.core.selected is None
    pump(.6, 'Victory'); pump(.6, 'Thumb_Up'); pump(.2, 'Thumb_Up', clear=False)
    assert commands[-1] == (0., 0.) and b.core.active is None
    pump(.2, 'None'); pump(.6, 'Victory'); pump(.6, 'Thumb_Up')
    pump(1.2, 'Thumb_Up', scan=False)
    assert commands[-1] == (0., 0.) and b.core.active is None
    print(json.dumps({'result':'PASS','synthetic':True,'cmd_messages':len(commands),
        'checks':['selection requires confirmation','circle velocity','immediate palm stop',
                  'signal timeout','fist cancel','obstacle stop','stale scan stop']}, indent=2))
finally:
    executor.shutdown(); b.destroy_node(); n.destroy_node(); rclpy.shutdown()
