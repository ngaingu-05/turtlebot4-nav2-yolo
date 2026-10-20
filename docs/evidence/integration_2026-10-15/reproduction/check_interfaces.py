import time,json,math
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data,QoSProfile,DurabilityPolicy,ReliabilityPolicy
from sensor_msgs.msg import Image,LaserScan
from nav_msgs.msg import Odometry,OccupancyGrid
from geometry_msgs.msg import PoseWithCovarianceStamped,TwistStamped
from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer,TransformListener
from lifecycle_msgs.srv import GetState
rclpy.init();n=Node('validate_interfaces');n.set_parameters([Parameter('use_sim_time',value=True)])
b=Buffer();listener=TransformListener(b,n);data={};counts={}
latched=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
for t,c in [('map',OccupancyGrid),('amcl_pose',PoseWithCovarianceStamped),('scan',LaserScan),('odom',Odometry),('tf',TFMessage),('tf_static',TFMessage),('cmd_vel',TwistStamped),('oakd/rgb/preview/image_raw',Image),('yolo/detections/image',Image),('sim_ground_truth_pose',Odometry)]:
 def cb(m,t=t):data[t]=m;counts[t]=counts.get(t,0)+1
 n.create_subscription(c,t,cb,latched if t in ('map','amcl_pose','tf_static') else qos_profile_sensor_data)
start=time.monotonic()
while time.monotonic()-start<15:rclpy.spin_once(n,timeout_sec=.1)
results={'message_counts':counts,'wall_duration_s':time.monotonic()-start}
for topic in ('map','amcl_pose','scan','odom','tf','tf_static','cmd_vel','oakd/rgb/preview/image_raw','yolo/detections/image'):
 results[topic]={'status':'PASS' if topic in data else 'FAIL'}
 if topic in data and isinstance(data[topic],Image):
  m=data[topic];results[topic].update(width=m.width,height=m.height,encoding=m.encoding,data_bytes=len(m.data))
if 'map' in data:
 m=data['map'];results['map'].update(width=m.info.width,height=m.info.height,resolution=m.info.resolution)
if 'scan' in data:
 m=data['scan'];ranges=[r for r in m.ranges if math.isfinite(r) and m.range_min<=r<=m.range_max]
 results['scan'].update(rays=len(m.ranges),finite_valid=len(ranges),minimum=min(ranges) if ranges else None,maximum=max(ranges) if ranges else None)
try:
 t=b.lookup_transform('map','base_link',rclpy.time.Time());results['map_to_base_link']={'status':'PASS','x':t.transform.translation.x,'y':t.transform.translation.y}
except Exception as exc:results['map_to_base_link']={'status':'FAIL','error':str(exc)}
results['lifecycle']={}
for name in ('amcl','map_server','planner_server','controller_server','bt_navigator','collision_monitor'):
 client=n.create_client(GetState,name+'/get_state')
 if client.wait_for_service(timeout_sec=3):
  f=client.call_async(GetState.Request());end=time.monotonic()+5
  while not f.done() and time.monotonic()<end:rclpy.spin_once(n,timeout_sec=.1)
  results['lifecycle'][name]=f.result().current_state.label if f.done() else 'TIMEOUT'
 else:results['lifecycle'][name]='UNAVAILABLE'
print(json.dumps(results,indent=2),flush=True)
Path('/home/nghia/turtlebot4/docs/evidence/integration_2026-10-15/interfaces.json').write_text(json.dumps(results,indent=2))
n.destroy_node();rclpy.shutdown()
