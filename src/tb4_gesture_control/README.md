# tb4_gesture_control — Assignment 6

ROS 2 Jazzy package for Ubuntu 24.04 and Gazebo Harmonic.

- `gesture_recognition_node`: webcam, MediaPipe Gesture Recognizer and temporal Wave detection.
- `robot_behavior_node`: selection, confirmation, motion, stop/cancel and signal/scan watchdogs.
- `simulation.launch.py`: empty arena and TurtleBot 4.
- `gesture.launch.py`: recognition and behavior nodes.
- `demo.launch.py`: simulator and gesture nodes in one launch session.

Install the Python dependencies in a system-site-packages venv and download the
MediaPipe model as described in the [workspace README](../../README.md).
Build using `colcon build --symlink-install --packages-select tb4_gesture_control`.
Run tests using `colcon test --packages-select tb4_gesture_control` followed by
`colcon test-result --verbose`.

Selection is held for five seconds for Thumb Up confirmation. While moving, loss
of valid gesture input for 0.8 seconds stops and cancels the behavior. Open Palm
stops immediately; Closed Fist cancels. The robot must be undocked and scan data
must be fresh and clear before a behavior can run.
