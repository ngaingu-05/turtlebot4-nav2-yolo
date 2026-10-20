from pathlib import Path
import time,subprocess
r=Path(__file__).resolve().parent;seen=set();end=time.monotonic()+400
while time.monotonic()<end:
 s=(r/'combined_launch.log').read_text() if (r/'combined_launch.log').exists() else ''
 for i in (1,2,3):
  if f'Goal {i} succeeded' in s and i not in seen:
   subprocess.run(['python3',str(r/'capture_window.py'),'RViz',str(r/f'goal_{i}_rviz.png')]);seen.add(i)
 if len(seen)==3:break
 time.sleep(.3)
print('captured goals',sorted(seen),flush=True)
