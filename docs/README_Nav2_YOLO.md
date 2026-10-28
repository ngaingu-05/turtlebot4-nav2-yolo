# TurtleBot 4: Nav2 và YOLO trên ROS 2 Jazzy

## Báo cáo và minh chứng mới nhất — 20/10/2026

Nguyễn Minh Nghĩa · MSSV **23020755** · Lớp **K68 E RE**.

- [Báo cáo PDF](reports/Bao_cao_TurtleBot4_Nav2_YOLO_2026-10-20.pdf)
- [Log, ảnh và kết quả kiểm thử mới](evidence/integration_2026-10-20/README.md)
- Phiên chạy mới: **3/3 goal SUCCEEDED**, **139,81 giây**, YOLO nhận diện `chair` với confidence cao nhất **0,86**.
- Không ghi nhận BUMP trong 2.226 message hazard; kênh bumper_contact không có message. Log có KeyboardInterrupt khi dừng detector sau nhiệm vụ; chi tiết nằm trong báo cáo.


Workspace `/home/nghia/turtlebot4`, Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic,
Python 3.12. Package hiện hữu `tb4_simulation_lab` dùng ament_cmake:
không cần setup.py/setup.cfg; CMake cài các executable Python, launch, config và map.
Giữ bản đồ Depot đã có, không ghi đè khi chạy. Xem kết quả kiểm tra thực tế trong
[docs/validation.md](validation.md). Phiên tích hợp ngày 15/10/2026 đã hoàn thành ba goal tuần tự cùng YOLO; xem log thực trong docs/evidence/integration_2026-10-15/.

## Kiến trúc

```mermaid
flowchart TD
 G[Gazebo Depot + TurtleBot 4] --> L[LiDAR /scan]
 G --> O[Odometry /odom + TF]
 G --> C[RGB /oakd/rgb/preview/image_raw]
 M[Map YAML + PGM] --> A[AMCL]
 L --> A
 O --> A
 A --> T[map → odom → base_link]
 T --> N[Nav2]
 L --> N
 U[navigation_node BasicNavigator] -->|NavigateToPose: Goal 1 → 2 → 3| N
 N -->|TwistStamped /cmd_vel| G
 C --> Y[yolo_detection_node CPU worker]
 Y --> I[/yolo/detections/image + class/confidence logs]
```

Nav2 dùng NavFn A*, DWB, costmap và collision monitor. Node navigation kiểm tra
lifecycle AMCL/BT/planner/controller, chờ pose AMCL, clock và dock_status; không tự
phát initial pose mặc định. Mỗi goal phải nhận SUCCEEDED mới gửi goal tiếp theo.
Timeout theo đồng hồ thực, lỗi thì dừng chuỗi và yêu cầu hủy action đang chạy.
Detector ở process riêng, callback chỉ thay frame mới nhất, inference CPU 2 Hz,
2 thread, không phát vận tốc. Input dùng sensor-data QoS; output bgr8 giữ header ảnh gốc.

## Dependency và build

Kiểm tra ứng viên trước khi cài; chỉ dùng gói Jazzy:

```bash
source /opt/ros/jazzy/setup.bash
apt-cache policy ros-jazzy-turtlebot4-simulator ros-jazzy-nav2-simple-commander ros-jazzy-cv-bridge
sudo apt update
sudo apt install ros-jazzy-turtlebot4-simulator ros-jazzy-turtlebot4-bringup \
  ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-nav2-simple-commander \
  ros-jazzy-slam-toolbox ros-jazzy-cv-bridge ros-jazzy-ros-gz-bridge \
  ros-jazzy-joy-linux ros-jazzy-teleop-twist-keyboard \
  python3-opencv python3-yaml python3-venv python3-colcon-common-extensions
cd /home/nghia/turtlebot4
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --symlink-install
source install/setup.bash
```

