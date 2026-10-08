import time
import threading
from pathlib import Path
import requests
from .media import MAX_FILE


def chunks(text,limit=3500):
    """Keep below Telegram's UTF-16 character limit even with emoji."""
    result=[]; current=''; units=0
    for char in text:
        size=2 if ord(char)>0xffff else 1
        if units+size>limit:
            result.append(current); current=''; units=0
        current+=char; units+=size
    if current: result.append(current)
    return result


class Telegram:
    def __init__(self,store): self.store=store; self.send_lock=threading.RLock()

    def call(self,method,payload=None,files=None,timeout=30,token_override=None):
        token=token_override or self.store.secret('telegram_token')
        if not token: raise ValueError('Chưa có Telegram Bot Token.')
        try:
            response=requests.post('https://api.telegram.org/bot'+token+'/'+method,
                data=payload or {},files=files,timeout=(5,timeout))
        except requests.RequestException:
            # Never expose a requests exception: it includes the credential-bearing URL.
            raise RuntimeError('Telegram mất kết nối; kết quả gửi có thể chưa xác định.') from None
        try: data=response.json()
        except ValueError: raise RuntimeError('Telegram trả phản hồi không hợp lệ.') from None
        if not data.get('ok'):
            code=data.get('error_code',response.status_code)
            messages={401:'Bot token chưa hợp lệ.',403:'Bot bị chặn hoặc chưa được bắt đầu.',
                      409:'Bot đang được ứng dụng khác đọc hoặc có webhook. Dùng một bot riêng cho Hourly Coach.',
                      429:'Telegram giới hạn tần suất. Đợi rồi thử lại.'}
            raise ValueError(messages.get(code,f'Telegram HTTP {code}: yêu cầu bị từ chối.'))
        return data['result']

    def download(self,file_id,target):
        info=self.call('getFile',{'file_id':file_id})
        if info.get('file_size',0)>MAX_FILE:
            raise ValueError('Telegram Bot tải tối đa 20 MB/file. Giảm kích thước rồi gửi lại.')
        token=self.store.secret('telegram_token')
        try:
            with requests.get('https://api.telegram.org/file/bot'+token+'/'+info['file_path'],
                stream=True,timeout=(5,90)) as response:
                response.raise_for_status(); size=0
                with Path(target).open('wb') as f:
                    for part in response.iter_content(65536):
                        size+=len(part)
                        if size>MAX_FILE: raise ValueError('File vượt 20 MB.')
                        f.write(part)
        except requests.RequestException:
            raise RuntimeError('Không tải được file Telegram. Thử gửi lại.') from None

    def queue_text(self,text,dedupe,assignment_id=''):
        for i,part in enumerate(chunks(text)):
            self.store.execute('INSERT OR IGNORE INTO outbox(dedupe,assignment_id,kind,payload) VALUES(?,?,?,?)',
                (f'{dedupe}:{i}',assignment_id,'text',part))

    def queue_file(self,path,dedupe,assignment_id='',caption='',kind='document'):
        self.store.execute('INSERT OR IGNORE INTO outbox(dedupe,assignment_id,kind,payload) VALUES(?,?,?,?)',
            (dedupe,assignment_id,kind,str(path)+'\n'+caption))

    def flush(self):
        with self.send_lock:
            return self._flush()

    def _flush(self):
        # One worker owns dispatch. Record intent before I/O, then the acknowledged message id.
        for item in self.store.rows("SELECT * FROM outbox WHERE status='pending' ORDER BY id"):
            self.store.execute("UPDATE outbox SET status='sending' WHERE id=?",(item['id'],))
            try:
                payload={'chat_id':self.store.get('telegram_chat_id')}
                if not payload['chat_id']: raise ValueError('Chưa ghép tài khoản Telegram.')
                if item['kind']=='text':
                    result=self.call('sendMessage',payload|{'text':item['payload']})
                else:
                    path,caption=item['payload'].split('\n',1)
                    field={'audio':'audio','photo':'photo'}.get(item['kind'],'document')
                    method={'audio':'sendAudio','photo':'sendPhoto','document':'sendDocument'}[field]
                    with open(path,'rb') as f:
                        result=self.call(method,
                            payload|{'caption':caption[:900]},files={field:(Path(path).name,f)})
                message_id=result['message_id']
                with self.store.lock:
                    self.store.db.execute("UPDATE outbox SET status='sent',message_id=?,error='' WHERE id=?",(message_id,item['id']))
                    if item['assignment_id']:
                        self.store.db.execute('INSERT OR REPLACE INTO telegram_messages VALUES(?,?)',(message_id,item['assignment_id']))
                    self.store.db.commit()
            except Exception as e:
                # Explicit HTTP rejection is safe to retry. Transport failure is ambiguous.
                state='failed' if isinstance(e,(ValueError,OSError)) else 'uncertain'
                self.store.execute('UPDATE outbox SET status=?,error=? WHERE id=?',(state,str(e),item['id']))
                raise
            time.sleep(0.12)
