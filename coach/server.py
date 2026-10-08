import base64
import hmac
import json
import mimetypes
import secrets
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from .store import day_of
from .samples import samples
from .curriculum import SCHEDULE,public_assignment
from .gateway import Gateway
from .media import ALLOWED,VIDEO,MAX_FILE,MAX_VIDEO
from .batches import batch_state,save_draft,submit_batch,FINAL
from .charts import render_chart
from .codex_chat import ChatError


def create_server(engine,web,port=8766,token=None):
    token=token or secrets.token_urlsafe(32)
    store=engine.store; web=Path(web).resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass

        def authenticated(self):
            cookie=SimpleCookie()
            try: cookie.load(self.headers.get('Cookie',''))
            except Exception: return False
            value=cookie.get('coach_session')
            return bool(value and hmac.compare_digest(value.value,token))

        def json(self,status,data):
            raw=json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
            self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(raw)

        def valid_host(self):
            return self.headers.get('Host','') in (f'127.0.0.1:{port}',f'localhost:{port}')

        def do_GET(self):
            if not self.valid_host(): self.json(403,{'error':'Invalid host'}); return
            parsed=urlsplit(self.path); path=parsed.path; query=parse_qs(parsed.query)
            if path=='/' and 'session' in query:
                if not hmac.compare_digest(query['session'][0],token): self.json(403,{'error':'Phiên không hợp lệ.'}); return
                self.send_response(303); self.send_header('Location','/')
                self.send_header('Set-Cookie','coach_session='+token+'; HttpOnly; SameSite=Strict; Path=/')
                self.send_header('Cache-Control','no-store'); self.end_headers(); return
            if not self.authenticated():
                self.json(401,{'error':'Mở Hourly Coach từ shortcut Desktop hoặc khay hệ thống để vào phiên.'}); return
            try:
                if path=='/api/state':
                    date=query.get('date',[day_of()])[0]
                    if len(date)!=10: raise ValueError('Ngày chưa hợp lệ.')
                    settings=store.settings()
                    tasks=store.rows('SELECT id,seq,day,category,skill,level,title,status,sent,due,score,error FROM assignments WHERE day=? ORDER BY seq',(date,))
                    dates=store.rows('SELECT DISTINCT day FROM assignments ORDER BY day DESC')
                    data={'settings':settings,'date':date,'today':day_of(),'stats':store.stats(date),'tasks':tasks,
                        'dates':[r['day'] for r in dates],'activity':engine.activity,'poll_error':engine.poll_error,
                        'schedule':[{'category':c,'skill':s,'slot':i+1} for i,(c,s) in enumerate(SCHEDULE)],
                        'events':store.rows('SELECT * FROM events ORDER BY id DESC LIMIT 20'),
                        'failures':store.rows("SELECT id,kind,error FROM jobs WHERE status='failed' ORDER BY id DESC LIMIT 12"),
                        'delivery_issues':store.rows("SELECT id,status,error FROM outbox WHERE status IN ('failed','uncertain') ORDER BY id LIMIT 12"),
                        'history':[dict(date=r['day'],**store.stats(r['day'])) for r in dates[:30]],
                        'data_path':str(store.root.resolve()),'now':time.time()}
                    waiting=store.one('SELECT seq FROM assignments WHERE sent=0 ORDER BY seq LIMIT 1')
                    data['codex_requests']=store.rows('SELECT id,created,completed,status,model,error,length(answer) AS answer_chars FROM codex_requests ORDER BY created DESC LIMIT 8')
                    data['next_sequence']=waiting['seq'] if waiting else (store.one('SELECT max(seq) AS n FROM assignments')['n'] or 0)+1
                    data['batch']=batch_state(store)
                    data['batch_history']=store.rows('SELECT id,cycle,status,created,completed FROM batches ORDER BY created DESC LIMIT 20')
                    running=store.one("SELECT kind FROM jobs WHERE status='running' LIMIT 1")
                    if running and data['activity']=='Sẵn sàng':
                        data['activity']={'prepare':'Đang chuẩn bị đề trước giờ gửi','generate':'Đang gửi đề',
                            'grade':'Đang chấm bài','preview':'Đang tạo mẫu Antigravity','incoming':'Đang nhận bài'}.get(running['kind'],'Đang xử lý')
                    self.json(200,data); return
                if path=='/api/batch':
                    self.json(200,batch_state(store,query.get('cycle',[None])[0]));return
                if path=='/api/samples':
                    data=samples(); preview=store.root/'ai-preview.json'
                    if preview.exists():
                        source=store.root/'ai-preview-source.json'
                        provider=json.loads(source.read_text(encoding='utf-8')).get('provider','AI') if source.exists() else 'Antigravity'
                        data[0]=data[0]|json.loads(preview.read_text(encoding='utf-8'))|{'source':provider+' · đã kiểm tra cấu trúc'}
                    else: data[0]['source']='Mẫu biên soạn sẵn · chưa phải phản hồi Antigravity'
                    if data[0].get('chart'):
                        chart=render_chart(data[0]['chart'],store.root/'samples')
                        data[0]['chart_image']='/api/file?path='+str(chart.relative_to(store.root)).replace('\\','/')
                    self.json(200,{'samples':data}); return
                if path=='/api/task':
                    task_id=query.get('id',[''])[0]
                    task=store.one('SELECT * FROM assignments WHERE id=?',(task_id,))
                    if not task: self.json(404,{'error':'Không tìm thấy bài.'}); return
                    task['body']=public_assignment(json.loads(task['body']))
                    if task['body'].get('chart'):
                        chart=render_chart(task['body']['chart'],store.root/'assignments'/task_id)
                        task['body']['chart_image']='/api/file?path='+str(chart.relative_to(store.root)).replace('\\','/')
                    task['evaluation']=json.loads(task['evaluation']) if task['evaluation'] else None
                    originals=store.one('SELECT body FROM assignments WHERE id=?',(task_id,))
                    full=json.loads(originals['body']); task['answer_key']=full['answer_key']
                    if full.get('questions'): task['answers']=full['questions']
                    if full.get('listening_sections'): task['transcripts']=full['listening_sections']
                    task['submissions']=store.rows('SELECT id,created,text,files,status,error,evaluation FROM submissions WHERE assignment_id=? ORDER BY created DESC',(task_id,))
                    for sub in task['submissions']:
                        sub['files']=[{'name':Path(p).name,'url':'/api/file?path='+__import__('urllib.parse',fromlist=['quote']).quote(str(Path(p).resolve().relative_to(store.root.resolve())))} for p in json.loads(sub['files'])]
                        batch=store.one('SELECT b.id,b.status FROM batch_items i JOIN batches b ON b.id=i.batch_id WHERE i.submission_id=?',(sub['id'],))
                        sub['evaluation']=json.loads(sub['evaluation']) if sub['evaluation'] and (not batch or batch['status'] in FINAL) else None
                        sub['batch_id']=batch['id'] if batch else None
                    draft=store.one('SELECT * FROM drafts WHERE assignment_id=?',(task_id,))
                    task['draft']={'text':draft['text'],'complete':bool(draft['complete']),'assistance':draft['assistance'],'files':[{'path':str(Path(p).resolve().relative_to(store.root.resolve())).replace('\\','/'),'name':Path(p).name} for p in json.loads(draft['files'])]} if draft else {'text':'','files':[],'complete':False,'assistance':'unknown'}
                    task['batch']=batch_state(store,(task['seq']-1)//12+1)
                    task['audio']=[{'name':p.name,'url':'/api/file?path='+str(p.relative_to(store.root)).replace('\\','/')} for p in (store.root/'assignments'/task_id).glob('*.wav')]
                    self.json(200,task); return
                if path=='/api/health': self.json(200,engine.gateway.health()); return
                if path=='/api/codex/request':
                    row=store.one('SELECT * FROM codex_requests WHERE id=?',(query.get('id',[''])[0],))
                    if not row: self.json(404,{'error':'Không tìm thấy yêu cầu.'}); return
                    self.json(200,row); return
                if path=='/api/file':
                    relative=query.get('path',[''])[0]
                    target=(store.root/relative).resolve()
                    if not target.is_relative_to(store.root.resolve()) or not target.is_file(): self.json(404,{'error':'File không tồn tại.'}); return
                    if target.suffix.lower() not in ALLOWED: self.json(403,{'error':'File không được phép tải.'}); return
                    self.serve_file(target,download=target.suffix.lower() not in ('.png','.jpg','.jpeg','.webp','.wav','.mp3','.ogg','.m4a')); return
                target=web/('index.html' if path=='/' else path.lstrip('/'))
                if target.resolve().is_relative_to(web) and target.is_file(): self.serve_file(target); return
                self.json(404,{'error':'Không tìm thấy.'})
            except (ValueError,KeyError) as e: self.json(400,{'error':str(e)})
            except Exception: self.json(500,{'error':'Lỗi ứng dụng. Xem data/app.log hoặc khởi động lại.'})

        def serve_file(self,path,download=False):
            raw=path.read_bytes(); mime=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
            self.send_response(200); self.send_header('Content-Type',mime+('; charset=utf-8' if mime.startswith('text/') else ''))
            self.send_header('Content-Length',str(len(raw))); self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if download: self.send_header('Content-Disposition','attachment')
            self.end_headers(); self.wfile.write(raw)

        def do_POST(self):
            if urlsplit(self.path).path=='/ask':
                self.codex_ask(); return
            if not self.valid_host() or not self.authenticated(): self.json(403,{'error':'Phiên không hợp lệ.'}); return
            origin=self.headers.get('Origin','')
            if origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):
                self.json(403,{'error':'Origin không hợp lệ.'}); return
            if self.headers.get('X-Coach-Request')!='1' or not self.headers.get('Content-Type','').startswith('application/json'):
                self.json(403,{'error':'Yêu cầu không hợp lệ.'}); return
            try:
                size=int(self.headers.get('Content-Length',0))
                limit=(MAX_VIDEO*4//3+1024*1024) if urlsplit(self.path).path=='/api/upload' else 29*1024*1024
                if not 0<size<limit: raise ValueError('Yêu cầu quá lớn hoặc trống.')
                data=json.loads(self.rfile.read(size)); path=urlsplit(self.path).path
                result={'ok':True}
                if path=='/api/settings':
                    # Validate everything before persisting. Blank secret fields preserve saved credentials.
                    url=Gateway.validate_url(data.get('gateway_url',store.get('gateway_url')))
                    band=float(data.get('band',6.5)); goal=float(data.get('goal_band',8))
                    if not 0<=band<=9 or not 0<goal<=9: raise ValueError('Band cần trong khoảng 0–9.')
                    token_value=str(data.get('telegram_token','')).strip()
                    key_value=str(data.get('gateway_key','')).strip()
                    if token_value and not __import__('re').fullmatch(r'\d+:[A-Za-z0-9_-]{20,}',token_value): raise ValueError('Bot token sai định dạng.')
                    speech_python=str(data.get('speech_python','')).strip()
                    if speech_python and not Path(speech_python).is_file(): raise ValueError('Không tìm thấy Python giọng nói.')
                    changed=bool(token_value and token_value!=store.secret('telegram_token'))
                    if changed and store.one('SELECT id FROM assignments WHERE sent>0'):
                        raise ValueError('Đã có bài gửi. Dùng nguyên bot này để giữ lịch sử; không đổi bot giữa lộ trình.')
                    model=data.get('speech_model','base')
                    if model not in ('tiny','base','small'): raise ValueError('Model giọng nói chưa hợp lệ.')
                    verified_bot=None
                    if token_value:
                        verified_bot=engine.telegram.call('getMe',token_override=token_value)
                        webhook=engine.telegram.call('getWebhookInfo',token_override=token_value)
                        if webhook.get('url'): raise ValueError('Bot có webhook. Dùng bot riêng; cấu hình cũ chưa bị thay đổi.')
                    if token_value: store.secret('telegram_token',token_value)
                    if key_value: store.secret('gateway_key',key_value)
                    store.set(gateway_url=url,band=band,goal_band=goal,speech_python=speech_python,speech_model=model)
                    if changed: store.set(telegram_chat_id='',telegram_username='',offset=0,pairing_code=secrets.token_hex(4),active=False)
                    if verified_bot:
                        store.set(telegram_username=verified_bot.get('username',''))
                    elif store.get('telegram_token'):
                        if engine.poll_error: result['warning']=engine.poll_error
                    store.event('settings','Đã cập nhật cấu hình; bí mật được mã hóa bằng Windows DPAPI.')
                elif path=='/api/codex/settings':
                    provider=data.get('ai_provider','codex_chat')
                    if provider not in ('codex_chat','antigravity'): raise ValueError('Nhà cung cấp chưa hợp lệ.')
                    thread_id=str(data.get('codex_thread_id',store.get('codex_thread_id'))).strip()
                    if not __import__('re').fullmatch(r'[a-zA-Z0-9_-]{8,100}',thread_id): raise ValueError('Thread ID Codex chưa hợp lệ.')
                    access_key=str(data.get('codex_access_key','')).strip()
                    if access_key and len(access_key)<16: raise ValueError('Key riêng cần ít nhất 16 ký tự.')
                    effort=data.get('codex_reasoning_effort',store.get('codex_reasoning_effort') or '')
                    if effort not in ('','low','medium','high','xhigh'): raise ValueError('Mức suy nghĩ Codex chưa hợp lệ.')
                    if access_key: store.secret('codex_access_key',access_key)
                    store.set(ai_provider=provider,codex_thread_id=thread_id,codex_reasoning_effort=effort)
                    store.event('settings','Đã chọn '+engine.gateway.name+'; key riêng được mã hóa bằng Windows DPAPI.')
                elif path=='/api/codex/chat':
                    image=''
                    if data.get('image'):
                        image=(store.root/str(data['image'])).resolve()
                        if not image.is_relative_to((store.root/'uploads').resolve()) or not image.is_file():
                            raise ValueError('Ảnh tải lên chưa hợp lệ.')
                    result=engine.gateway.codex.ask(data.get('prompt'),image,request_id=data.get('request_id'))
                elif path=='/api/approve':
                    store.set(approved=True); store.event('approve','Người dùng đã duyệt mẫu cấu trúc đề.')
                    if engine.ready(): engine.activate()
                    else: result['message']='Đã duyệt mẫu. Kết nối Codex hoặc Antigravity để bật lịch.'
                elif path=='/api/telegram/test':
                    if not store.get('telegram_chat_id') or not store.get('telegram_token'):
                        raise ValueError('Lưu bot token, mở bot và bấm Start để ghép trước khi thử thông báo.')
                    store.enqueue('telegram_test',{},'telegram-test:'+secrets.token_hex(8)); engine.wake.set()
                elif path=='/api/toggle':
                    if store.get('active'): store.set(active=False)
                    else: engine.activate()
                elif path=='/api/preview': store.enqueue('preview',{},'preview:'+secrets.token_hex(8)); engine.wake.set()
                elif path=='/api/sample': store.enqueue('sample',{},'sample-job:'+secrets.token_hex(8)); engine.wake.set()
                elif path=='/api/now':
                    if not engine.ready() or not store.get('active'): raise ValueError('Duyệt mẫu và bật lịch trước khi gửi đề.')
                    if store.one("SELECT id FROM jobs WHERE kind IN ('generate','prepare') AND status IN ('pending','running','failed')"): raise ValueError('Đã có đề đang tạo hoặc cần thử lại.')
                    waiting=store.one('SELECT seq FROM assignments WHERE sent=0 ORDER BY seq LIMIT 1')
                    seq=waiting['seq'] if waiting else (store.one('SELECT max(seq) AS n FROM assignments')['n'] or 0)+1
                    store.enqueue('generate',{'seq':seq},'manual:'+secrets.token_hex(8)); engine.wake.set()
                elif path=='/api/upload':
                    name=Path(str(data.get('name',''))).name; suffix=Path(name).suffix.lower()
                    if suffix not in ALLOWED: raise ValueError('Định dạng file chưa hỗ trợ.')
                    raw=base64.b64decode(data.get('data',''),validate=True)
                    limit=MAX_VIDEO if suffix in VIDEO else MAX_FILE
                    if not raw or len(raw)>limit: raise ValueError('Video tối đa 100 MB; file khác tối đa 20 MB.')
                    folder=store.root/'uploads'/secrets.token_hex(12); folder.mkdir(parents=True)
                    target=folder/name; target.write_bytes(raw)
                    result={'ok':True,'path':str(target.relative_to(store.root)),'name':name}
                elif path=='/api/submit':
                    raise ValueError('Lưu bài nháp ở cuối đề. Cần đủ 12 đề rồi bấm Gửi tất cả & chấm, không chấm riêng từng đề.')
                elif path=='/api/batch/submit':
                    request_id=str(data.get('request_id',''))
                    if not __import__('re').fullmatch('[a-f0-9]{32}',request_id):raise ValueError('Mã gửi bộ bài chưa hợp lệ.')
                    result['batch_id']=submit_batch(engine,int(data['cycle']),request_id)
                elif path=='/api/draft':
                    files=[]
                    for name in data.get('files',[]):
                        p=(store.root/name).resolve()
                        if not p.is_relative_to((store.root/'uploads').resolve()) or not p.is_file(): raise ValueError('File bài nộp không hợp lệ.')
                        files.append(str(p))
                    if not isinstance(data.get('complete'),bool):raise ValueError('Trạng thái hoàn thành chưa hợp lệ.')
                    result['batch']=save_draft(store,data['id'],str(data.get('text','')),files,data['complete'],str(data.get('assistance','unknown')))
                elif path=='/api/answers': engine.reveal_answer(data['id'])
                elif path=='/api/retry': engine.retry(bool(data.get('include_uncertain')))
                elif path=='/api/verify': engine.verify_criteria(data['id'],data['scores'],str(data.get('note','')))
                else: self.json(404,{'error':'Không tìm thấy API.'}); return
                self.json(200,result)
            except ChatError as e: self.json(e.status,{'error':str(e)})
            except (ValueError,KeyError,TypeError) as e: self.json(400,{'error':str(e)})
            except Exception: self.json(500,{'error':'Không hoàn thành thao tác. Xem nhật ký rồi thử lại.'})

        def codex_ask(self):
            if not self.valid_host(): self.json(403,{'error':'Invalid host'}); return
            origin=self.headers.get('Origin','')
            if origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):
                self.json(403,{'error':'Origin không hợp lệ.'}); return
            try:
                key=store.secret('codex_access_key')
                if not key: self.json(503,{'error':'Đặt key riêng trong Cài đặt kết nối → Codex Chat trước.'}); return
                supplied=self.headers.get('Authorization','')
                if not supplied.startswith('Bearer ') or not hmac.compare_digest(supplied[7:].encode(),key.encode()):
                    self.json(401,{'error':'Key truy cập Codex Chat không hợp lệ.'}); return
                if not self.headers.get('Content-Type','').startswith('application/json'):
                    self.json(415,{'error':'Cần Content-Type: application/json.'}); return
                size=int(self.headers.get('Content-Length',0))
                if not 0<size<=8*1024*1024: self.json(413,{'error':'Body phải từ 1 byte đến 8 MB.'}); return
                data=json.loads(self.rfile.read(size))
                if not isinstance(data,dict): raise ValueError('Body cần là JSON object.')
                data.setdefault('request_id',secrets.token_hex(16))
                timeout=float(data.get('timeout_seconds',900))
                if not 1<=timeout<=1800: raise ValueError('timeout_seconds cần từ 1 đến 1800.')
                result=engine.gateway.codex.ask(data.get('prompt'),data.get('image_path',''),
                                               request_id=data.get('request_id'),timeout=timeout)
                self.json(200,result)
            except ChatError as error: self.json(error.status,{'error':str(error),'request_id':data.get('request_id') if isinstance(locals().get('data'),dict) else None})
            except (ValueError,TypeError) as error: self.json(400,{'error':str(error)})
            except (BrokenPipeError,ConnectionResetError): pass
            except Exception: self.json(502,{'error':'Không nhận được đáp án Codex. Xem log trong Cài đặt kết nối.'})

    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    port=server.server_address[1]
    server.daemon_threads=True
    return server,token
