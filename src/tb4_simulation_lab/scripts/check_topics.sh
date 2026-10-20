#!/usr/bin/env bash
# ============================================================================
# Script kiểm tra các topic ROS 2 của TurtleBot 4 Simulation
# Bài thực hành 04 – TurtleBot 4 Simulation cơ bản
#
# Script này kiểm tra:
#   1. /scan  (LiDAR)  – phải là sensor_msgs/msg/LaserScan
#   2. /odom  (Odometry) – phải là nav_msgs/msg/Odometry
#   3. /cmd_vel (Velocity command) – geometry_msgs/msg/TwistStamped (Jazzy)
#   4. /tf và /tf_static – kiểm tra TF tree hoạt động
#   5. /map (nếu SLAM hoặc map_server đang chạy)
#
# Cách dùng:
#   source /opt/ros/jazzy/setup.bash
#   source ~/turtlebot4/install/setup.bash
#   ros2 run tb4_simulation_lab check_topics.sh
#
# Biến môi trường:
#   WAIT_SECONDS – thời gian chờ message (mặc định: 10 giây)
# ============================================================================
set -euo pipefail

# Thời gian chờ tối đa khi đợi message từ topic (giây)
readonly WAIT_SECONDS="${WAIT_SECONDS:-10}"

# Màu sắc cho output dễ đọc
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# ============================================================================
# Hàm tiện ích
# ============================================================================

# Hàm thông báo lỗi và thoát
fail() {
  printf "${RED}❌ LỖI: %s${NC}\n" "$*" >&2
  exit 1
}

# Hàm thông báo thành công
ok() {
  printf "${GREEN}✅ OK: %s${NC}\n" "$*"
}

# Hàm thông báo cảnh báo
warn() {
  printf "${YELLOW}⚠️  CHÚ Ý: %s${NC}\n" "$*"
}

# Hàm thông báo thông tin
info() {
  printf "${CYAN}ℹ️  %s${NC}\n" "$*"
}

# Kiểm tra ros2 có trên PATH không
command -v ros2 >/dev/null 2>&1 || \
  fail "ros2 không có trên PATH. Chạy 'source /opt/ros/jazzy/setup.bash' trước."

# ============================================================================
# Hàm kiểm tra kiểu dữ liệu topic
# Đối số: $1 = tên topic, $2 = kiểu dữ liệu mong đợi
# ============================================================================
check_type() {
  local topic="$1"
  local expected_type="$2"
  local actual_type

  actual_type="$(ros2 topic type "$topic" 2>/dev/null)" ||
    fail "Topic $topic không tồn tại hoặc chưa được tạo."
  [[ "$actual_type" == "$expected_type" ]] ||
    fail "$topic có kiểu $actual_type; mong đợi $expected_type."
  ok "$(printf '%-12s kiểu = %s' "$topic" "$actual_type")"
}

# ============================================================================
# Hàm kiểm tra topic có publisher đang hoạt động
# Đối số: $1 = tên topic
# ============================================================================
check_has_publisher() {
  local topic="$1"
  local details
  details="$(ros2 topic info "$topic" 2>/dev/null)" ||
    fail "Không thể truy vấn $topic."
  grep -Eq 'Publisher count: [1-9][0-9]*' <<<"$details" ||
    fail "$topic không có publisher nào đang hoạt động."
  ok "$(printf '%-12s publisher đang hoạt động' "$topic")"
}

# ============================================================================
# Hàm kiểm tra topic có nhận được message trong thời gian chờ
# Đối số: $1 = tên topic, $2 = thời gian chờ (giây)
# ============================================================================
check_receives_message() {
  local topic="$1"
  local timeout="$2"
  timeout "$timeout" ros2 topic echo "$topic" --once >/dev/null 2>&1 ||
    fail "Không nhận được message trên $topic trong ${timeout}s. Kiểm tra Gazebo đã khởi động chưa."
  ok "$(printf '%-12s nhận được message thành công' "$topic")"
}

# ============================================================================
# Hàm kiểm tra tần số publish của topic
# Đối số: $1 = tên topic
# ============================================================================
check_hz() {
  local topic="$1"
  info "Đang đo tần số $topic (5 giây)..."
  timeout 6 ros2 topic hz "$topic" --window 10 2>/dev/null | head -3 || true
}

