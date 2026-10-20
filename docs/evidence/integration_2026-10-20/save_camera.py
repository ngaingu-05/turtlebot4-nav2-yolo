import rclpy,time,json
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from pathlib import Path
import cv2
r=Path(__file__).resolve().parent;rclpy.init();n=Node('report_camera_capture');b=CvBridge();latest={};saved=set();start=time.monotonic()
for t in ['oakd/rgb/preview/image_raw','yolo/detections/image']:
 n.create_subscription(Image,t,lambda m,t=t:latest.update({t:m}),qos_profile_sensor_data)
while time.monotonic()-start<300:
 rclpy.spin_once(n,timeout_sec=.1)
 log=(r/'combined_launch.log').read_text()
 if '[YOLO] chair' in log and 'chair' not in saved and len(latest)==2:
  for t,m in latest.items():cv2.imwrite(str(r/('yolo_chair.jpg' if t.startswith('yolo') else 'camera_rgb.jpg')),b.imgmsg_to_cv2(m,'bgr8'))
  saved.add('chair')
 if 'All navigation goals completed successfully' in log and 'chair' in saved:break
print('saved',list(saved));n.destroy_node();rclpy.shutdown()
