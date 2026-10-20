import sys,time
from Xlib import display,X,protocol
from PIL import Image
D=display.Display();root=D.screen().root;needle=sys.argv[1].lower();found=[]
def visit(w):
 try:
  name=w.get_wm_name() or ''
  if needle in name.lower():found.append(w)
  for c in w.query_tree().children:visit(c)
 except Exception:pass
visit(root)
if not found:raise RuntimeError('Window not found: '+needle)
w=found[-1]
msg=protocol.event.ClientMessage(window=w,client_type=D.intern_atom('_NET_ACTIVE_WINDOW'),data=(32,[2,X.CurrentTime,0,0,0]));root.send_event(msg,event_mask=X.SubstructureRedirectMask|X.SubstructureNotifyMask);w.configure(stack_mode=X.Above);D.sync();time.sleep(2)
g=w.get_geometry();p=w.translate_coords(root,0,0);raw=w.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff)
Image.frombytes('RGB',(g.width,g.height),raw.data,'raw','BGRX').save(sys.argv[2]);print(w.get_wm_name(),g.width,g.height)
