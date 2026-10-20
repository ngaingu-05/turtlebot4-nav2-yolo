from pathlib import Path
import os,time
os.environ.setdefault("SOURCE_DATE_EPOCH", str(int(time.time())))
import json,re,math,hashlib,yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak,KeepTogether,Preformatted
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from xml.sax.saxutils import escape
r=Path(__file__).resolve().parent;ws=r.parents[2];out=ws/'docs/reports';out.mkdir(exist_ok=True)
log=(r/'combined_launch.log').read_text();interfaces=json.loads((r/'interfaces.json').read_text());loc=json.loads((r/'localization.json').read_text());collision=json.loads((r/'collision_summary.json').read_text());monitor=json.loads((r/'message_monitor.json').read_text())
goals=yaml.safe_load((ws/'src/tb4_simulation_lab/config/navigation_goals.yaml').read_text())['goals']
success=[];send=[]
for line in log.splitlines():
 m=re.search(r'\[([0-9]+\.[0-9]+)\].*\[NAV\] Goal (\d+) succeeded',line)
 if m:success.append({'goal':int(m[2]),'wall_timestamp':float(m[1])})
 m=re.search(r'\[([0-9]+\.[0-9]+)\].*Navigating to Goal (\d+)',line)
 if m:send.append({'goal':int(m[2]),'wall_timestamp':float(m[1])})
chairs=[float(x) for x in re.findall(r'chair ([0-9.]+)',log)]
summary={'date':'2026-10-20','success':success,'elapsed_wall_s':success[-1]['wall_timestamp']-send[0]['wall_timestamp'] if success else None,'initial_amcl_error_m':loc['initial_position_error_m'],'chair_logged_observations':len(chairs),'max_chair_confidence':max(chairs) if chairs else None,'collision':collision,'interfaces':interfaces,'map_checksums':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ws/'src/tb4_simulation_lab/maps').glob('map.*')}}
(r/'summary.json').write_text(json.dumps(summary,indent=2))
# Figure built from the saved map, not a simulation screenshot.
mp=ws/'src/tb4_simulation_lab/maps';meta=yaml.safe_load((mp/'map.yaml').read_text());im=np.array(PILImage.open(mp/'map.pgm'));ox,oy,_=meta['origin'];res=meta['resolution'];h,w=im.shape
fig,ax=plt.subplots(figsize=(8.6,4.7));ax.imshow(im,cmap='gray',vmin=0,vmax=255,extent=[ox,ox+w*res,oy,oy+h*res]);ax.set_xlim(-5,2);ax.set_ylim(-2.5,3.5)
for i,g in enumerate(goals,1):
 ax.scatter(g['x'],g['y'],s=80,color=['#0077b6','#e76f51','#6a4c93'][i-1],zorder=5);ax.annotate(f"Goal {i}",(g['x'],g['y']),xytext=(8,8),textcoords='offset points',weight='bold');ax.arrow(g['x'],g['y'],.4*math.cos(g['yaw']),.4*math.sin(g['yaw']),width=.025,color='#006d77')
ax.set_xlabel('x (m), map');ax.set_ylabel('y (m), map');ax.set_aspect('equal');ax.grid(alpha=.2);fig.tight_layout();fig.savefig(r/'map_goals.png',dpi=160);plt.close(fig)
for name,f in [('DV','DejaVuSans.ttf'),('DV-Bold','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+f))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold')
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyVN',fontName='DV',fontSize=10,leading=15,spaceAfter=8));styles.add(ParagraphStyle(name='TitleVN',fontName='DV-Bold',fontSize=22,leading=30,textColor=colors.HexColor('#12374b'),spaceAfter=16));styles.add(ParagraphStyle(name='HeadingVN',fontName='DV-Bold',fontSize=14,leading=20,textColor=colors.HexColor('#006d77'),spaceAfter=10));styles.add(ParagraphStyle(name='CaptionVN',fontName='DV',fontSize=8.5,leading=12,textColor=colors.HexColor('#52616b'),spaceAfter=12));styles.add(ParagraphStyle(name='CodeVN',fontName='Mono',fontSize=7,leading=10,spaceAfter=8))
story=[]
def p(s):story.append(Paragraph(s,styles['BodyVN']))
def heading(s):story.append(Paragraph(s,styles['HeadingVN']))
def figure(name,caption,width=470):
 path=r/name
 if not path.exists():p('Chưa có ảnh: '+name);return
 w,h=PILImage.open(path).size;story.append(Image(str(path),width=width,height=width*h/w));story.append(Spacer(1,5));story.append(Paragraph(caption,styles['CaptionVN']))
def table(rows,widths=None):
 cells=[[Paragraph(escape(str(c)),styles['BodyVN']) for c in row] for row in rows];t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5f1f3')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#006d77')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#dddddd')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5)]));story.append(t);story.append(Spacer(1,12))
