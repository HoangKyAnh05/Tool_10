import sys
from pathlib import Path

if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from coach.store import Store
    store=Store(Path(__file__).resolve().parents[1]/'data',recover=False)
    store.set(speech_python=str(Path(sys.argv[1]).resolve()))
    store.event('speech','Đã cài bộ chép lời audio và đọc video cục bộ.')
    store.db.close()
