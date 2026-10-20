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
root=Path('/home/nghia/turtlebot4');mp=root/'src/tb4_simulation_lab/maps';m=yaml.safe_load((mp/'map.yaml').read_text());im=cv2.imread(str(mp/'map.pgm'),0)
res=m['resolution'];ox,oy,_=m['origin'];h,w=im.shape
d=cv2.distanceTransform((im>250).astype('uint8'),cv2.DIST_L2,5)*res
# Map-derived candidate cell centres: safe connected region around measured pose.
ys,xs=np.indices(im.shape);wx=ox+(xs+.5)*res;wy=oy+(h-ys-.5)*res
dist=np.hypot(wx-a.position.x,wy-a.position.y)
safe=(d>.7)&(dist>1.5)&(dist<2.2)
count,labels=cv2.connectedComponents((d>.45).astype('uint8'))
row=h-1-int((a.position.y-oy)/res);col=int((a.position.x-ox)/res)
safe &= labels==labels[row,col]
indices=np.argwhere(safe)
if not len(indices):raise RuntimeError('No safe candidates')
# Prefer clearance for first goal; second must also be separated from first.
r,c=max(indices,key=lambda rc:float(d[tuple(rc)]));g1=(float(wx[r,c]),float(wy[r,c]))
sep=np.hypot(wx-g1[0],wy-g1[1]);indices2=np.argwhere(safe&(sep>2.0))
if not len(indices2):raise RuntimeError('No separated second goal')
r2,c2=max(indices2,key=lambda rc:float(d[tuple(rc)]));g2=(float(wx[r2,c2]),float(wy[r2,c2]))
# Return to actually observed undocked pose only when map clearance is sufficient.
if d[row,col]<.5:raise RuntimeError('Return pose has inadequate map clearance')
points=[g1,g2,(a.position.x,a.position.y)]
client=ActionClient(n,ComputePathToPose,'compute_path_to_pose');assert client.wait_for_server(timeout_sec=15)
start=PoseStamped();start.header.frame_id='map';start.pose=a;goals=[];records=[]
for i,(x,y) in enumerate(points,1):
 goal=PoseStamped();goal.header.frame_id='map';goal.pose.position.x=x;goal.pose.position.y=y;goal.pose.orientation.w=1.
 request=ComputePathToPose.Goal();request.start=start;request.goal=goal;request.use_start=True;request.planner_id='GridBased'
 f=client.send_goal_async(request);wait(f.done);handle=f.result();assert handle.accepted
 f=handle.get_result_async();wait(f.done,30);result=f.result();assert result.status==4 and len(result.result.path.poses)>1
 path=result.result.path.poses
 # Derive requested final yaw from final nonzero path segment (map geometry).
 last=path[-1].pose.position;prev=next(p.pose.position for p in reversed(path[:-1]) if math.hypot(last.x-p.pose.position.x,last.y-p.pose.position.y)>.05)
 heading=math.atan2(last.y-prev.y,last.x-prev.x)
 goals.append(dict(name=f'goal_{i}',x=float(x),y=float(y),yaw=float(heading)))
 records.append(dict(goal=i,path_poses=len(path),planner_status=int(result.status)))
 goal.pose.orientation.z=math.sin(heading/2);goal.pose.orientation.w=math.cos(heading/2);start=goal
 print('PATH_VALID',goals[-1],records[-1],flush=True)
file=root/'src/tb4_simulation_lab/config/navigation_goals.yaml'
file.write_text('# Selected from saved Depot free cells with clearance >0.7 m; return to measured AMCL pose.\n# Paths verified with ComputePathToPose; yaw from final path tangent (radians).\n'+yaml.safe_dump({'goals':goals},sort_keys=False))
(root/'docs/evidence/integration_2026-10-15/goal_selection.json').write_text(json.dumps({'initial_position_error_m':err,'goals':goals,'plans':records,'message_counts':counts},indent=2))
print('GOALS_CONFIGURED',file,flush=True)
n.destroy_node();rclpy.shutdown()
