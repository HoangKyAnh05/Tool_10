"""Install the original 120-exercise bank while Hourly Coach is closed."""
import socket
import sys
from pathlib import Path
from coach.store import Store
from coach.engine import Engine
from coach.practice_bank import install_bank


def main():
    try:
        with socket.create_connection(('127.0.0.1',8766),timeout=1):
            raise SystemExit('Thoát Hourly Coach từ khay hệ thống trước khi cài ngân hàng đề.')
    except OSError:
        pass
    store=Store(Path(__file__).resolve().parent/'data');engine=Engine(store)
    try:
        cycles=install_bank(engine)
        print(f'Đã có {len(cycles)} bộ · 120 đề và đáp án. Mở lại Hourly Coach để làm bài.')
    finally:
        engine.gateway.codex.close();store.db.close()


if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr,'reconfigure'):sys.stderr.reconfigure(encoding='utf-8')
    main()
