#!/usr/bin/env python3
"""Latest-frame CPU YOLO worker; inference never runs in subscription callbacks."""
import math
import os
from pathlib import Path
import sys
import threading
import time

import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class YoloDetectionNode(Node):
    def __init__(self):
        super().__init__('yolo_detection_node')
        defaults = dict(camera_topic='/oakd/rgb/preview/image_raw',
                        model_path='models/yolov8n.pt', confidence_threshold=0.4,
                        image_size=320, show_window=False, inference_rate=2.0,
                        log_interval=3.0, cpu_threads=2)
        for key, value in defaults.items():
            self.declare_parameter(key, value)
        self.settings = {key: self.get_parameter(key).value for key in defaults}
        for key in ('inference_rate', 'log_interval'):
            if not math.isfinite(self.settings[key]) or self.settings[key] <= 0:
                raise ValueError(f'{key} must be finite and positive')
        if not 0 < self.settings['confidence_threshold'] <= 1:
            raise ValueError('confidence_threshold must be in (0, 1]')
        if self.settings['image_size'] < 32 or self.settings['cpu_threads'] < 1:
            raise ValueError('image_size >= 32 and cpu_threads >= 1 required')
        model_path = Path(self.settings['model_path']).expanduser().resolve()
        if not model_path.is_file():
            raise FileNotFoundError(f'Model missing: {model_path}. Download yolov8n.pt as documented in README; no automatic download during node startup.')
        from ultralytics import YOLO
        import torch
        torch.set_num_threads(self.settings['cpu_threads'])
        self.model = YOLO(str(model_path))
        self.bridge = CvBridge()
        self.lock = threading.Lock()
        self.latest = None
        self.preview = None
        self.last_received = time.monotonic()
        self.stop = threading.Event()
        self.failure = None
        self.publisher = self.create_publisher(Image, '/yolo/detections/image', 1)
        self.subscription = self.create_subscription(
            Image, self.settings['camera_topic'], self.receive, qos_profile_sensor_data)
        self.create_timer(5.0, self.health)
        self.show = self.settings['show_window']
        # Qt can abort the process before cv2.error if no display is available.
        if self.show and not os.environ.get('DISPLAY'):
            self.get_logger().warning('No DISPLAY: disabling OpenCV window; image topic remains enabled.')
            self.show = False
        if self.show:
            self.create_timer(0.1, self.display_frame)
        self.worker = threading.Thread(target=self.process, name='yolo_worker')
        self.worker.start()
        self.get_logger().info(f'[YOLO] Model loaded on CPU; subscribing to {self.settings["camera_topic"]}')

    def receive(self, msg):
        with self.lock:
            self.latest = msg
            self.last_received = time.monotonic()

    def health(self):
        if self.failure:
            self.get_logger().error(f'[YOLO] Worker failed: {self.failure}')
            raise RuntimeError(self.failure)
        if time.monotonic() - self.last_received > 5:
            self.get_logger().warning('[YOLO] No recent RGB frames. Check camera topic, bridge and Gazebo.')

    def process(self):
        last_log = 0.0
        try:
            while not self.stop.is_set() and rclpy.ok():
                start = time.monotonic()
                with self.lock:
                    msg, self.latest = self.latest, None
                if msg is not None:
                    frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                    result = self.model.predict(
                        frame, device='cpu', imgsz=self.settings['image_size'],
                        conf=self.settings['confidence_threshold'], verbose=False)[0]
                    annotated = result.plot(labels=True, conf=True)
                    output = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
                    output.header = msg.header
                    self.publisher.publish(output)
                    if start - last_log >= self.settings['log_interval']:
                        items = [f'{result.names[int(box.cls.item())]} {box.conf.item():.2f}'
                                 for box in result.boxes]
                        self.get_logger().info('[YOLO] ' + (', '.join(items) or '0 detections'))
                        last_log = start
                    if self.show:
                        with self.lock:
                            self.preview = annotated
                self.stop.wait(max(0.01, 1.0 / self.settings['inference_rate'] - (time.monotonic() - start)))
        except Exception as exc:
            if not self.stop.is_set():
                self.failure = str(exc)

    def display_frame(self):
        # OpenCV/Qt GUI must run on the executor's main thread.
        with self.lock:
            frame, self.preview = self.preview, None
        if frame is not None and self.show:
            try:
                cv2.imshow('TurtleBot 4 YOLO', frame)
                cv2.waitKey(1)
            except cv2.error as exc:
                self.get_logger().warning(f'Window disabled: {exc}')
                cv2.destroyAllWindows()
                self.show = False

    def destroy_node(self):
        self.stop.set()
        self.worker.join()
        if self.show:
            cv2.destroyAllWindows()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    code = 0
    try:
        node = YoloDetectionNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except Exception as exc:
        print(f'[YOLO] {exc}', file=sys.stderr)
        code = 1
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return code


if __name__ == '__main__':
    sys.exit(main())
