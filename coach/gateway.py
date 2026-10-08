import re
import threading
from urllib.parse import urlsplit
import requests


class Gateway:
    def __init__(self,store):
        self.store=store
        self.lock=threading.Lock()
        from .codex_chat import CodexChat
        self.codex=CodexChat(store)

    @property
    def name(self):
        return 'Codex' if self.store.get('ai_provider')=='codex_chat' else 'Antigravity'

    @staticmethod
    def validate_url(url):
        parsed=urlsplit(url)
        if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost') or parsed.path!='/ask' or parsed.username or parsed.query or parsed.fragment:
            raise ValueError('Gateway phải là http://127.0.0.1:<port>/ask trên máy này.')
        return url

    def health(self):
        if self.store.get('ai_provider')=='codex_chat':
            return self.codex.health()
        url=self.validate_url(self.store.get('gateway_url'))
        try:
            response=requests.get(url.rsplit('/ask',1)[0]+'/health',timeout=(3,5))
            result=response.json()
            return {'online':response.ok,'service':str(result.get('service','Gateway'))[:100]}
        except (requests.RequestException,ValueError):
            return {'online':False,'service':'Không kết nối được gateway'}

    def ask(self,prompt,image_path=''):
        if self.store.get('ai_provider')=='codex_chat':
            return self.codex.ask(prompt,image_path)['answer']
        url=self.validate_url(self.store.get('gateway_url'))
        key=self.store.secret('gateway_key')
        if not key:
            raise ValueError('Bạn chưa nhập key Antigravity trong Cài đặt.')
        prompt=re.sub('trả một object json','xuất duy nhất đối tượng JSON',prompt,flags=re.I)
        with self.lock:
            try:
                response=requests.post(url,headers={'Authorization':'Bearer '+key},
                    json={'prompt':prompt,'image_path':str(image_path)},timeout=(5,300))
            except requests.RequestException:
                raise RuntimeError('Không nhận được phản hồi Antigravity; kiểm tra gateway/relay và thử lại.') from None
            try:
                data=response.json()
            except ValueError:
                raise RuntimeError('Gateway trả phản hồi không phải JSON.') from None
            if not response.ok:
                raise RuntimeError(f"Antigravity HTTP {response.status_code}: yêu cầu thất bại hoặc relay hết thời gian.")
            answer=data.get('answer')
            if not isinstance(answer,str) or not answer.strip():
                raise RuntimeError('Gateway chưa trả nội dung từ Antigravity.')
            return answer
