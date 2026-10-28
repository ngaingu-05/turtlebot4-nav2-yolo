# Kiểm tra Bài 6 — 28/10/2026

Môi trường thực: Ubuntu 24.04.5 LTS, ROS 2 Jazzy, Gazebo Harmonic,
Python 3.12, MediaPipe 0.10.21, OpenCV 4.11.0, NumPy 1.26.4.

- `colcon build --symlink-install --packages-select tb4_gesture_control`: PASS.
- `python3 -m pytest src/tb4_gesture_control/test -q`: 7 PASS.
- Package đã đăng ký pytest vào CMake; `colcon test --packages-select
  tb4_gesture_control` và `colcon test-result --verbose`: 0 lỗi/thất bại.
- ROS integration dùng publisher tổng hợp, domain 43: 7 tình huống PASS,
  chi tiết `ros_integration.json`. Không phát lệnh vào robot của domain 42.
- Webcam thật mở được, MediaPipe tải model và chạy inference; ảnh `webcam.png`.
  Ảnh có landmark nhưng confidence cử chỉ ở thời điểm chụp dưới ngưỡng,
  nên nhãn `None` là kết quả đúng theo bộ lọc. Chưa đo accuracy 6 cử chỉ.
- Gazebo spawn robot và activate controller; scan 640 mẫu hoạt động.
  `+inf` trên sàn trống nghĩa là không có vật cản trong tầm quét, không phải lỗi.
  Xem `simulation_probe.json` và `gazebo.png`.
- Bài thử chuyển động dùng cử chỉ tổng hợp: **PASS cả 3 hành vi**; xem
  `simulation_behaviors.json`. Tiến–lùi đi 1,33 m, vòng tròn đi 2,46 m.
  Kiểm tra chào riêng qua odometry: biên độ yaw 0,499 rad (`simulation_wave.json`). Đây không phải video nhận diện bằng tay thật.
- `pip check` thấy xung đột yt-dlp/websockets thuộc gói hệ thống được venv kế thừa;
  import rclpy, OpenCV và MediaPipe đã chạy được. Không sửa các gói không liên quan.

## Dọn thư mục

Đã bỏ log build cũ, cache Python trong source và `.venv-yolo` cũ (~1,2 GB).
Môi trường YOLO có thể cài lại theo `requirements-yolo.txt` và hướng dẫn cũ.
Giữ nguyên source bài cũ, maps, model YOLO, ảnh/log minh chứng trong docs và
thay đổi tên PDF có sẵn của người dùng. README bài cũ chuyển vào
`docs/README_Nav2_YOLO.md`; README gốc tập trung Bài 6.
`.venv-gesture`, `models`, `build/install/log` không commit.

## Tái lập kiểm thử

```bash
source /opt/ros/jazzy/setup.bash
python3 -m pytest src/tb4_gesture_control/test -q
ROS_DOMAIN_ID=43 python3 src/tb4_gesture_control/test/check_ros_integration.py
# Chỉ chạy lệnh sau khi simulator và behavior đã hoạt động, camera node đã dừng:
python3 src/tb4_gesture_control/test/check_simulation.py
python3 docs/lab6/create_report.py
```

Các lần phát triển đã gặp lỗi Sensors nạp trùng và bridge trỏ nhầm world;
source cuối đã loại plugin trùng và truyền đúng `world:=gesture_arena`.
Đóng sạch phiên Gazebo trước khi chạy lại; không chạy nhiều server/controller.
Khi mô phỏng chậm, thời lượng hành vi tính theo ROS clock nên thời gian thực dài hơn.

## Kịch bản video cần quay bằng tay thật

1. Hiển thị đồng thời Gazebo và cửa sổ webcam, giải thích topic và confidence.
2. Giơ 1 ngón: trạng thái SELECTED, robot chưa chạy. Giơ ngón cái: tiến–lùi 4 cặp.
3. Giữ ngón cái: robot không tự chạy lặp sau khi DONE.
4. Victory → Thumb Up: một vòng tròn hoàn chỉnh.
5. Vẫy tay trái–phải đủ biên độ → SELECTED wave → Thumb Up: robot chào.
6. Chọn lại một hành vi, xác nhận, xòe tay: robot dừng.
7. Chọn/xác nhận, nắm tay: robot hủy, về chờ; ngón cái đơn lẻ không chạy lại.
8. Chọn/xác nhận, đưa tay ra khỏi khung hoặc che camera: robot dừng.
9. Không dùng bàn phím điều khiển robot trong các bước demo.

Video tay thật đủ 6 cử chỉ và URL video Bài 6 còn cần bổ sung.
Source nằm trên nhánh `assignment-6-hand-gesture`; xem `links.md`.
Điền `submission.json`, chụp thêm các hành vi thật và chạy lại script tạo PDF.

## Sửa thao tác chuyển cử chỉ

Lựa chọn nay được giữ 5 giây để chuyển từ cử chỉ chọn sang Thumb Up.
Watchdog mất tín hiệu 0,8 giây vẫn áp dụng khi robot đang chạy.
Bài thử tổng hợp trên Gazebo: Victory → None 1,3 giây → Thumb Up → Closed Fist
đã PASS; robot dịch chuyển 0,109 m rồi về IDLE (`hand_transition_test.json`).
Cửa sổ webcam hiển thị hướng dẫn khi không thấy trọn bàn tay hoặc confidence thấp.