def page():story.append(PageBreak())
all_ok=[x['goal'] for x in success]==[1,2,3] and 'All navigation goals completed successfully' in log
story.append(Paragraph('BÁO CÁO THỰC HÀNH<br/>TURTLEBOT 4',styles['TitleVN']))
p('<b>Định vị trên bản đồ có sẵn, điều hướng tự động bằng Nav2 và nhận diện vật thể bằng YOLO</b>')
p('Ngày thực nghiệm: <b>20/10/2026</b> · Múi giờ Việt Nam (UTC+7).<br/>Môi trường: Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic, TurtleBot 4 Standard, world Depot.')
p('Họ và tên: <b>Nguyễn Minh Nghĩa</b><br/>Mã sinh viên: <b>23020755</b><br/>Lớp / Nhóm: <b>K68 E RE</b>')
p('GitHub: <link href="https://github.com/ngaingu-05/turtlebot4-nav2-yolo" color="#0077b6"><u>github.com/ngaingu-05/turtlebot4-nav2-yolo</u></link><br/>Google Drive: <link href="https://drive.google.com/drive/u/1/folders/1KpX5KTfOAgTgpQlJO7Gp-5q5eNcDs8VM" color="#0077b6"><u>Thư mục nộp bài và tài liệu</u></link>')

heading('Kết quả thực nghiệm')
p(f"Chuỗi navigation: <b>{'ĐẠT — 3/3 goal thành công đúng thứ tự' if all_ok else 'CHƯA ĐẠT'}</b>. Thời gian từ gửi Goal 1 đến kết quả Goal 3: <b>{summary['elapsed_wall_s']:.2f} giây thực</b>.")
p(f"AMCL: sai lệch vị trí ban đầu so với ground truth Gazebo <b>{loc['initial_position_error_m']*1000:.2f} mm</b>. YOLO: {len(chairs)} lần ghi log có nhãn chair; độ tin cậy cao nhất <b>{max(chairs) if chairs else 0:.2f}</b>.")
figure('gazebo.png','Hình 1. Ảnh chụp trực tiếp Gazebo Depot và TurtleBot 4 trong phiên chạy ngày 20/10/2026, trước khi thêm ghế thử.',460)
p('Toàn bộ ảnh và số liệu trong báo cáo được thu từ phiên chạy mới. Ground truth chỉ dùng để đặt và kiểm tra initial pose trong mô phỏng; node navigation vận hành bằng AMCL và Nav2.')
page();heading('1. Khởi chạy mô phỏng và định vị')
p('Nạp lại map.yaml và map.pgm của workspace, không chạy SLAM đồng thời. Khởi động Gazebo, robot và bridge; tắt E-stop trong mô phỏng, gọi action /undock và đợi kết quả SUCCEEDED. Sau đó đặt initial pose theo vị trí/hướng thật của robot trong Gazebo bằng script phục vụ kiểm thử.')
p('RViz dùng Fixed Frame = map. AMCL cung cấp biến đổi map → odom, kết hợp odom → base_link để Nav2 định vị robot. Kiểm tra nhận dữ liệu map, scan, odom, tf, tf_static, amcl_pose và cmd_vel; cả sáu lifecycle node đều active.')
table([['Thông số','Giá trị'],['Bản đồ','604 × 304 ô; độ phân giải 0,05 m/ô'],['AMCL ban đầu (x, y)',f"({loc['amcl']['x']:.5f}, {loc['amcl']['y']:.5f}) m"],['Ground truth (x, y)',f"({loc['truth']['x']:.5f}, {loc['truth']['y']:.5f}) m"],['Sai lệch vị trí ban đầu',f"{loc['initial_position_error_m']:.6f} m"],['Lifecycle','amcl, map_server, planner_server, controller_server, bt_navigator, collision_monitor: active']],[150,320])
figure('localization_rviz.png','Hình 2. RViz sau khởi tạo AMCL: Fixed Frame map, trạng thái OK, hiển thị bản đồ, costmap, robot và dữ liệu LiDAR.',470)
p('Lưu ý: sai lệch trên là phép kiểm tra tại thời điểm ban đầu, không phải kết luận về độ chính xác ở mọi vị trí. Ground truth không thay thế AMCL trong điều khiển.')
page();heading('2. Tọa độ mục tiêu và chương trình điều hướng')
p('Sử dụng ba tọa độ đã được ghi nhận trong navigation_goals.yaml. Hai điểm đầu thuộc vùng trống trên map Depot; điểm thứ ba quay về khu vực xuất phát sau undock. Tọa độ thuộc frame map, đơn vị mét và radian. Cách chọn trước đó dựa trên ô trống, khoảng hở và đường planner; phiên này giữ nguyên tọa độ để kiểm tra lặp lại.')
table([['Mục tiêu','x (m)','y (m)','yaw (rad)']]+[[f'Goal {i}',f"{g['x']:.6f}",f"{g['y']:.6f}",f"{g['yaw']:.6f}"] for i,g in enumerate(goals,1)],[90,125,125,130])
figure('map_goals.png','Hình 3. Vị trí và hướng của ba goal trên bản đồ lưu. Đây là hình minh họa từ PGM và YAML, không phải ảnh chụp RViz hay đường robot đã đi.',450)
p('Node navigation_node.py kế thừa BasicNavigator. Chương trình đợi Nav2 active, AMCL có pose, đồng hồ mô phỏng hoạt động và robot đã rời dock; sau đó tạo PoseStamped trong map và gọi NavigateToPose cho từng goal. Quaternion hướng được tính bằng z = sin(yaw/2), w = cos(yaw/2).')
p('Chỉ gửi goal tiếp theo khi TaskResult.SUCCEEDED. Nếu bị từ chối, thất bại hoặc hết thời gian, chương trình dừng chuỗi và yêu cầu hủy action. Trong chuỗi thử nghiệm không sử dụng teleop và không đặt goal bằng chuột trên RViz.')
page();heading('3. Kết quả ba goal tự động')
rows=[['Goal','Kết quả action','Thời gian chặng (giây thực)']]
for i in (1,2,3):
 a=next((v for v in send if v['goal']==i),None);b=next((v for v in success if v['goal']==i),None);rows.append([f'Goal {i}','SUCCEEDED' if b else 'Chưa thành công',f"{b['wall_timestamp']-a['wall_timestamp']:.2f}" if a and b else '—'])
