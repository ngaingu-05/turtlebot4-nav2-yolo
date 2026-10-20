# Công cụ của phiên kiểm thử

Các script lưu lại chính thao tác kiểm tra đã dùng, không thuộc node vận hành.
Chạy với Python hệ thống sau source ROS Jazzy, trong mô phỏng Depot đã khởi động.
Chúng truy cập workspace /home/nghia/turtlebot4, không dùng trên robot thật.

- `select_and_check_goals.py`: lấy ground truth để đặt initial pose của AMCL
  (chỉ cho mô phỏng), đo sai lệch, kiểm tra lifecycle, chọn đích từ map có khoảng
  hở và kiểm tra 3 đường với planner. **Ghi đè navigation_goals.yaml** bằng kết quả
  chọn mới và ghi goal_selection.json; chỉ chạy khi muốn chọn lại goals.
  Phải undock và chờ thành công trước khi chạy. E-stop chỉ tắt sau khi xác nhận mô phỏng.
- `check_interfaces.py`: nhận message và kiểm tra TF/lifecycle, ghi interfaces.json.
- `monitor.py`: đếm message, lưu một số frame thật và sai lệch AMCL so với ground truth;
  Ctrl+C kết thúc, ghi message_monitor.json.

Không dùng ground truth thay AMCL trong node navigation. Ground truth chỉ khởi tạo
và đối chiếu AMCL ở phiên test; Nav2 vận hành bằng AMCL/scan/odom như bình thường.
