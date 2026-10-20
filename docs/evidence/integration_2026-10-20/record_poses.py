import rclpy,time,json,signal,math
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from pathlib import Path
r=Path(__file__).resolve().parent;rclpy.init();n=Node('report_pose_recorder');rows=[];latest={};start=time.monotonic();stop=False
for t,c in [('amcl',PoseWithCovarianceStamped),('truth',Odometry)]:
 def cb(m,t=t):
  latest[t]=m
  if t=='amcl':
   p=m.pose.pose;row={'elapsed_s':time.monotonic()-start,'x':p.position.x,'y':p.position.y}
   if 'truth' in latest:
    b=latest['truth'].pose.pose;row['truth_x']=b.position.x;row['truth_y']=b.position.y
   rows.append(row)
 n.create_subscription(c,'amcl_pose' if t=='amcl' else 'sim_ground_truth_pose',cb,qos_profile_sensor_data)
def halt(*a):
 global stop
 stop=True
signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGTERM,halt)
while not stop and time.monotonic()-start<300:rclpy.spin_once(n,timeout_sec=.1)
(r/'poses.json').write_text(json.dumps(rows,indent=2));n.destroy_node();rclpy.shutdown()