table(rows,[90,150,230])
for i in (1,2):figure(f'goal_{i}_rviz.png',f'Hình {3+i}. RViz được chụp sau khi log báo Goal {i} succeeded; node tự động chuyển sang goal kế tiếp nên ảnh có thể đã hiển thị đường đi chặng tiếp theo.',400)
page();heading('4. Hoàn tất hành trình và kiểm tra va chạm')
figure('goal_3_rviz.png','Hình 6. RViz sau khi Goal 3 thành công, kết thúc chuỗi điều hướng tự động.',470)
p(f"Trong cửa sổ giám sát {collision['duration_s']:.2f} giây thực, nhận {collision['hazard_messages']} message hazard_detection và {collision['bumper_messages']} message bumper_contact. Số lần quan sát hazard BUMP: <b>{collision['bump_events']}</b>; số message contact không rỗng: <b>{collision['nonempty_contacts']}</b>.")
p('Luồng hazard_detection có dữ liệu thực và không ghi nhận BUMP trong cửa sổ thử nghiệm. Kênh bumper_contact không nhận message; số 0 ở kênh này không được coi là xác nhận luồng contact hoạt động. Giới hạn: hazard bumper không chứng minh mọi tiếp xúc hình học ở mọi bộ phận robot; không đánh đồng action thành công với bằng chứng tuyệt đối không va chạm.')
navlines=[line[line.index('[NAV]'):] for line in log.splitlines() if '[NAV]' in line and ('Goal' in line or 'All navigation' in line)]
story.append(Preformatted('\n'.join(navlines),styles['CodeVN']))
p('Minh chứng gốc: combined_launch.log, collision_summary.json, interfaces.json và các ảnh goal_1_rviz.png đến goal_3_rviz.png trong thư mục evidence của phiên này.')
page();heading('5. Nhận diện vật thể từ camera bằng YOLO')
p('Node yolo_detection_node.py subscribe /oakd/rgb/preview/image_raw bằng sensor-data QoS. CvBridge chuyển sensor_msgs/Image sang ảnh OpenCV bgr8. YOLOv8n chạy trên CPU (ngưỡng confidence 0,4; imgsz 320; mục tiêu 2 Hz); inference ở worker riêng để không chặn callback ảnh hay node navigation.')
p('Kết quả được vẽ bounding box, tên class, confidence bằng result.plot và publish lên /yolo/detections/image. Terminal ghi class/confidence theo chu kỳ. RGB và annotated đều 320 × 240; ảnh đầu vào rgb8, ảnh đầu ra bgr8.')
p('Thêm model Chair static từ cache Fuel vào Gazebo trước khi chạy chuỗi goal, tại x = −0,52 m, y = −1,03 m, yaw = 1,39 rad. Đây là vật thể 3D trong môi trường mô phỏng; không dùng ảnh ghi sẵn làm đầu vào. Fixture được kế thừa từ lần thử trước, chỉ tồn tại trong phiên Gazebo, chưa cố định vào world.')
figure('yolo_chair.jpg','Hình 7. Ảnh camera trực tiếp được node YOLO chú thích trong phiên thử mới. Tên class và confidence nằm trên bounding box.',410)
p(f"Trong log của phiên tích hợp có <b>{len(chairs)}</b> lần ghi nhận nhãn chair, confidence cao nhất <b>{max(chairs) if chairs else 0:.2f}</b>. YOLO chạy đồng thời với navigation; một số góc nhìn có 0 detections là bình thường.")
others=sorted(set(re.findall(r'\[YOLO\] ([a-z]+) [0-9]',log))-{'chair'})
p('Giới hạn nhận diện: mô hình pretrained COCO có khác biệt miền ảnh với Gazebo; không bảo đảm nhận đúng mọi vật thể. '+('Log còn có nhãn '+', '.join(others)+'; các nhãn này không được coi là xác nhận vật thể thật, có thể là false positive.' if others else 'Trong log theo chu kỳ chưa quan sát nhãn khác ngoài chair; đây không phải thống kê mọi frame.'))
page();heading('6. Tổng hợp và cách tái hiện')
table([['Hạng mục','Kết quả / minh chứng'],['Build workspace','PASS — build.log'],['Unit tests','2/2 PASS — unit_tests.log'],['Map + AMCL + TF','PASS — localization.json, interfaces.json'],['Navigation tuần tự','3/3 SUCCEEDED — combined_launch.log'],['Camera + cv_bridge + YOLO','Ảnh đầu vào/đầu ra có message, có nhận diện chair'],['Va chạm bumper',f"BUMP={collision['bump_events']}; contact không rỗng={collision['nonempty_contacts']}"],['Bảo toàn map','SHA-256 được lưu trong summary.json; đối chiếu bản test trước']],[155,315])
p('Ba terminal đều source /opt/ros/jazzy/setup.bash và install/setup.bash trong workspace. Thực hiện undock và đặt initial pose trước khi bắt đầu nhiệm vụ. Thêm lại fixture ghế nếu muốn tái hiện nhận diện dương tính.')
code='''# Terminal 1
ros2 launch tb4_simulation_lab gazebo_rviz.launch.py joy:=false
# Terminal 2
ros2 launch tb4_simulation_lab localization_navigation.launch.py
# Chuẩn bị: /undock; đặt initial pose trong RViz
# Terminal 3
source .venv-yolo/bin/activate
ros2 launch tb4_simulation_lab autonomous_yolo.launch.py \\
  goals_file:=/home/nghia/turtlebot4/src/tb4_simulation_lab/config/navigation_goals.yaml \\
  yolo_model:=/home/nghia/turtlebot4/models/yolov8n.pt show_window:=false'''
