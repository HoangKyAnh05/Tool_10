import argparse
import atexit
import json
import logging
import os
import secrets
import sys
import threading
import webbrowser
from pathlib import Path

from coach.store import Store
from coach.engine import Engine
from coach.server import create_server

ROOT=Path(__file__).resolve().parent
PORT=8766


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--hidden',action='store_true'); parser.add_argument('--headless',action='store_true')
    args=parser.parse_args(); data=ROOT/'data'; data.mkdir(exist_ok=True)
    # Check the singleton before opening SQLite; a second launch must not recover live jobs.
    if os.name=='nt':
        import ctypes
        kernel=ctypes.windll.kernel32
        kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
        kernel.CreateMutexW.restype=ctypes.c_void_p
        handle=kernel.CreateMutexW(None,False,'Local\\HourlyCoach8766')
        exists=kernel.GetLastError()==183
        kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        atexit.register(kernel.CloseHandle,handle)
        if exists:
            try:
                info=json.loads((data/'session.json').read_text(encoding='utf-8'))
                if not args.hidden: webbrowser.open(f"http://127.0.0.1:{PORT}/?session={info['token']}")
            except Exception: pass
            return
    logging.basicConfig(filename=data/'app.log',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    store=Store(data); engine=Engine(store)
    previous_token=None
    try:
        saved=json.loads((data/'session.json').read_text(encoding='utf-8'))
        if isinstance(saved.get('token'),str) and len(saved['token'])>=40: previous_token=saved['token']
    except Exception: pass
    try: server,token=create_server(engine,ROOT/'web',PORT,token=previous_token)
    except OSError:
        try:
            info=json.loads((data/'session.json').read_text(encoding='utf-8'))
            if not args.hidden: webbrowser.open(f"http://127.0.0.1:{PORT}/?session={info['token']}")
        except Exception: logging.error('Port 8766 unavailable; another application may be using it.')
        return
    (data/'session.json').write_text(json.dumps({'pid':os.getpid(),'token':token}),encoding='utf-8')
    url=f'http://127.0.0.1:{PORT}/?session={token}'
    threading.Thread(target=server.serve_forever,daemon=True).start(); engine.start()
    if not args.hidden and not args.headless: webbrowser.open(url)
    def close(icon=None,item=None):
        engine.stop.set(); engine.wake.set()
        if icon: icon.stop()
        server.shutdown()
        engine.gateway.codex.close()
    if args.headless:
        try: engine.stop.wait()
        except KeyboardInterrupt: close()
        return
    import pystray
    from PIL import Image
    def open_dashboard(icon=None,item=None): webbrowser.open(url)
    def toggle(icon,item):
        if store.get('active'): store.set(active=False); store.event('schedule','Tạm dừng từ khay hệ thống.')
        else:
            try: engine.activate()
            except ValueError: open_dashboard()
    icon=pystray.Icon('HourlyCoach',Image.open(ROOT/'assets'/'coach.png'),'Hourly Coach · Antigravity',
        menu=pystray.Menu(pystray.MenuItem('Mở Hourly Coach',open_dashboard,default=True),
            pystray.MenuItem(lambda item:'Tạm dừng gửi đề' if store.get('active') else 'Bật lịch gửi đề',toggle),
            pystray.Menu.SEPARATOR,pystray.MenuItem('Thoát ứng dụng',close)))
    try: icon.run()
    finally: close()


if __name__=='__main__':
    try: main()
    except Exception:
        logging.exception('Unhandled application error')
        if os.name=='nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,'Hourly Coach chưa khởi động được. Xem data\\app.log hoặc chạy START.bat để xem lỗi.','Hourly Coach',0x10)
        raise