# ============================================================================
# BẮT ĐẦU KIỂM TRA
# ============================================================================
echo ""
printf "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}\n"
printf "${CYAN}║  Kiểm tra Topic TurtleBot 4 – ROS 2 Jazzy                  ║${NC}\n"
printf "${CYAN}║  Thời gian chờ: %-3ss                                       ║${NC}\n" "$WAIT_SECONDS"
printf "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}\n"
echo ""

# --- 1. Kiểm tra /scan (LiDAR) ---
info "=== Kiểm tra /scan (LiDAR sensor) ==="
check_type /scan sensor_msgs/msg/LaserScan
check_has_publisher /scan
check_receives_message /scan "$WAIT_SECONDS"
echo ""

# --- 2. Kiểm tra /odom (Odometry) ---
info "=== Kiểm tra /odom (Odometry) ==="
check_type /odom nav_msgs/msg/Odometry
check_has_publisher /odom
check_receives_message /odom "$WAIT_SECONDS"
echo ""

# --- 3. Kiểm tra /cmd_vel (Velocity Command) ---
info "=== Kiểm tra /cmd_vel (Lệnh vận tốc) ==="
if cmd_vel_type="$(ros2 topic type /cmd_vel 2>/dev/null)" && [[ -n "$cmd_vel_type" ]]; then
  # TurtleBot 4 trên ROS 2 Jazzy sử dụng TwistStamped thay vì Twist
  [[ "$cmd_vel_type" == "geometry_msgs/msg/TwistStamped" ]] ||
    fail "/cmd_vel có kiểu $cmd_vel_type; mong đợi geometry_msgs/msg/TwistStamped cho cấu hình Jazzy Nav2."
  ok "$(printf '%-12s kiểu = %s' "/cmd_vel" "$cmd_vel_type")"

  # Kiểm tra subscriber – robot cần có subscriber để nhận lệnh
  cmd_vel_info="$(ros2 topic info /cmd_vel)"
  if grep -Eq 'Subscription count: [1-9][0-9]*' <<<"$cmd_vel_info"; then
    ok "/cmd_vel có subscriber đang hoạt động – robot sẵn sàng nhận lệnh."
  else
    warn "/cmd_vel không có subscriber. Kiểm tra robot bridge/base interface."
  fi
else
  warn "/cmd_vel chưa hoạt động. Khởi chạy teleop hoặc Nav2 rồi kiểm tra lại."
fi
echo ""

# --- 4. Kiểm tra /tf và /tf_static ---
info "=== Kiểm tra TF ==="
if ros2 topic type /tf >/dev/null 2>&1; then
  ok "/tf đang hoạt động"
else
  warn "/tf chưa có – TF tree có thể chưa sẵn sàng."
fi

if ros2 topic type /tf_static >/dev/null 2>&1; then
  ok "/tf_static đang hoạt động"
else
  warn "/tf_static chưa có."
fi
echo ""

# --- 5. Kiểm tra /map (nếu SLAM hoặc map_server đang chạy) ---
info "=== Kiểm tra /map (Bản đồ) ==="
if map_type="$(ros2 topic type /map 2>/dev/null)" && [[ -n "$map_type" ]]; then
  ok "$(printf '%-12s kiểu = %s (SLAM hoặc map_server đang phát bản đồ)' "/map" "$map_type")"
else
  warn "/map chưa hoạt động – bình thường nếu chưa chạy SLAM hoặc map_server."
fi
echo ""

# --- 6. Kiểm tra /amcl_pose (nếu AMCL đang chạy) ---
info "=== Kiểm tra /amcl_pose (Localization) ==="
if amcl_type="$(ros2 topic type /amcl_pose 2>/dev/null)" && [[ -n "$amcl_type" ]]; then
  ok "$(printf '%-12s kiểu = %s (AMCL đang hoạt động)' "/amcl_pose" "$amcl_type")"
else
  warn "/amcl_pose chưa hoạt động – bình thường nếu chưa chạy localization."
fi
echo ""

# --- Kết luận ---
printf "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}\n"
printf "${GREEN}║  ✅ Kiểm tra topic hoàn tất!                                ║${NC}\n"
printf "${GREEN}║  Robot motion cần xác minh trực tiếp trong Gazebo.          ║${NC}\n"
printf "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}\n"
echo ""

# Liệt kê tất cả topic đang hoạt động để tham khảo
info "Danh sách tất cả topic đang hoạt động:"
ros2 topic list -t 2>/dev/null | head -30
echo ""