Ultralytics không có ứng viên apt trong lần kiểm tra. Dùng venv riêng với các module
hệ thống để không mất rclpy/cv_bridge; không sửa Python hệ thống. NumPy <2 giữ ABI
với cv_bridge trên máy này. Cài torch CPU trước để tránh tải CUDA không cần thiết.

```bash
cd /home/nghia/turtlebot4
python3 -m venv --system-site-packages .venv-yolo
.venv-yolo/bin/python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
.venv-yolo/bin/python -m pip install -r requirements-yolo.txt
source /opt/ros/jazzy/setup.bash
.venv-yolo/bin/python -c 'import rclpy, cv_bridge, cv2, torch; from ultralytics import YOLO; print("Imports OK")'
mkdir -p models
curl -fL https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt -o models/yolov8n.pt
```

Tham khảo cách cài từ [Ultralytics chính thức](https://docs.ultralytics.com/quickstart/).
Node yêu cầu file model tồn tại; không tự tải khi startup. Không commit weights,
venv, build/install/log hoặc rosbag. Model COCO có thể không nhận ra nhiều vật thể
Gazebo; không có detection vẫn là một frame inference hợp lệ, không phải bằng chứng nhận diện thành công.

## Chạy hệ thống: ba terminal

Mỗi terminal ROS cần:

```bash
cd /home/nghia/turtlebot4
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Terminal 1 — Gazebo, robot, bridge và RViz:

```bash
ros2 launch tb4_simulation_lab gazebo_rviz.launch.py world:=depot model:=standard joy:=false
```

Dùng Ogre2 để tránh lỗi scan toàn range_min từng gặp với Ogre1. Không chạy thêm
simulator/bridge thứ hai. Chờ các cảm biến xuất hiện. Robot trên dock: thực hiện
undock và đợi action kết thúc thành công trước khi chạy nhiệm vụ:

```bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'
ros2 topic echo /dock_status --once
```

Nếu E-stop đang bật, kiểm tra trong mô phỏng rồi mới tắt:

```bash
ros2 service call /e_stop irobot_create_msgs/srv/EStop '{e_stop_on: false}'
```

Terminal 2 — map có sẵn, AMCL và đúng một Nav2 stack:

```bash
ros2 launch tb4_simulation_lab localization_navigation.launch.py
```

RViz: Fixed Frame `map`, dùng **2D Pose Estimate** tại vị trí/hướng thực của robot.
Đối chiếu laser với tường, kiểm tra hạt hội tụ và `/amcl_pose`. Không chạy SLAM
cùng AMCL. Có thể truyền `map:=/đường/dẫn/map.yaml`; mặc định dùng map trong package.

Terminal 3 — sau khi cấu hình goals:

```bash
source .venv-yolo/bin/activate
ros2 launch tb4_simulation_lab autonomous_yolo.launch.py \
  goals_file:=/home/nghia/turtlebot4/src/tb4_simulation_lab/config/navigation_goals.yaml \
  camera_topic:=/oakd/rgb/preview/image_raw \
  yolo_model:=/home/nghia/turtlebot4/models/yolov8n.pt \
  confidence_threshold:=0.4 show_window:=false
```

Executable dùng `#!/usr/bin/env python3`, vì vậy kích hoạt venv **trước** launch
để process YOLO lấy đúng interpreter. Không cần build lại dưới venv. Hai node ở
process riêng: navigation kết thúc không làm dừng detector. Nếu navigation lỗi,
đọc log, sửa nguyên nhân và chạy lại; detector vẫn hoạt động độc lập.

## Chọn ít nhất ba goal có thật

Sửa `src/tb4_simulation_lab/config/navigation_goals.yaml`. `x,y` tính bằng mét
trong `map`; `yaw` tính bằng **radian**. File hiện đã có ba goal lấy từ vùng trống trên map Depot, đường đi được planner xác minh; yaw tính theo tiếp tuyến cuối đường. Goal 3 quay về pose AMCL đã đo sau undock. Log chọn goal: docs/evidence/integration_2026-10-15/goal_selection.json. Nếu thay world/map, phải chọn lại; null hoặc giá trị không hợp lệ sẽ bị từ chối.

1. RViz Fixed Frame `map`, chọn **Publish Point**, nhấn một vùng trống đủ rộng.
2. Đọc tọa độ:

```bash
ros2 topic echo /clicked_point --once
```

3. Đến vị trí và hướng mong muốn bằng RViz Nav2 Goal, chờ thành công rồi đọc pose:

```bash
ros2 topic echo /amcl_pose --once
```

Quaternion `(x,y,z,w)` đổi yaw bằng
`atan2(2*(w*z+x*y), 1-2*(y*y+z*z))`. Tọa độ AMCL là vị trí thực đã đến,
Publish Point là vị trí chọn; ghi rõ cách thu thập. Kiểm tra khoảng cách an toàn
trên costmap và thử từng đích trong RViz trước. Không teleop đồng thời với Nav2.
Không chuyển sang đích tiếp theo nếu đích trước chưa thành công.

Chạy navigation riêng (tên executable cũ cũng dùng cùng implementation):

```bash
ros2 run tb4_simulation_lab navigation_node.py --ros-args \
  -p use_sim_time:=true \
  -p goals_file:=/home/nghia/turtlebot4/src/tb4_simulation_lab/config/navigation_goals.yaml \
  -p startup_timeout:=180.0 -p goal_timeout:=180.0
```

`send_nav_goals.py` là alias, nay nhận goals_file, không còn goals_json độ như trước.
Chỉ log `[NAV] Goal N succeeded` khi kết quả action thực sự thành công;
`[NAV] All navigation goals completed successfully` chỉ sau tất cả goals thành công.

## Camera và YOLO riêng

Topic mặc định lấy từ file bridge **đã cài** của turtlebot4_gz_bringup, không suy đoán.
Model khai báo RGBD 320×240, 30 Hz; tần số thực tùy tải mô phỏng. Kiểm tra trực tiếp:

```bash
ros2 topic list -t
ros2 topic info /oakd/rgb/preview/image_raw -v
ros2 topic hz /oakd/rgb/preview/image_raw
ros2 topic echo /oakd/rgb/preview/image_raw --once --field header
```

Kiểu cần là `sensor_msgs/msg/Image`. Namespace khác: dùng topic thực từ `topic list`
và truyền `camera_topic`. Launch hiện cấu hình một robot ở namespace gốc; chưa xác
nhận đa robot/namespaced bringup. Không thêm bridge trùng với bridge camera gốc.

```bash
source .venv-yolo/bin/activate
ros2 run tb4_simulation_lab yolo_detection_node.py --ros-args \
  -p use_sim_time:=true -p camera_topic:=/oakd/rgb/preview/image_raw \
  -p model_path:=/home/nghia/turtlebot4/models/yolov8n.pt \
  -p show_window:=false -p inference_rate:=2.0 -p image_size:=320
ros2 topic hz /yolo/detections/image
```

Xem `/yolo/detections/image` bằng RViz Image hoặc chạy node với `show_window:=true`
trên phiên desktop X11 hợp lệ. Headless/Wayland: ưu tiên false vì Qt có thể abort
khi DISPLAY tồn tại nhưng không truy cập được. Ảnh vẫn được publish khi tắt cửa sổ.
Log ví dụ **định dạng**, không phải kết quả đo: `[YOLO] <class> <confidence>` hoặc
`[YOLO] 0 detections`. Log giới hạn mỗi 3 giây.

## Kiểm tra, lỗi thường gặp và minh chứng

```bash
ros2 run tb4_simulation_lab check_topics.sh
ros2 topic list -t
ros2 node list
ros2 action list -t
ros2 lifecycle get /amcl
ros2 lifecycle get /bt_navigator
ros2 lifecycle get /planner_server
ros2 lifecycle get /controller_server
ros2 run tf2_ros tf2_echo map base_link
ros2 topic echo /amcl_pose --once
```

Cần map, scan, odom, tf, tf_static, cmd_vel, amcl_pose và action navigate_to_pose.
Clock phải tăng; map→odom do AMCL cung cấp. `check_topics.sh` chỉ là kiểm tra sơ bộ,
không chứng minh robot đến đích hoặc YOLO hoạt động.

- Goal unset: chọn đủ x,y,yaw; không thay null bằng số ngẫu nhiên.
- Waiting for Nav2: kiểm tra lifecycle, pose, clock, dock_status; đặt pose sau undock.
- Goal lỗi/timeout: kiểm tra costmap, đường đi, TF và tải CPU. Không tự bỏ qua goal.
- Không thấy ảnh: chờ spawn hoàn tất, kiểm tra camera_bridge và topic thực; xem log Gazebo.
- LiDAR sai: giữ Ogre2; không sửa package hệ thống.
- Không import ultralytics: kích hoạt venv trước ros2 run/launch.
- NumPy ABI: giữ numpy<2 và opencv-python<4.12; kiểm tra import cv_bridge trong venv.
- Model thiếu: tải file bằng lệnh trên; node dừng kèm đường dẫn cần sửa.
- Fuel tải chậm: `gz fuel download -u https://fuel.gazebosim.org/1.0/OpenRobotics/models/Depot`.
- Sandbox chặn DDS hoặc thư mục log: chạy trên desktop bình thường; khi cần đặt
  `export ROS_LOG_DIR=/tmp/tb4_ros_logs` cho log ở đường dẫn ghi được.

Lưu log mới bằng `2>&1 | tee docs/evidence/<ten_phien>.txt`. Chụp Gazebo Depot,
RViz localization, từng goal **sau thành công**, ảnh YOLO có box nếu thực sự phát hiện.
Ghi model, threshold, topic, số frame, tần số thực và trạng thái action. Không dùng
ảnh mẫu/prerecorded thay minh chứng camera trực tiếp. Không có kết quả thì ghi
NOT TESTED hoặc FAIL, không dựng screenshot. Mẫu báo cáo: [docs/report_outline.md](report_outline.md).

## Kết quả kiểm thử tích hợp mới

Phiên 15/10/2026: Gazebo Depot, undock SUCCEEDED, AMCL và toàn bộ Nav2 active;
map→base_link hợp lệ. Sai lệch vị trí ban đầu AMCL với ground truth khoảng 0,009 m.
Ba goal có kết quả SUCCEEDED theo thứ tự trong navigation.log. Camera RGB 320×240,
YOLO CPU và subscriber ảnh annotated hoạt động trong khi robot di chuyển.

Depot nguyên trạng cho 0 detections ở các góc nhìn đã thử. Sau lần navigation đầu,
đã thêm **tạm thời model Chair từ cache Fuel** trước robot để thử nhận diện dương
tính: ảnh camera sống có box `chair 0.87`. Đây là cảnh thử có thêm ghế, không phải
khẳng định Depot nguyên trạng có sẵn ghế này. Không ghi thay đổi vào map hoặc world
gốc; khởi động lại Gazebo sẽ trở về Depot ban đầu. Xem
[ảnh thực](evidence/integration_2026-10-15/chair_live_annotated.jpg) và
[kết quả chi tiết](integration_test_results.md).

Ground truth Gazebo chỉ dùng để khởi tạo/đối chiếu AMCL trong test. Node navigation
vẫn dùng AMCL và Nav2. Khi thao tác thông thường, đặt 2D Pose Estimate trong RViz.

Lượt chạy launch tích hợp đã xác minh thêm 3/3 goal (146,04 giây thực). GUI đã
được sửa để chỉ hiển thị trên main thread và thử lại thành công; thiếu model/camera
được xử lý có thông báo. Mô phỏng đã dừng sau khi kiểm thử; chạy lại bằng ba terminal ở trên.
