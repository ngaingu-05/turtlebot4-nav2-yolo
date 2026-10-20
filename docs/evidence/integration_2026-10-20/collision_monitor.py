import rclpy,time,json,signal
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from irobot_create_msgs.msg import HazardDetectionVector
from ros_gz_interfaces.msg import Contacts
from pathlib import Path
rclpy.init();n=Node('report_collision_monitor');start=time.monotonic();stats={'hazard_messages':0,'bumper_messages':0,'bump_events':0,'nonempty_contacts':0,'events':[]};stop=False
def hazard(m):
 stats['hazard_messages']+=1
 for d in m.detections:
  if d.type==1:
   stats['bump_events']+=1;stats['events'].append({'elapsed':time.monotonic()-start,'type':'BUMP','frame':d.header.frame_id})
def contact(m):
 stats['bumper_messages']+=1
 if m.contacts:stats['nonempty_contacts']+=1
n.create_subscription(HazardDetectionVector,'hazard_detection',hazard,qos_profile_sensor_data)
n.create_subscription(Contacts,'bumper_contact',contact,qos_profile_sensor_data)
def halt(*a):
 global stop
 stop=True
signal.signal(signal.SIGINT,halt);signal.signal(signal.SIGTERM,halt)
while not stop and time.monotonic()-start<600:rclpy.spin_once(n,timeout_sec=.1)
stats['duration_s']=time.monotonic()-start;Path(__file__).with_name('collision_summary.json').write_text(json.dumps(stats,indent=2));n.destroy_node();rclpy.shutdown()
