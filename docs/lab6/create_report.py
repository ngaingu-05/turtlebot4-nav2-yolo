"""Build the Lab 6 report with the typography and layout of last week's report."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
import shutil
import textwrap
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, Preformatted, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from reportlab.graphics import renderSVG

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
OUT = WORKSPACE / 'docs' / 'reports'
OUT.mkdir(exist_ok=True)
PDF = OUT / 'Bao_cao_TurtleBot4_Cu_chi_tay_Bai6.pdf'
SUB = json.loads((ROOT / 'submission.json').read_text())
MOTION = json.loads((ROOT / 'simulation_behaviors.json').read_text())
WAVE = json.loads((ROOT / 'simulation_wave.json').read_text())['behaviors'][0]
TRANSITION = json.loads((ROOT / 'hand_transition_test.json').read_text())
ROS = json.loads((ROOT / 'ros_integration.json').read_text())
TEAL = colors.HexColor('#006d77')
BLUE = colors.HexColor('#12374b')
GRAY = colors.HexColor('#52616b')
PALE = colors.HexColor('#e5f1f3')
WIDTH = A4[0] - 84
for name, filename in [('DV', 'DejaVuSans.ttf'), ('DV-Bold', 'DejaVuSans-Bold.ttf'), ('Mono', 'DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, '/usr/share/fonts/truetype/dejavu/' + filename))
pdfmetrics.registerFontFamily('DV', normal='DV', bold='DV-Bold', italic='DV', boldItalic='DV-Bold')
styles = getSampleStyleSheet()
for name, opts in [
    ('BodyVN', dict(fontName='DV', fontSize=10, leading=15, spaceAfter=8)),
    ('TitleVN', dict(fontName='DV-Bold', fontSize=22, leading=30, textColor=BLUE, spaceAfter=16)),
    ('HeadingVN', dict(fontName='DV-Bold', fontSize=14, leading=20, textColor=TEAL, spaceAfter=10)),
    ('CaptionVN', dict(fontName='DV', fontSize=8.5, leading=12, textColor=GRAY, spaceAfter=12)),
    ('CellVN', dict(fontName='DV', fontSize=8.8, leading=12.5, spaceAfter=0)),
    ('CodeVN', dict(fontName='Mono', fontSize=7.4, leading=11, spaceAfter=8)),
]:
    styles.add(ParagraphStyle(name=name, **opts))
story = []

def p(text):
    story.append(Paragraph(text, styles['BodyVN']))

def heading(text):
    story.append(Paragraph(text, styles['HeadingVN']))

def page():
    story.append(PageBreak())

def table(rows, widths):
    cells = [[Paragraph(escape(str(cell)).replace('\n', '<br/>'), styles['CellVN']) for cell in row] for row in rows]
    obj = Table(cells, colWidths=widths, repeatRows=1, hAlign='LEFT')
    obj.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PALE),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), .7, TEAL),
        ('LINEBELOW', (0, 1), (-1, -1), .3, colors.HexColor('#dddddd')),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.extend([obj, Spacer(1, 10)])

def figure(filename, caption, width):
    path = ROOT / filename
    with PILImage.open(path) as im:
        w, h = im.size
    story.append(KeepTogether([
        Image(str(path), width=width, height=width * h / w),
        Spacer(1, 5), Paragraph(caption, styles['CaptionVN']),
    ]))

def link(url, label):
    return f'<link href="{escape(url, {chr(34): "&quot;"})}" color="#0077b6"><u>{escape(label)}</u></link>'

def arrow(drawing, x1, y1, x2, y2):
    drawing.add(Line(x1, y1, x2, y2, strokeColor=TEAL, strokeWidth=1.1))
    if x2 > x1:
        pts = [x2, y2, x2 - 5, y2 + 3, x2 - 5, y2 - 3]
    elif x2 < x1:
        pts = [x2, y2, x2 + 5, y2 + 3, x2 + 5, y2 - 3]
    elif y2 > y1:
        pts = [x2, y2, x2 - 3, y2 - 5, x2 + 3, y2 - 5]
    else:
        pts = [x2, y2, x2 - 3, y2 + 5, x2 + 3, y2 + 5]
    drawing.add(Polygon(pts, fillColor=TEAL, strokeColor=TEAL))

def box(d, x, y, w, h, lines):
    d.add(Rect(x, y, w, h, rx=5, ry=5, fillColor=PALE, strokeColor=TEAL, strokeWidth=.8))
    first = y + h / 2 + (len(lines) - 1) * 6
    for i, text in enumerate(lines):
        d.add(String(x + w / 2, first - i * 13 - 3, text, fontName='DV', fontSize=8, textAnchor='middle', fillColor=BLUE))

def architecture():
    d = Drawing(WIDTH, 175)
    x = [0, 123, 264, 405]
    widths = [104, 122, 122, 106]
    box(d, x[0], 85, widths[0], 55, ['Webcam laptop', 'Ảnh RGB'])
    box(d, x[1], 85, widths[1], 55, ['gesture_recognition', 'OpenCV + MediaPipe', '+ nhận diện Wave'])
    box(d, x[2], 85, widths[2], 55, ['robot_behavior', 'Chọn → Xác nhận', 'Điều khiển + an toàn'])
    box(d, x[3], 85, widths[3], 55, ['TurtleBot 4', 'Gazebo Harmonic'])
    for i in range(3):
        arrow(d, x[i] + widths[i], 112, x[i + 1], 112)
    d.add(String(254, 151, '/detected_gesture: String', fontName='DV', fontSize=8, fillColor=GRAY, textAnchor='middle'))
    d.add(String(398, 151, '/cmd_vel', fontName='DV', fontSize=8, fillColor=GRAY, textAnchor='middle'))
    d.add(Line(457, 85, 457, 40, strokeColor=TEAL))
    arrow(d, 457, 40, 325, 40)
    arrow(d, 325, 40, 325, 85)
    d.add(String(400, 23, '/scan + /clock', fontName='DV', fontSize=8, fillColor=GRAY, textAnchor='middle'))
    d.add(Line(285, 85, 285, 62, strokeColor=TEAL))
    arrow(d, 285, 62, 184, 62)
    arrow(d, 184, 62, 184, 85)
    d.add(String(229, 44, '/behavior_status', fontName='DV', fontSize=8, fillColor=GRAY, textAnchor='middle'))
    return d

# Page 1: same title, identity block, link block and large figure as last week.
story.append(Paragraph('BÁO CÁO THỰC HÀNH<br/>TURTLEBOT 4', styles['TitleVN']))
p('<b>Bài tập 6 — Giao tiếp phi ngôn ngữ và điều khiển TurtleBot 4 bằng cử chỉ tay</b>')
p('Ngày thực nghiệm: <b>28/10/2026</b> · Múi giờ Việt Nam (UTC+7).<br/>'
  'Môi trường: Ubuntu 24.04 LTS, ROS 2 Jazzy, Gazebo Harmonic, TurtleBot 4 Standard.')
p('Họ và tên: <b>Nguyễn Minh Nghĩa</b><br/>Mã sinh viên: <b>23020755</b><br/>Lớp / Nhóm: <b>K68 E RE</b>')
p('GitHub: ' + link(SUB['public_repository_url'], 'Nhánh assignment-6-hand-gesture — mã nguồn Bài 6') + '<br/>'
  'Google Drive: ' + link(SUB['previous_assignment_drive_folder_url'], 'Thư mục nộp bài và tài liệu'))
heading('Kết quả thực nghiệm')
p('Đã triển khai hai ROS 2 node, năm cử chỉ tĩnh và một cử chỉ động. '
  '<b>7/7 kiểm thử logic đạt</b>; kiểm thử ROS với dữ liệu tổng hợp đạt bảy tình huống. '
  'Trong Gazebo, ba hành vi tiến–lùi, vòng tròn và chào đều hoàn tất khi cấp cử chỉ tổng hợp.')
figure('gazebo.png', 'Hình 1. Ảnh chụp Gazebo và TurtleBot 4 trong world gesture_arena của Bài 6; môi trường mô phỏng có mặt sàn trống.', 460)
p('Phạm vi minh chứng: ảnh webcam và dữ liệu mô phỏng đã được lưu; video tay thật đầy đủ sáu cử chỉ chưa được cung cấp. '
  'Link Drive trên là thư mục lấy từ báo cáo tuần trước, chưa xác nhận chứa video Bài 6.')

# Page 2: system diagram and ROS interfaces.
page(); heading('1. Kiến trúc hệ thống và giao tiếp ROS 2')
p('Webcam laptop cung cấp ảnh cho node nhận diện. Kết quả phân loại được gửi đến node hành vi; '
  'robot chỉ chuyển động khi đã chọn hành vi và nhận cử chỉ xác nhận. Hệ thống không yêu cầu Nav2, SLAM hoặc bản đồ.')
diagram = architecture()
renderSVG.drawToFile(diagram, str(ROOT / 'architecture.svg'))
story.extend([diagram, Paragraph('Hình 2. Sơ đồ kiến trúc và luồng dữ liệu của hệ thống. Đây là sơ đồ thiết kế, không phải ảnh chụp thực nghiệm.', styles['CaptionVN'])])
table([
    ['Node', 'Chức năng'],
    ['gesture_recognition_node', 'Đọc webcam bằng OpenCV; chạy MediaPipe; nhận diện Wave theo landmark; hiển thị tên cử chỉ, confidence và trạng thái.'],
    ['robot_behavior_node', 'Chọn/xác nhận hành vi; phát vận tốc; dừng/hủy; kiểm tra tín hiệu điều khiển và LiDAR.'],
], [155, WIDTH - 155])
table([
    ['Topic', 'Kiểu message', 'Luồng xử lý'],
    ['/detected_gesture', 'std_msgs/msg/String', 'Nhận diện → node hành vi'],
    ['/cmd_vel', 'geometry_msgs/msg/\nTwistStamped', 'Node hành vi → bộ điều khiển robot (Jazzy)'],
    ['/behavior_status', 'std_msgs/msg/String', 'Node hành vi → cửa sổ webcam'],
    ['/scan', 'sensor_msgs/msg/LaserScan', 'LiDAR mô phỏng → kiểm tra khoảng hở'],
    ['/clock', 'rosgraph_msgs/msg/Clock', 'Gazebo → thời lượng chuyển động'],
], [117, 167, WIDTH - 284])
p('Đề bài sử dụng Ubuntu 22.04 / ROS 2 Humble; phiên thực hiện này dùng Ubuntu 24.04 / ROS 2 Jazzy '
  'đang có trên máy. Topic vận tốc dùng TwistStamped tương thích cấu hình mô phỏng đã kiểm tra.')

# Page 3: recognizer, mapping, state machine and safeguards.
page(); heading('2. Nhận diện cử chỉ và điều khiển hành vi')
p('OpenCV đọc ảnh 640 × 480 và lật gương để thao tác thuận tay. MediaPipe Gesture Recognizer chạy chế độ VIDEO '
  'trên CPU, trả nhãn cử chỉ, độ tin cậy và 21 landmark bàn tay. Ngưỡng phân loại mặc định là <b>0,65</b>.')
p('Năm lớp tĩnh sử dụng trực tiếp gồm Pointing_Up, Victory, Thumb_Up, Open_Palm và Closed_Fist. '
  'Wave được bổ sung bằng quy tắc: cổ tay của bàn tay mở đổi hướng ít nhất hai lần trong cửa sổ 1,5 giây; '
  'mỗi đoạn dịch chuyển tối thiểu 0,10 chiều rộng ảnh. Confidence khi hiện Wave là điểm Open Palm nền.')
table([
    ['Cử chỉ', 'Hành vi / tác dụng'],
    ['Vẫy tay — Wave', 'Chọn chào: xoay trái–phải bốn pha, mỗi pha 1 giây, vận tốc góc ±0,5 rad/s.'],
    ['Một ngón — Pointing Up', 'Chọn tiến–lùi bốn cặp; mỗi lượt 1,5 giây, vận tốc thẳng ±0,12 m/s.'],
    ['Hai ngón — Victory', 'Chọn một vòng tròn: v = 0,12 m/s; ω = 0,3 rad/s; bán kính lý thuyết R = v/ω = 0,4 m.'],
    ['Ngón cái — Thumb Up', 'Xác nhận và thực hiện hành vi đã chọn.'],
    ['Xòe tay — Open Palm', 'Dừng khi nhận được cử chỉ; xóa hành vi và lựa chọn.'],
    ['Nắm tay — Closed Fist', 'Hủy hành vi hiện tại, xóa lựa chọn và về trạng thái chờ.'],
], [157, WIDTH - 157])
heading('Máy trạng thái và cơ chế an toàn')
p('<b>IDLE → SELECTED → RUNNING → DONE.</b> Lệnh chọn/xác nhận phải ổn định ít nhất 0,35 giây. '
  'Mỗi cử chỉ giữ nguyên chỉ kích hoạt một lần. Lựa chọn được giữ tối đa 5 giây để người dùng đổi sang Thumb Up; '
  'robot vẫn đứng yên trong lúc chờ xác nhận.')
p('Khi đang chạy, mất cử chỉ hợp lệ quá 0,8 giây sẽ dừng và hủy hành vi. Timer steady phát vận tốc 20 Hz; '
  'watchdog dùng đồng hồ monotonic, còn thời lượng quỹ đạo dùng ROS clock. Open Palm/Closed Fist được xử lý ngay, '
  'không chờ khoảng giữ 0,35 giây.')
p('LiDAR phải có dữ liệu mới trong 1 giây và không có điểm vật cản gần hơn 0,55 m; dữ liệu lỗi hoặc quá hạn sẽ dừng robot. '
  'Khi bắt đầu vẫy tay, Open Palm có thể dừng robot trước khi Wave được chọn; động tác chào vẫn cần xác nhận.')

# Page 4: a real webcam screenshot and measured results, clearly distinguished.
page(); heading('3. Kết quả kiểm thử và hình ảnh minh họa')
figure('webcam.png', 'Hình 3. Webcam laptop và các landmark bàn tay. Tại thời điểm chụp, confidence 0,57 thấp hơn ngưỡng 0,65 nên nhãn hiển thị None; ảnh này minh họa bộ lọc, không chứng minh nhận đúng đủ sáu cử chỉ.', 340)
paths = {b['behavior']: b['path_length_m'] for b in MOTION['behaviors']}
table([
    ['Hạng mục', 'Kết quả / minh chứng'],
    ['Build và unit test', 'Build PASS; 7/7 pytest PASS; đã đăng ký kiểm thử với colcon.'],
    ['Kiểm thử giao tiếp ROS', ROS['result'] + ': chọn/xác nhận, vận tốc, dừng, hủy, mất tín hiệu, vật cản và scan quá hạn.'],
    ['Tiến–lùi bốn cặp', f"DONE; tổng quãng đường odometry {paths['back_forth']:.2f} m."],
    ['Một vòng tròn', f"DONE; tổng quãng đường odometry {paths['circle']:.2f} m."],
    ['Chào trái–phải', f"DONE; phép kiểm tra riêng ghi biên độ yaw {WAVE['yaw_span_rad']:.3f} rad."],
    ['Đổi tay trước xác nhận', f"PASS: chọn → mất nhận diện {TRANSITION['gap_seconds']:.1f} giây → xác nhận; robot dịch chuyển {TRANSITION['displacement_m']:.3f} m rồi hủy về IDLE."],
], [156, WIDTH - 156])
p('Các phép đo chuyển động trên sử dụng <b>cử chỉ tổng hợp qua topic</b> để kiểm tra node điều khiển, '
  'khác với đánh giá độ chính xác của AI trên tay thật. Chuyển động vòng hở có sai số; chưa có thống kê accuracy '
  'hoặc video tay thật bao phủ cả sáu cử chỉ.')

# Page 5: reproducibility, links and concrete limitations.
page(); heading('4. Tổng hợp, cách tái hiện và liên kết nộp')
p('Mã nguồn nằm trong package <b>tb4_gesture_control</b>, gồm hai executable, các launch file, world trống và bộ kiểm thử. '
  'README của workspace trình bày cài dependency, tạo venv kế thừa thư viện ROS, tải model MediaPipe, build và chạy.')
code = '''# Moi terminal ROS deu source workspace
cd ~/turtlebot4
source /opt/ros/jazzy/setup.bash
source install/setup.bash
# Build va kiem thu package
colcon build --symlink-install --packages-select tb4_gesture_control
colcon test --packages-select tb4_gesture_control
colcon test-result --verbose
# Terminal 1: mo phong
ros2 launch tb4_gesture_control simulation.launch.py
# Chuan bi truoc demo: roi dock, doi action hoan tat
ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'
# Terminal 2: nhan dien va dieu khien
ros2 launch tb4_gesture_control gesture.launch.py'''
story.append(Preformatted('\n'.join(textwrap.fill(line, width=94, subsequent_indent='  ') for line in code.splitlines()), styles['CodeVN']))
p('Có thể dùng <b>demo.launch.py</b> để mở mô phỏng và các node trong một phiên launch. '
  'Cần bảo đảm không còn phiên Gazebo/controller cũ, robot đã rời dock và action chuẩn bị đã kết thúc trước khi test. '
  'Trong demo, chỉ dùng cử chỉ để chọn, xác nhận, dừng và hủy hành vi.')
heading('Liên kết mã nguồn và minh chứng')
p('GitHub public: ' + link(SUB['public_repository_url'], 'assignment-6-hand-gesture') + '<br/>'
  'Commit mã nguồn đã kiểm thử: <b>' + escape(SUB['tested_public_commit'][:7]) + '</b>.<br/>'
  'Google Drive: ' + link(SUB['previous_assignment_drive_folder_url'], 'Thư mục nộp bài và tài liệu') + '.')
p('Thư mục Drive được kế thừa từ báo cáo tuần trước. URL video Bài 6 chưa được cung cấp riêng; '
  'cần upload video đầy đủ webcam/Gazebo và kiểm tra quyền xem trước khi nộp. Dữ liệu JSON, ảnh và script tạo PDF '
  'được lưu trong <b>docs/lab6/</b> để đối chiếu kết quả.')
heading('Nhận xét và kết luận')
p('Hệ thống đã kiểm tra được luồng webcam → nhận diện → topic cử chỉ → máy trạng thái → vận tốc robot. '
  'Cơ chế xác nhận, giữ lựa chọn 5 giây, chống kích hoạt lặp và watchdog đã được kiểm thử; '
  'ba hành vi chuyển động hoàn tất trong môi trường mô phỏng với đầu vào tổng hợp.')
p('Giới hạn: nhận diện phụ thuộc ánh sáng và việc bàn tay nằm trọn trong ảnh; không suy ra accuracy từ một ảnh webcam. '
  'LiDAR là hàng rào dừng bảo thủ, chưa phải bảo đảm không va chạm trong mọi tình huống. '
  'Nếu tiến trình điều khiển bị dừng đột ngột, robot còn cần timeout vận tốc ở controller phía dưới.')
p('Tài liệu tham khảo: ' + link('https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer/python', 'MediaPipe Gesture Recognizer') + '; '
  + link('https://github.com/turtlebot/turtlebot4_simulator/tree/jazzy', 'TurtleBot 4 Simulator — Jazzy') + '; '
  + link('https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html', 'OpenCV VideoCapture') + '.')

def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#cccccc'))
    canvas.line(42, 36, A4[0] - 42, 36)
    canvas.setFont('DV', 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(42, 23, 'TurtleBot 4 · Bài 6 · Thực nghiệm 28/10/2026')
    canvas.drawRightString(A4[0] - 42, 23, f'Trang {doc.page}')

SimpleDocTemplate(str(PDF), pagesize=A4, rightMargin=42, leftMargin=42,
                  topMargin=38, bottomMargin=48,
                  title='Báo cáo thực hành TurtleBot 4 — Bài 6: Cử chỉ tay',
                  author='Nguyễn Minh Nghĩa — 23020755').build(story, onFirstPage=footer, onLaterPages=footer)
shutil.copyfile(PDF, ROOT / 'report.pdf')
print(PDF)
