# Phiên kiểm thử thực tế 20/10/2026

ROS 2 Jazzy, Gazebo Harmonic, world Depot, TurtleBot 4 Standard, ROS_DOMAIN_ID=42.

- Build PASS, 2/2 unit tests PASS.
- Undock SUCCEEDED. Khởi tạo AMCL bằng ground truth chỉ trong mô phỏng; node navigation vẫn dùng AMCL.
- 3/3 goal SUCCEEDED đúng thứ tự, tổng 139.81 giây thực; YOLO chạy đồng thời.
- Initial AMCL position error 0.00680543 m.
- 2226 message hazard_detection, 0 BUMP. Không nhận message bumper_contact; không coi kênh này là bằng chứng luồng contact hoạt động.
- Ghế static được thêm vào trước navigation theo chair_fixture_used.sdf, x=-0.52, y=-1.03, z=0, yaw=1.39. Camera sống nhận diện chair, confidence log cao nhất 0.86. Có false positive umbrella/suitcase.
- Ctrl+C sau hoàn tất gây KeyboardInterrupt khi detector cleanup publisher, exit -2. Log giữ nguyên; chưa sửa mã nguồn trong phiên test.
- Đã dừng các process do phiên test tạo; không để simulation/navigation chạy nền.

Ảnh: gazebo.png, localization_rviz.png, goal_1_rviz.png, goal_2_rviz.png, goal_3_rviz.png, camera_rgb.jpg, yolo_chair.jpg.
map_goals.png là hình vẽ từ map và tọa độ, không phải screenshot hoặc trajectory.
Ảnh mỗi goal được chụp khi đọc thấy succeeded trong log; goal tiếp theo tự động được gửi ngay nên ảnh có thể đã thể hiện chặng sau.

Log chính: combined_launch.log, localization.log, nav2.log, simulation.log, undock.log.
Số liệu: summary.json, interfaces.json, collision_summary.json, message_monitor.json.
record_poses.py bắt đầu sau khi Goal 1 đã được gửi; poses.json không phải toàn bộ hành trình.

PDF: ../../reports/Bao_cao_TurtleBot4_Nav2_YOLO_2026-10-20.pdf
Tạo lại PDF: python3 docs/evidence/integration_2026-10-20/create_report.py từ workspace.
Không chạy initialize_localization.py trên robot thật. Script chỉ phục vụ mô phỏng.
