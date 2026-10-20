# Đề cương báo cáo

1. **Giới thiệu:** TurtleBot 4 trong Depot, Ubuntu 24.04 / ROS 2 Jazzy / Gazebo Harmonic.
2. **Mục tiêu:** AMCL, Nav2 ba đích tuần tự và YOLO camera sống đồng thời.
3. **Kiến trúc:** sơ đồ trong README; TF map→odom→base_link; luồng camera độc lập.
4. **Cấu trúc package:** ament_cmake, launch/config/maps/scripts; dependency ROS và venv.
5. **AMCL:** map có sẵn, initial pose, hạt hội tụ, đối chiếu laser và tường.
6. **Nav2:** NavFn A*, DWB, costmap, collision monitor, lifecycle.
7. **Quản lý goal:** YAML x/y/yaw radian, tối thiểu ba goal; success gate, timeout và hủy.
8. **Camera:** RGBD sensor, bridge Gazebo→ROS, sensor_msgs/Image, QoS.
9. **YOLO:** YOLOv8n CPU, worker ảnh mới nhất, bounding box, class và confidence.
10. **Topics/actions:** scan, odom, clock, map, amcl_pose, tf, tf_static, cmd_vel,
    oakd/rgb/preview/image_raw, yolo/detections/image, navigate_to_pose, undock.
11. **Phương pháp thử:** build, kiểm tra tĩnh, dependency, lifecycle, từng đích,
    ảnh đầu vào/đầu ra thực; phân biệt smoke test ảnh đen và camera sống.
12. **Kết quả:** điền từ docs/validation.md và log thực; không dùng kết quả lịch sử
    làm kết quả của phiên hiện tại. Bảng mỗi goal: tọa độ, yaw, thời gian, action status.
13. **Hạn chế:** tốc độ mô phỏng theo tải CPU và domain gap COCO/Gazebo; nhận diện dương tính đã thử với model Chair bổ sung tạm thời.
14. **Kết luận:** chỉ khẳng định phần đã đo; liệt kê việc còn cần thử.

## Vị trí dành cho ảnh thực tế

- [CHƯA CÓ ẢNH] Depot Gazebo: `images/depot_gazebo.png`.
- [CHƯA CÓ ẢNH] RViz map + AMCL: `images/amcl_localization.png`.
- [CHƯA CÓ ẢNH] Goal 1 thành công: `images/goal_1.png`.
- [CHƯA CÓ ẢNH] Goal 2 thành công: `images/goal_2.png`.
- [CHƯA CÓ ẢNH] Goal 3 thành công: `images/goal_3.png`.
- [CHƯA CÓ ẢNH] Camera sống có YOLO box: `images/yolo_live.png`.

Các vị trí trên là placeholder, không phải file ảnh đã tạo. Thêm log gốc vào evidence/.

## Kết quả đã có của phiên tích hợp

Xem [integration_test_results.md](integration_test_results.md). Ba goal tuần tự thành công,
YOLO CPU đồng thời; ảnh ghế có box/class/confidence là ảnh camera sống trong cảnh
kiểm thử có thêm Chair. Không đổi các placeholder screenshot từng goal thành ảnh
giả; log action là minh chứng cho từng goal, ảnh RViz hiện chỉ chụp một thời điểm.
