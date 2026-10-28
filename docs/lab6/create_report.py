"""Generate the Vietnamese report without inventing demo evidence."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont('VN', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('VNB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
c = canvas.Canvas(str(ROOT / 'report.pdf'), pagesize=(595,842))
c.setTitle('Bài 6 — Giao tiếp phi ngôn ngữ và điều khiển TurtleBot 4')
y=795

def line(text='', size=10):
    global y
    c.setFont('VN',size);c.drawString(42,y,text);y-=18

def title(text):
    global y
    y-=9;c.setFont('VNB',13);c.drawString(42,y,text);y-=25

def page():
    global y
    c.showPage();y=795

title('BÀI 6 — ĐIỀU KHIỂN TURTLEBOT 4 BẰNG CỬ CHỈ')
line('Nguyễn Minh Nghĩa — MSSV 23020755 — 28/10/2026')
line('Ubuntu 24.04 LTS · ROS 2 Jazzy · Gazebo Harmonic · Python 3.12')
title('1. Mục tiêu và kiến trúc')
line('Webcam nhận cử chỉ tay; robot chỉ chuyển động sau khi chọn và xác nhận.')
boxes=[(45,'Webcam'),(212,'MediaPipe + Wave'),(395,'Behavior FSM')]
for x,label in boxes:
    c.rect(x,y-30,150,40);c.setFont('VN',9);c.drawCentredString(x+75,y-13,label)
for a,b in [(195,212),(362,395)]:
    c.line(a,y-10,b,y-10);c.line(b-5,y-7,b,y-10);c.line(b-5,y-13,b,y-10)
y-=62
line('Webcam → gesture_recognition_node → /detected_gesture (String)')
line('→ robot_behavior_node → /cmd_vel (TwistStamped) → TurtleBot 4/Gazebo')
line('/scan (LaserScan) → kiểm tra an toàn; /clock → thời lượng chuyển động.')
line('/behavior_status (String) → trạng thái hiển thị trên ảnh webcam.')
title('2. Mô hình nhận diện và chống nhiễu')
line('OpenCV đọc ảnh 640×480 và lật gương. MediaPipe Gesture Recognizer')
line('chạy VIDEO trên CPU, trả lớp cử chỉ, confidence và 21 landmark bàn tay.')
line('Ngưỡng confidence 0,65. Chọn/xác nhận ổn định 0,35 giây mới kích hoạt.')
line('Latch theo cử chỉ: giữ nguyên tay không phát lại lệnh thực thi.')
line('Wave: Open Palm + cổ tay đổi hướng ≥2 lần trong 1,5 giây; mỗi đoạn')
line('dịch ≥0,10 bề rộng ảnh. Đây là quy tắc thời gian, không phải lớp AI riêng.')
line('Điểm hiển thị của Wave là confidence phân loại Open Palm nền.')
title('3. Ánh xạ cử chỉ và hành vi')
for s in ['Wave: chọn chào; xoay trái–phải 4 pha × 1 giây, ±0,5 rad/s.',
          'Pointing Up: chọn tiến–lùi 4 cặp, ±0,12 m/s, mỗi lượt 1,5 giây.',
          'Victory: chọn vòng tròn R=0,4 m; v=0,12 m/s, ω=0,3 rad/s.',
          'Thumb Up: xác nhận hành vi đã chọn và bắt đầu thực hiện.',
          'Open Palm: dừng ngay khi nhận callback và xóa lựa chọn.',
          'Closed Fist: hủy, xóa lựa chọn và về trạng thái chờ.']:
    line(s)
page()
title('4. Nguyên lý điều khiển và an toàn')
for s in ['Máy trạng thái: IDLE → SELECTED → RUNNING → DONE; dừng/hủy/mất',
          'tín hiệu đưa về trạng thái không chuyển động, phải chọn/xác nhận lại.',
          'Timer steady 20 Hz; mất tín hiệu khi đang chạy 0,8 giây → dừng.',
          'Lựa chọn được giữ 5 giây để chuyển sang cử chỉ Thumb Up xác nhận.',
          'Thời lượng dùng ROS clock để phù hợp tốc độ mô phỏng; reset clock → dừng.',
          'LiDAR mới ≤1 giây, mọi điểm hợp lệ >0,55 m; lỗi/vật cản → dừng.',
          'World mặt sàn 30×30 m, không đồ đạc; robot cần undock trước demo.',
          'Open Palm có ưu tiên dừng ngay cả khi đang bắt đầu vẫy tay.',
          'Không dùng Nav2, không điều khiển robot bằng bàn phím khi demo.',
          'Điều khiển vòng hở có sai số quỹ đạo; LiDAR là hàng rào dừng bảo thủ.',
          'Nếu behavior process bị kill, cần timeout ở controller downstream.']:
    line(s)
title('5. Kết quả kiểm tra và phần thực nghiệm còn thiếu')
line('Build ament_cmake thành công; 7 kiểm thử logic độc lập đã PASS.')
p=ROOT/'ros_integration.json'
if p.exists() and p.stat().st_size:
    result=json.loads(p.read_text())
    line('Kiểm thử ROS với dữ liệu tổng hợp: '+result['result']+'.')
    line('Kiểm tra chọn/xác nhận, vận tốc, dừng, hủy, mất tín hiệu và LiDAR.')
p=ROOT/'simulation_probe.json'
if p.exists() and p.stat().st_size:
    result=json.loads(p.read_text())
    line('Mô phỏng: LiDAR '+str(result.get('scan',{}).get('count','?'))+' mẫu; odometry và lệnh vận tốc có dữ liệu.')
p=ROOT/'simulation_behaviors.json'
if p.exists() and p.stat().st_size:
    result=json.loads(p.read_text())
    line('Gazebo: 3 hành vi hoàn tất với cử chỉ tổng hợp (không phải tay thật).')
    for b in result.get('behaviors',[]):
        line(b['behavior']+': '+b['result']+'; quãng đường '+format(b['path_length_m'],'.2f')+' m.',9)
line('Chưa có video tay thật đủ 6 cử chỉ hoặc bộ đo độ chính xác nhận diện.')
line('Ảnh nếu có chỉ chứng minh cửa sổ/phần mềm, không thay thế demo đầy đủ.')
title('6. Hướng dẫn tái lập và liên kết nộp')
line('Xem README.md: cài venv, tải model, build, launch mô phỏng và hai node.')
submission=json.loads((ROOT/'submission.json').read_text())
line('GitHub: nhánh '+submission.get('branch', 'assignment-6-hand-gesture'),9)
c.linkURL(submission['public_repository_url'], (42,y+14,550,y+28), relative=0)
line('Commit: '+(submission['tested_public_commit'] or 'xem lịch sử nhánh GitHub.'))
line('Video Drive: '+(submission['video_drive_url'] or 'chưa bổ sung video Bài 6.'))
line('Điền submission.json sau khi quay/upload và push; chạy lại script này.')
line('Liên kết thư mục Drive cũ được lưu riêng trong docs/lab6/links.md.')
title('7. Tài liệu tham khảo')
for text,url in [('MediaPipe Gesture Recognizer — Google AI Edge',
                  'https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer/python'),
                 ('TurtleBot 4 simulator — nhánh Jazzy',
                  'https://github.com/turtlebot/turtlebot4_simulator/tree/jazzy'),
                 ('OpenCV VideoCapture — tài liệu chính thức',
                  'https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html')]:
    line(text,9);c.linkURL(url,(42,y+15,550,y+27),relative=0)
for image in ['gazebo.png','webcam.png']:
    p=ROOT/image
    if p.exists():
        page();title('Ảnh thực nghiệm phần mềm: '+image)
        img=ImageReader(str(p));w,h=img.getSize()
        scale=min(510/w,580/h)
        c.drawImage(img,42,y-h*scale,width=w*scale,height=h*scale)
        y-=h*scale+30
        line('Ảnh chụp khi kiểm tra, chưa chứng minh đủ hành vi bằng tay thật.',9)
c.save()
print(ROOT/'report.pdf')
