"""A private chat bridge using Codex's documented App Server protocol."""
import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path


class ChatError(RuntimeError):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


class CodexChat:
    def __init__(self, store):
        self.store = store
        self.lock = threading.RLock()
        self.request_condition = threading.Condition()
        self.request_order = []
        self.process = None
        self.events = queue.Queue()
        self.sequence = 0
        self.bound_thread = None
        self.bound_effort = None
        self.auth_stamp = None
        self.info = {}
        self.store.execute('''CREATE TABLE IF NOT EXISTS codex_requests(
            id TEXT PRIMARY KEY, fingerprint TEXT, created REAL, completed REAL,
            status TEXT, thread_id TEXT, turn_id TEXT, model TEXT,
            prompt TEXT, image_path TEXT, answer TEXT, error TEXT, http_status INTEGER)''')

    def close(self,force=False):
        # Shutdown must unblock a long answer before waiting for its request lock.
        # The interrupted request records a failure; it is never counted as a result.
        if force:
            process=self.process
            if process and process.poll() is None:
                try:process.terminate()
                except OSError:pass
        with self.lock:
            if self.process:
                if self.process.poll() is None:
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                self.process = None
            self.bound_thread = None
            self.bound_effort = None
            self.auth_stamp = None
            self.info = {}

    def _send(self, message):
        try:
            self.process.stdin.write(json.dumps(message, ensure_ascii=False) + '\n')
            self.process.stdin.flush()
        except (OSError, ValueError, AttributeError):
            raise ChatError('Kết nối Codex bị ngắt; yêu cầu chưa được tự gửi lại.') from None

    def _read(self, process, events):
        try:
            for line in process.stdout:
                if not line.strip():
                    continue
                try:
                    events.put(json.loads(line))
                except ValueError:
                    events.put({'_error': 'Codex trả dữ liệu giao thức không hợp lệ.'})
        finally:
            events.put({'_error': 'App Server Codex đã đóng kết nối.'})

    def _next(self, deadline):
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ChatError('Hết thời gian chờ Codex. Xem log yêu cầu trước khi gửi lại.', 504)
            try:
                message = self.events.get(timeout=min(remaining, 1))
            except queue.Empty:
                continue
            if '_error' in message:
                raise ChatError(message['_error'])
            if 'method' in message and 'id' in message:
                # The gateway returns chat answers; it never approves background actions.
                if message['method'] in ('item/commandExecution/requestApproval', 'item/fileChange/requestApproval'):
                    self._send({'id': message['id'], 'result': {'decision': 'decline'}})
                else:
                    self._send({'id': message['id'], 'error': {'code': -32601,
                                'message': 'This chat gateway cannot answer interactive tool requests.'}})
                continue
            return message

    def _call(self, method, params, timeout=45):
        self.sequence += 1
        request_id = self.sequence
        self._send({'id': request_id, 'method': method, 'params': params})
        deadline = time.monotonic() + timeout
        deferred = []
        try:
            while True:
                message = self._next(deadline)
                if message.get('id') == request_id:
                    if 'error' in message:
                        raise ChatError(str(message['error'].get('message', 'Lỗi Codex App Server')))
                    return message.get('result', {})
                deferred.append(message)
        finally:
            for message in deferred:
                self.events.put(message)

    @staticmethod
    def _auth_stamp():
        root=Path(os.environ.get('CODEX_HOME') or (Path.home()/'.codex'))
        try:
            stat=(root/'auth.json').stat()
            return (stat.st_mtime_ns,stat.st_size,stat.st_ctime_ns)
        except OSError:return None

    def _connect(self):
        thread_id = self.store.get('codex_thread_id')
        effort = self.store.get('codex_reasoning_effort') or ''
        if effort not in ('', 'low', 'medium', 'high', 'xhigh'):
            raise ChatError('Mức suy nghĩ Codex chưa hợp lệ.', 400)
        if not isinstance(thread_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{8,100}', thread_id):
            raise ChatError('Chưa chọn cuộc chat Codex riêng cho tool.', 400)
        auth_stamp=self._auth_stamp()
        if self.process and self.process.poll() is None and self.bound_thread == thread_id and self.bound_effort == effort and self.auth_stamp == auth_stamp:
            return
        self.close()
        executable = shutil.which('codex')
        if not executable and os.name == 'nt':
            installed = list((Path(os.environ.get('LOCALAPPDATA', '')) / 'OpenAI' / 'Codex' / 'bin').glob('*/codex.exe'))
            if installed:
                executable = str(max(installed, key=lambda path: path.stat().st_mtime))
        if not executable:
            raise ChatError('Chưa tìm thấy Codex CLI trên máy.', 503)
        env = os.environ.copy()
        for name in ('OPENAI_API_KEY', 'CODEX_API_KEY'):
            env.pop(name, None)
        self.events = queue.Queue()
        self.process = subprocess.Popen([executable, 'app-server', '--stdio'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding='utf-8', env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        threading.Thread(target=self._read, args=(self.process, self.events), daemon=True).start()
        self._call('initialize', {'clientInfo': {'name': 'hourly_coach_chat_gateway',
                    'title': 'Hourly Coach Codex Chat Gateway', 'version': '1.0.0'}})
        self._send({'method': 'initialized', 'params': {}})
        account = self._call('account/read', {'refreshToken': False}).get('account') or {}
        if account.get('type') != 'chatgpt':
            self.close()
            raise ChatError('Đăng nhập Codex bằng ChatGPT để dùng cuộc chat này.', 503)
        # Keep the chat's model; override effort only when the user selects it.
        resume_params = {'threadId': thread_id, 'approvalPolicy': 'never', 'sandbox': 'read-only'}
        if effort:
            resume_params['config'] = {'model_reasoning_effort': effort}
        try:
            result = self._call('thread/resume', resume_params)
        except ChatError as error:
            if 'already has an active writer' not in str(error):
                raise
            # Another app may own the selected chat after an account switch.
            # A single fork retains its history, model and
            # instructions while giving the gateway one exclusive writer.
            result = self._call('thread/fork', resume_params)
            thread_id = result['thread']['id']
            self.store.set(codex_thread_id=thread_id)
            self._call('thread/name/set', {'threadId': thread_id, 'name': 'Codex Chat Gateway · API'})
        if result.get('modelProvider') != 'openai':
            self.close()
            raise ChatError('Chat đã chọn chưa dùng nhà cung cấp OpenAI với đăng nhập ChatGPT.', 400)
        if result.get('thread', {}).get('status', {}).get('type') == 'active':
            self.close()
            raise ChatError('Chat Codex đang có một lượt chạy khác. Hãy đợi lượt đó hoàn tất.', 409)
        self.bound_thread = thread_id
        self.bound_effort = effort
        self.auth_stamp = self._auth_stamp()
        self.info = {'thread_id': thread_id, 'model': result.get('model'),
                     'reasoning_effort': result.get('reasoningEffort'), 'auth_type': 'chatgpt'}

    def health(self):
        # A long answer must not block dashboard polling.
        if not self.lock.acquire(blocking=False):
            return {'online': True, 'service': 'Codex Chat Gateway', 'busy': True, **self.info}
        try:
            self._connect()
            return {'online': True, 'service': 'Codex Chat Gateway', 'busy': False, **self.info}
        except Exception as error:
            self.close()
            return {'online': False, 'service': 'Codex Chat Gateway', 'error': str(error)}
        finally:
            self.lock.release()

    def ask(self, prompt, image_path='', request_id=None, timeout=900):
        if not isinstance(prompt, str) or not prompt.strip():
            raise ChatError('Cần nhập câu hỏi.', 400)
        if len(prompt.encode('utf-8')) > 8 * 1024 * 1024:
            raise ChatError('Câu hỏi vượt 8 MB; hãy chia tài liệu thành các phần.', 413)
        image_path = str(image_path or '')
        if image_path and (not Path(image_path).is_file() or Path(image_path).suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.gif')):
            raise ChatError('Đường dẫn ảnh chưa hợp lệ.', 400)
        request_id = request_id or str(uuid.uuid4())
        if not isinstance(request_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{8,100}', request_id):
            raise ChatError('request_id cần 8–100 ký tự chữ, số, dấu - hoặc _.', 400)
        fingerprint = hashlib.sha256(json.dumps([prompt, image_path], ensure_ascii=False).encode()).hexdigest()
        ticket=object()
        with self.request_condition:
            self.request_order.append(ticket)
            if not self.request_condition.wait_for(lambda:self.request_order[0] is ticket,timeout=900):
                self.request_order.remove(ticket);self.request_condition.notify_all()
                raise ChatError('Hàng đợi Codex đang quá dài. Bài đã lưu; thử lại sau.',503)
        if not self.lock.acquire(timeout=90):
            with self.request_condition:
                self.request_order.remove(ticket);self.request_condition.notify_all()
            raise ChatError('Chat đang bận. Thử lại sau khi yêu cầu hiện tại hoàn tất.', 503)
        try:
            previous = self.store.one('SELECT * FROM codex_requests WHERE id=?', (request_id,))
            if previous:
                if previous['fingerprint'] != fingerprint:
                    raise ChatError('request_id đã được dùng với câu hỏi khác.', 409)
                if previous['status'] != 'completed':
                    raise ChatError('Yêu cầu này đã được nhận; xem log trước khi tạo lượt mới.', 409)
                return {'status': 'success', 'answer': previous['answer'], 'request_id': request_id,
                        'thread_id': previous['thread_id'], 'turn_id': previous['turn_id'],
                        'model': previous['model'], 'cached': True}
            self.store.execute('INSERT INTO codex_requests(id,fingerprint,created,status,prompt,image_path) VALUES(?,?,?,?,?,?)',
                               (request_id, fingerprint, time.time(), 'running', prompt, image_path))
            turn_id = None
            try:
                self._connect()
                inputs = [{'type': 'text', 'text': prompt}]
                if image_path:
                    inputs.append({'type': 'localImage', 'path': str(Path(image_path).resolve())})
                turn_params = {'threadId': self.bound_thread, 'input': inputs}
                if self.bound_effort:
                    turn_params['effort'] = self.bound_effort
                result = self._call('turn/start', turn_params)
                turn_id = result['turn']['id']
                self.store.execute('UPDATE codex_requests SET thread_id=?,turn_id=?,model=? WHERE id=?',
                    (self.bound_thread, turn_id, self.info.get('model'), request_id))
                deadline = time.monotonic() + timeout
                items = {}
                while True:
                    message = self._next(deadline)
                    params = message.get('params', {})
                    if params.get('threadId') != self.bound_thread:
                        continue
                    if params.get('turnId') and params['turnId'] != turn_id:
                        continue
                    method = message.get('method')
                    if method == 'item/completed':
                        item = params.get('item', {})
                        if item.get('type') == 'agentMessage':
                            items[item['id']] = item
                    if method == 'turn/completed' and params.get('turn', {}).get('id') == turn_id:
                        turn = params['turn']
                        if turn.get('status') != 'completed':
                            error = turn.get('error') or {}
                            raise ChatError(str(error.get('message') or 'Codex chưa hoàn tất câu trả lời.'))
                        for item in turn.get('items', []):
                            if item.get('type') == 'agentMessage':
                                items[item['id']] = item
                        finals = [i.get('text', '') for i in items.values() if i.get('phase') in ('final_answer', None)]
                        answer = '\n\n'.join(text for text in finals if text.strip())
                        if not answer.strip():
                            raise ChatError('Codex hoàn tất lượt nhưng chưa có nội dung trả lời.')
                        self.store.execute('UPDATE codex_requests SET status=?,completed=?,answer=?,http_status=200 WHERE id=?',
                            ('completed', time.time(), answer, request_id))
                        return {'status': 'success', 'answer': answer, 'request_id': request_id,
                                'thread_id': self.bound_thread, 'turn_id': turn_id,
                                'model': self.info.get('model'), 'cached': False}
            except Exception as error:
                if isinstance(error, ChatError) and error.status == 504 and turn_id:
                    try:
                        self._call('turn/interrupt', {'threadId': self.bound_thread, 'turnId': turn_id}, timeout=10)
                    except Exception:
                        pass
                self.store.execute('UPDATE codex_requests SET status=?,completed=?,error=?,http_status=? WHERE id=?',
                    ('failed', time.time(), str(error), getattr(error, 'status', 502), request_id))
                self.close()
                raise
        finally:
            self.lock.release()
            with self.request_condition:
                self.request_order.remove(ticket);self.request_condition.notify_all()
