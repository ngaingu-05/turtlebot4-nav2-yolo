# Lịch sử kiểm tra trước khi chạy tích hợp

**Cập nhật:** Bảng dưới lưu kết quả của phiên trước. Kết quả mới nhất, đã có 3 goal thực và YOLO nhận diện ghế, ở [integration_test_results.md](integration_test_results.md).

# Kiểm tra ngày 15/10/2026

## Hiện trạng trước sửa

Một package ament_cmake, không có setup.py/setup.cfg. README/docs đã bị xóa ở lượt
trước theo yêu cầu dọn workspace; không có bằng chứng cũ trên đĩa để khôi phục.
Không xóa map, config hoặc evidence nào trong lần triển khai này. ROS Jazzy ở
/opt/ros/jazzy, Python 3.12.3. cv_bridge 4.1.0, nav2_simple_commander 1.3.13 có sẵn.
Ultralytics/PyTorch ban đầu chưa có. Localization mặc định trỏ map ngoài workspace;
script cũ bỏ qua goal lỗi và có thể báo hoàn tất dù có thất bại.

## Kết quả thực tế

| Kiểm tra | Trạng thái | Bằng chứng/giới hạn |
|---|---|---|
| colcon build --symlink-install | PASS | 1 package finished, lần đầu 1.52 s, lần sau 0.41 s |
| Python AST, YAML, package.xml, bash syntax | PASS | Parse toàn bộ source/config |
| Launch --show-args | PASS | autonomous_yolo và localization_navigation đọc được |
| Executable được cài | PASS | navigation_node.py, yolo_detection_node.py, send_nav_goals.py, check_topics.sh |
| Goal null bị từ chối | PASS | Executable trả exit 1, không gửi goal; xem unset_goals log |
| Không gửi Goal 3 khi Goal 2 lỗi | PASS | unittest mock giao thức, không phải thử robot |
| Giá trị goal bool/NaN/string/null | PASS | Kiểm tra load_goals từ chối |
| Map Depot giữ nguyên | PASS | SHA256 bên dưới |
| Gazebo spawn + controller | PASS | Robot được tạo, diffdrive controller active; có cảnh báo tốc độ update |
| Camera sống | PASS | Nhận Image rgb8 320×240, chuyển bgr8 và inference trên ảnh thật |
| Model load/inference CPU | PASS | YOLOv8n, torch 2.5.1+cpu, ultralytics 8.3.221 |
| Venv cùng ROS | PASS | import rclpy, cv_bridge, OpenCV 4.11, torch, ultralytics |
| Zero detections | PASS | Log detector nhận ảnh sống và in 0 detections định kỳ |
| Annotated image nhận qua subscriber ROS | PASS | 320×240 bgr8, frame oakd_rgb_camera_optical_frame; evidence/annotated_output_check.txt |
| Bounding box cho vật được nhận diện | NOT TESTED | Ảnh đã thử không phát hiện vật; không khẳng định nhận diện thành công |
| Map server nạp bản đồ | PASS | 604×304, 0.05 m/cell trong log thực |
| AMCL active và nhận map | PASS | Lifecycle localization báo active |
| AMCL định vị chính xác / map→base_link | NOT TESTED | Chưa đặt initial pose trong RViz |
| Toàn bộ Nav2 active | FAIL | Planner chờ map→base_link trong lần thử thiếu initial pose |
| 3 goal hợp lệ trong map | NOT TESTED | YAML để null có chủ đích, cần thu tọa độ/hướng thực |
| 3 navigation success thực | NOT TESTED | Không gửi goal khi chưa có dữ liệu hợp lệ |
| Navigation di chuyển đồng thời YOLO | NOT TESTED | Không có chuỗi goal hợp lệ để chạy |
| Cửa sổ GUI/box | NOT TESTED | Detector thử với show_window=false |

Ảnh `evidence/live_camera_probe.jpg` lấy từ camera robot thật trong Gazebo, inference
0 detections; không phải ảnh có bounding boxes. Smoke test riêng bằng ảnh đen chỉ
xác minh API/model/cv_bridge, không dùng làm minh chứng camera sống.

DDS cần thời gian discovery: topic list với --spin-time 5 thấy đầy đủ scan, odom,
tf/tf_static, dock_status, camera. Thử ngắn hơn ban đầu không thấy camera; không kết
luận camera thiếu dựa trên lần thử đó. Sandbox chặn socket DDS và ghi ~/.ros/log;
đã chạy runtime ngoài sandbox, log vào /tmp. Không thay ROS distribution.

## Map checksum

- map.pgm: `e3ec5ba8efae64a5112069ce5561a3451b345886fd23767e662101a5b688c860`
- map.yaml: `146a98668d0e57474a7258998064ff312a4bcfed30af989eeda4571aa9bb231d`

## Còn cần làm thủ công

Undock; đặt initial pose; chọn và thử ba x/y/yaw; xác minh lifecycle sau hội tụ;
chạy custom navigation và detector cùng nhau; quay minh chứng từng action result.
Nếu cần vật được YOLO nhận diện, thử góc nhìn/vật thể phù hợp COCO trong mô phỏng,
không thay camera bằng ảnh ghi sẵn. Không tự coi ngày thử này đã hoàn thành bài tập.