# Wrap long command lines for A4.
import textwrap
story.append(Preformatted('\n'.join(textwrap.fill(x,width=88,subsequent_indent='    ') for x in code.splitlines()),styles['CodeVN']))
p('Lưu ý khi dừng: sau khi navigation hoàn tất, thao tác Ctrl+C kết thúc detector gây KeyboardInterrupt trong bước destroy_publisher (exit −2). Inference và navigation đã hoàn thành trước đó; đây là hạn chế cleanup khi tắt launch, chưa được sửa trong phiên đánh giá này. Log gốc được giữ nguyên.')
p('Mã nguồn: src/tb4_simulation_lab/scripts/navigation_node.py và yolo_detection_node.py. Cấu hình: config/navigation_goals.yaml, config/nav2_params.yaml. Launch kết hợp: launch/autonomous_yolo.launch.py.')
p('Minh chứng phiên mới: docs/evidence/integration_2026-10-20/. Script tạo PDF và dữ liệu JSON nằm cùng thư mục để kiểm tra lại số liệu. Ảnh được chụp từ cửa sổ thật hoặc nhận từ topic camera; hình bản đồ mục tiêu được ghi rõ là hình minh họa.')
p('Kết luận: phiên chạy kiểm tra được việc sử dụng bản đồ có sẵn để định vị, tự động hoàn thành ba goal bằng ROS 2 Node và nhận diện ghế từ camera trong lúc hệ thống vận hành. Nguồn gốc bản đồ của bài tuần trước cần được người thực hiện xác nhận trước khi nộp.')
def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#cccccc'));c.line(42,36,A4[0]-42,36);c.setFont('DV',8);c.setFillColor(colors.HexColor('#52616b'));c.drawString(42,23,'TurtleBot 4 · Thực nghiệm 20/10/2026');c.drawRightString(A4[0]-42,23,f'Trang {doc.page}')
pdf=out/'Bao_cao_TurtleBot4_Nav2_YOLO_2026-10-20.pdf'
SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=38,bottomMargin=48,title='Báo cáo TurtleBot 4 — Nav2 và YOLO',author='Báo cáo thực nghiệm workspace TurtleBot 4').build(story,onFirstPage=footer,onLaterPages=footer)
print(pdf)
