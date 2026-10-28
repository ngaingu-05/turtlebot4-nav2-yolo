#!/usr/bin/env python3
"""Synthetic end-to-end control check in the running empty Gazebo arena."""
import json
import math
import time
import sys
import rclpy
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry
from std_msgs.msg import String

rclpy.init(); n=rclpy.create_node('lab6_sim_check')
pub=n.create_publisher(String,'/detected_gesture',1)
poses=[]; yaws=[]; status=['']; results=[]
def odom(m):
    poses.append((m.pose.pose.position.x,m.pose.pose.position.y))
    q=m.pose.pose.orientation
    yaws.append(math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)))
n.create_subscription(Odometry,'/odom',odom,qos_profile_sensor_data)
n.create_subscription(String,'/behavior_status',lambda m:status.__setitem__(0,m.data),1)


def pump(duration, gesture=None):
    end=time.monotonic()+duration
    while time.monotonic()<end:
        if gesture: pub.publish(String(data=gesture))
        cycle=time.monotonic()+.05
        while time.monotonic()<cycle:rclpy.spin_once(n,timeout_sec=.005)


try:
    pump(6,'None')
    assert poses, 'No odometry'
    behaviors=[('Pointing_Up','back_forth',120),('Victory','circle',180),('Wave','wave',60)]
    if '--wave-only' in sys.argv: behaviors=behaviors[-1:]
    for gesture, behavior, max_time in behaviors:
        pump(1.2,gesture)
        assert status[0]=='SELECTED: '+behavior,status[0]
        before=poses[-1]; start_index=len(poses)
        pump(1.2,'Thumb_Up')
        assert status[0]=='RUNNING: '+behavior,status[0]
        end=time.monotonic()+max_time
        while status[0]!='DONE' and time.monotonic()<end:
            pump(.1,'Thumb_Up')
        assert status[0]=='DONE',status[0]
        travel=sum(math.dist(a,b) for a,b in zip(poses[start_index:],poses[start_index+1:]))
        if behavior!='wave':assert travel>.3,(behavior,travel)
        yaw_span=max(yaws[start_index:])-min(yaws[start_index:])
        if behavior=='wave':assert yaw_span>.1,('No greeting rotation',yaw_span)
        results.append({'behavior':behavior,'result':'DONE','path_length_m':travel,
                        'start_xy':before,'end_xy':poses[-1],'yaw_span_rad':yaw_span})
        pump(.2,'None')
    print(json.dumps({'synthetic':True,'result':'PASS','behaviors':results},indent=2))
finally:
    pub.publish(String(data='Closed_Fist'));pump(.2)
    n.destroy_node();rclpy.shutdown()
