"""Use managed Codex Chat for generation and grading."""
from .codex_chat import CodexChat

class Gateway:
    def __init__(self,store):self.codex=CodexChat(store)
    @property
    def name(self):return 'Codex'
    def health(self):return self.codex.health()
    def ask(self,prompt,image_path=''):return self.codex.ask(prompt,image_path)['answer']
