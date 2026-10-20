import time,math,json,yaml
from pathlib import Path
import numpy as np,cv2
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan,Image
from geometry_msgs.msg import PoseWithCovarianceStamped,PoseStamped
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import ComputePathToPose
from rclpy.action import ActionClient
rclpy.init();n=Node('plan_integration_test');n.set_parameters([Parameter('use_sim_time',value=True)]); latest={}; counts={}
for t,c in [('sim_ground_truth_pose',Odometry),('amcl_pose',PoseWithCovarianceStamped),('scan',LaserScan),('yolo/detections/image',Image)]:
 def cb(m,t=t): latest[t]=m;counts[t]=counts.get(t,0)+1
 n.create_subscription(c,t,cb,qos_profile_sensor_data)
def wait(pred,seconds=40):
 end=time.monotonic()+seconds
 while not pred():
  if time.monotonic()>end:raise TimeoutError(str(counts))
  rclpy.spin_once(n,timeout_sec=.1)
wait(lambda:'sim_ground_truth_pose' in latest)
p=latest['sim_ground_truth_pose'].pose.pose
q=p.orientation;yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z));p.position.z=0.;q.x=q.y=0.;q.z=math.sin(yaw/2);q.w=math.cos(yaw/2)
pub=n.create_publisher(PoseWithCovarianceStamped,'initialpose',10)
msg=PoseWithCovarianceStamped();msg.header.frame_id='map';msg.pose.pose=p
msg.pose.covariance[0]=.04;msg.pose.covariance[7]=.04;msg.pose.covariance[35]=.02
publish_end=time.monotonic()+8.0
next_publish=0.0
while time.monotonic()<publish_end:
 if time.monotonic()>=next_publish:
  msg.header.stamp=n.get_clock().now().to_msg();pub.publish(msg);next_publish=time.monotonic()+.5
 rclpy.spin_once(n,timeout_sec=.1)
wait(lambda:'amcl_pose' in latest)
print('INITIAL_TRUTH',p,flush=True)
for _ in range(30):rclpy.spin_once(n,timeout_sec=.1)
a=latest['amcl_pose'].pose.pose;truth=latest['sim_ground_truth_pose'].pose.pose
err=math.hypot(a.position.x-truth.position.x,a.position.y-truth.position.y)
print('AMCL',a,'POSITION_ERROR_METRES',err,flush=True)
if err>.5:raise RuntimeError('AMCL disagrees with Gazebo truth; do not generate goals')
for name in ['amcl','map_server','planner_server','controller_server','bt_navigator','collision_monitor']:
 c=n.create_client(GetState,name+'/get_state');assert c.wait_for_service(timeout_sec=10)
 f=c.call_async(GetState.Request());wait(f.done);state=f.result().current_state
 print('LIFECYCLE',name,state.label,flush=True);assert state.id==3

Path('/home/nghia/turtlebot4/docs/evidence/integration_2026-10-20/localization.json').write_text(json.dumps({'initial_position_error_m':err,'amcl':{'x':a.position.x,'y':a.position.y},'truth':{'x':truth.position.x,'y':truth.position.y}},indent=2))
n.destroy_node();rclpy.shutdown()
