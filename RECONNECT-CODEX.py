"""Desktop action: reconnect after signing into a different ChatGPT account.

Pause new lessons, let current work finish, restart only this installation,
check Codex, and restore the original schedule. Never change login credentials.
"""
import argparse
import json
import os
import queue
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

import requests
from coach.store import Store

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
FLAGS=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0


def process_alive(pid):
    if os.name!='nt' or not isinstance(pid,int):return False
    import ctypes
    kernel=ctypes.windll.kernel32
    kernel.OpenProcess.restype=ctypes.c_void_p
    handle=kernel.OpenProcess(0x1000,False,pid)
    if not handle:return False
    code=ctypes.c_ulong()
    kernel.GetExitCodeProcess.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)]
    kernel.CloseHandle.argtypes=[ctypes.c_void_p]
    try:return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
    finally:kernel.CloseHandle(handle)


def start_app():
    subprocess.Popen([str(ROOT/'.venv/Scripts/pythonw.exe'),str(ROOT/'app.py'),'--hidden'],cwd=ROOT,creationflags=FLAGS)


def reconnect(status=lambda text:None):
    store=Store(DATA,recover=False)
    active=bool(store.get('active'))
    original_due=store.get('next_due')
    store.set(active=False,reconnect_until=time.time()+1860)
    restored=False
    proof={'started':time.time(),'schedule_was_active':active,'original_due':original_due}
    try:
        initial={}
        try:initial=json.loads((DATA/'session.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):pass
        if not process_alive(initial.get('pid')):
            # Startup recovers interrupted jobs; the reconnect hold keeps them queued.
            status('Đang mở Hourly Coach chạy nền…')
            start_app()
            deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                try:
                    fresh=json.loads((DATA/'session.json').read_text(encoding='utf-8'))
                    if fresh.get('pid')!=initial.get('pid') and process_alive(fresh.get('pid')):break
                except (OSError,ValueError):pass
                time.sleep(.5)
            else:raise RuntimeError('Không mở được Hourly Coach. Xem data/app.log.')
            store.execute("UPDATE codex_requests SET status='failed',completed=?,http_status=502,error='Hourly Coach đã dừng trước khi lưu phản hồi. Bài đã giữ để thử lại.' WHERE status='running'",(time.time(),))
        status('Đang đợi lượt AI hiện tại hoàn tất; không ngắt bài đang làm…')
        deadline=time.monotonic()+1800
        while time.monotonic()<deadline:
            if not store.one("SELECT id FROM jobs WHERE status='running' LIMIT 1") and not store.one("SELECT id FROM codex_requests WHERE status='running' LIMIT 1"):
                break
            time.sleep(1)
        else:
            raise RuntimeError('AI vẫn đang xử lý. Chưa ngắt tiến trình; hãy thử lại sau khi chấm/tạo đề xong.')
        info={}
        try:info=json.loads((DATA/'session.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):pass
        if isinstance(info.get('pid'),int):
            status('Đang khởi động lại kết nối với tài khoản đã đăng nhập…')
            result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'RECONNECT-CODEX.ps1'),'-AppPid',str(info['pid'])],capture_output=True,text=True,creationflags=FLAGS,timeout=30)
            if result.returncode:
                raise RuntimeError('Không xác nhận được tiến trình Hourly Coach để khởi động lại. Không đụng tới Codex hay ứng dụng khác.')
        # The mutex is released only after the owned app has exited.
        time.sleep(1)
        start_app()
        client=requests.Session();client.headers['X-Coach-Request']='1'
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            try:
                info=json.loads((DATA/'session.json').read_text(encoding='utf-8'))
                client.cookies.set('coach_session',info['token'])
                state=client.get('http://127.0.0.1:8766/api/state',timeout=3)
                if state.ok:break
            except (OSError,ValueError,requests.RequestException):pass
            time.sleep(1)
        else:raise RuntimeError('Hourly Coach chưa khởi động được. Xem data/app.log.')
        status('Đang kiểm tra API Codex của phiên đăng nhập hiện tại…')
        health=client.get('http://127.0.0.1:8766/api/health',timeout=75).json()
        if not health.get('online'):
            raise RuntimeError(health.get('error') or 'Chưa kết nối được Codex. Hãy đăng nhập ChatGPT trong Codex rồi bấm shortcut lại.')
        store.set(active=active,reconnect_until=0)
        restored=True
        # Retry saved failed jobs, never resubmit work already successfully graded.
        retry=client.post('http://127.0.0.1:8766/api/retry',json={},timeout=15)
        proof.update(success=True,finished=time.time(),model=health.get('model'),reasoning_effort=health.get('reasoning_effort'),schedule_restored=active,retry_requested=retry.ok)
        store.event('reconnect','Đã nối lại Codex với phiên đăng nhập hiện tại; giữ đề, bài nộp và lịch.')
        return proof,info['token']
    except Exception as error:
        proof.update(success=False,finished=time.time(),error=str(error))
        raise
    finally:
        if not restored:store.set(active=active,reconnect_until=0)
        (DATA/'reconnect-last.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
        store.db.close()


def main():
    handle=None
    if os.name=='nt':
        import ctypes
        kernel=ctypes.windll.kernel32
        kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
        kernel.CreateMutexW.restype=ctypes.c_void_p
        handle=kernel.CreateMutexW(None,False,'Local\\HourlyCoachReconnect8766')
        if kernel.GetLastError()==183:
            ctypes.windll.user32.MessageBoxW(None,'Đang kết nối lại Codex. Hãy đợi cửa sổ đang chạy.','Hourly Coach',0x40)
            return
        import atexit
        kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        atexit.register(kernel.CloseHandle,handle)
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.check:
        proof,_=reconnect();print(json.dumps(proof,ensure_ascii=True));return
    import tkinter as tk
    from tkinter import ttk
    window=tk.Tk();window.title('Hourly Coach · Kết nối lại Codex');window.geometry('550x230');window.resizable(False,False)
    message=tk.StringVar(value='Sau khi đăng nhập nick mới trong Codex, shortcut này nối lại API.\nĐề và bài làm được giữ nguyên trên ổ E.')
    ttk.Label(window,textvariable=message,wraplength=490,justify='left',padding=24).pack(fill='x')
    progress=ttk.Progressbar(window,mode='indeterminate');progress.pack(fill='x',padx=24);progress.start()
    buttons=ttk.Frame(window);buttons.pack(pady=18)
    events=queue.Queue();result={}
    def work():
        try:events.put(('done',reconnect(lambda s:events.put(('status',s)))))
        except Exception as error:events.put(('error',str(error)))
    def tick():
        try:
            while True:
                kind,value=events.get_nowait()
                if kind=='status':message.set(value)
                else:
                    progress.stop();progress.pack_forget()
                    if kind=='done':
                        proof,token=value;result['token']=token
                        message.set('Đã kết nối Codex · '+str(proof['model'])+' · '+str(proof['reasoning_effort'])+'\nĐề, bài làm và lịch đã được giữ nguyên.')
                        ttk.Button(buttons,text='Mở Hourly Coach',command=lambda:webbrowser.open('http://127.0.0.1:8766/?session='+result['token'])).pack(side='left',padx=5)
                    else:message.set(value)
                    ttk.Button(buttons,text='Đóng',command=window.destroy).pack(side='left',padx=5)
                    window.protocol('WM_DELETE_WINDOW',window.destroy)
        except queue.Empty:pass
        window.after(200,tick)
    window.protocol('WM_DELETE_WINDOW',lambda:message.set('Đang nối lại. Vui lòng đợi để giữ nguyên bài đang xử lý.'))
    threading.Thread(target=work,daemon=True).start();tick();window.mainloop()


if __name__=='__main__':main()
