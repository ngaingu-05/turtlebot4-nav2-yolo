import time,json,signal,math
from pathlib import Path
import rclpy,cv2
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.parameter import Parameter
from nav_msgs.msg import Odometry,OccupancyGrid
from sensor_msgs.msg import Image,LaserScan
from tf2_msgs.msg import TFMessage
from geometry_msgs.msg import PoseWithCovarianceStamped,TwistStamped
from cv_bridge import CvBridge
rclpy.init();n=Node('integration_evidence_monitor');n.set_parameters([Parameter('use_sim_time',value=True)])
root=Path('/home/nghia/turtlebot4/docs/evidence/integration_2026-10-15');counts={};latest={};errors=[];start=time.monotonic();stop=False
bridge=CvBridge()
for topic,typ in [('sim_ground_truth_pose',Odometry),('odom',Odometry),('map',OccupancyGrid),('amcl_pose',PoseWithCovarianceStamped),('scan',LaserScan),('oakd/rgb/preview/image_raw',Image),('yolo/detections/image',Image),('cmd_vel',TwistStamped),('tf',TFMessage),('tf_static',TFMessage)]:
 def callback(msg,t=topic):
  counts[t]=counts.get(t,0)+1;latest[t]=msg
  if t=='amcl_pose' and 'sim_ground_truth_pose' in latest:
   a=msg.pose.pose;b=latest['sim_ground_truth_pose'].pose.pose
   errors.append({'wall_elapsed_s':time.monotonic()-start,'position_error_m':math.hypot(a.position.x-b.position.x,a.position.y-b.position.y)})
  if t=='yolo/detections/image' and counts[t] in (1,50,100,200):cv2.imwrite(str(root/f'annotated_frame_{counts[t]}.jpg'),bridge.imgmsg_to_cv2(msg,'bgr8'))
 n.create_subscription(typ,topic,callback,qos_profile_sensor_data)
def halt(*_):
 global stop
 stop=True
signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGTERM,halt)
try:
 while not stop and time.monotonic()-start<600:rclpy.spin_once(n,timeout_sec=.2)
finally:
 (root/'message_monitor.json').write_text(json.dumps({'wall_duration_s':time.monotonic()-start,'message_counts':counts,'amcl_truth_errors':errors},indent=2))
 print('MONITOR',counts,flush=True);n.destroy_node();rclpy.shutdown()
