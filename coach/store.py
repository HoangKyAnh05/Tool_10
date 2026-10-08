import base64
import ctypes
import json
import os
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=7))


def day_of(timestamp=None):
    return datetime.fromtimestamp(timestamp or time.time(), TZ).strftime('%Y-%m-%d')


class Blob(ctypes.Structure):
    _fields_ = [('size', ctypes.c_ulong), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def protect(value, decrypt=False):
    """Windows DPAPI; credentials belong to the signed-in Windows account."""
    if os.name != 'nt':
        raise RuntimeError('Kho bí mật này yêu cầu Windows DPAPI.')
    raw = base64.b64decode(value) if decrypt else value.encode('utf-8')
    buffer = ctypes.create_string_buffer(raw)
    source = Blob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    fn = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise RuntimeError('Không thể mở kho bí mật Windows.')
    try:
        result = ctypes.string_at(target.data, target.size)
        return result.decode('utf-8') if decrypt else base64.b64encode(result).decode('ascii')
    finally:
        ctypes.windll.kernel32.LocalFree(target.data)


DEFAULTS = dict(gateway_url='http://127.0.0.1:8000/ask', ai_provider='antigravity', codex_thread_id='', codex_seed_thread_id='', codex_reasoning_effort='', telegram_chat_id='',
    telegram_username='', telegram_notifications_only=True, pairing_code=secrets.token_hex(4), approved=False, active=False,
    next_due=0, interval=3600, band=6.5, goal_band=8.0, level=1.0, offset=0,
    selected_assignment='', speech_model='base', speech_python='', last_growth_cycle=0)


class Store:
    def __init__(self, root, recover=True):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.root / 'coach.sqlite3', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS assignments(
            id TEXT PRIMARY KEY, seq INTEGER UNIQUE, day TEXT, category TEXT, skill TEXT,
            level REAL, title TEXT, body TEXT, status TEXT, created REAL,
            sent REAL DEFAULT 0, due REAL DEFAULT 0, score REAL,
            evaluation TEXT, completed REAL DEFAULT 0, error TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS submissions(
            id TEXT PRIMARY KEY, assignment_id TEXT REFERENCES assignments(id),
            created REAL, text TEXT, files TEXT, status TEXT, error TEXT DEFAULT '',
            analysis TEXT DEFAULT '', evaluation TEXT);
        CREATE TABLE IF NOT EXISTS jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, payload TEXT,
            dedupe TEXT UNIQUE, status TEXT DEFAULT 'pending', created REAL,
            attempts INTEGER DEFAULT 0, error TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS telegram_messages(
            message_id INTEGER PRIMARY KEY, assignment_id TEXT);
        CREATE TABLE IF NOT EXISTS drafts(
            assignment_id TEXT PRIMARY KEY, text TEXT DEFAULT '', files TEXT DEFAULT '[]');
        CREATE TABLE IF NOT EXISTS outbox(
            id INTEGER PRIMARY KEY AUTOINCREMENT, dedupe TEXT UNIQUE,
            assignment_id TEXT, kind TEXT, payload TEXT, status TEXT DEFAULT 'pending',
            message_id INTEGER, error TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, created REAL, kind TEXT, message TEXT);
        ''')
        columns={r[1] for r in self.db.execute('PRAGMA table_info(assignments)')}
        if 'answer_viewed' not in columns:
            self.db.execute('ALTER TABLE assignments ADD COLUMN answer_viewed REAL DEFAULT 0')
        if 'assistance' not in columns:
            self.db.execute("ALTER TABLE assignments ADD COLUMN assistance TEXT DEFAULT 'unknown'")
        sub_columns={r[1] for r in self.db.execute('PRAGMA table_info(submissions)')}
        if 'assistance' not in sub_columns:
            self.db.execute("ALTER TABLE submissions ADD COLUMN assistance TEXT DEFAULT 'unknown'")
        for key, value in DEFAULTS.items():
            self.db.execute('INSERT OR IGNORE INTO settings VALUES(?,?)', (key,json.dumps(value)))
        # Network sends that were interrupted have an uncertain outcome. Never auto-repeat them.
        if recover:
            self.db.execute("UPDATE outbox SET status='uncertain',error='Ứng dụng dừng giữa lúc gửi. Kiểm tra Telegram trước khi gửi lại.' WHERE status='sending'")
            self.db.execute("UPDATE jobs SET status='pending' WHERE status='running'")
        self.db.commit()

    def execute(self, sql, args=()):
        with self.lock:
            cursor = self.db.execute(sql,args)
            self.db.commit()
            return cursor.lastrowid if cursor.rowcount!=0 else 0

    def rows(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.db.execute(sql,args).fetchall()]

    def one(self, sql, args=()):
        rows = self.rows(sql,args)
        return rows[0] if rows else None

    def get(self, key):
        row = self.one('SELECT value FROM settings WHERE key=?',(key,))
        return json.loads(row['value']) if row else None

    def set(self, **values):
        with self.lock:
            for k,v in values.items():
                self.db.execute('INSERT OR REPLACE INTO settings VALUES(?,?)',(k,json.dumps(v)))
            self.db.commit()

    def secret(self, key, value=None):
        if value is not None:
            self.set(**{key:protect(value) if value else ''})
        encrypted = self.get(key)
        return protect(encrypted,True) if encrypted else ''

    def settings(self):
        return {k:self.get(k) for k in DEFAULTS} | {
            'gateway_key_set':bool(self.get('gateway_key')),
            'telegram_token_set':bool(self.get('telegram_token')),
            'codex_access_key_set':bool(self.get('codex_access_key'))}

    def event(self, kind, message):
        self.execute('INSERT INTO events(created,kind,message) VALUES(?,?,?)',
                     (time.time(),kind,str(message)[:1000]))

    def enqueue(self, kind, payload, dedupe):
        return self.execute('INSERT OR IGNORE INTO jobs(kind,payload,dedupe,created) VALUES(?,?,?,?)',
                            (kind,json.dumps(payload,ensure_ascii=False),dedupe,time.time()))

    def stats(self, date):
        tasks = self.rows('SELECT * FROM assignments WHERE day=? AND sent>0 ORDER BY seq',(date,))
        graded = [t for t in tasks if t['status']=='graded' and t['score'] is not None]
        groups = {}
        for t in graded:
            key = t['category'] + (' · '+t['skill'] if t['skill'] else '')
            groups.setdefault(key,[]).append(t['score'])
        # Compare identical category/skill/difficulty strata, and require 3 independent tasks per side.
        earlier = self.rows('SELECT DISTINCT day FROM assignments WHERE day<? AND score IS NOT NULL ORDER BY day DESC LIMIT 1',(date,))
        growth = None
        comparable = 0
        baseline_day = earlier[0]['day'] if earlier else None
        differences = []
        if baseline_day:
            before = self.rows("SELECT category,skill,level,score FROM assignments WHERE day=? AND status=? AND assistance='no'",(baseline_day,'graded'))
            def strata(items):
                result = {}
                for t in items:
                    result.setdefault((t['category'],t['skill'],round(t['level'],4)),[]).append(t['score'])
                return result
            old, new = strata(before), strata([t for t in graded if t['assistance']=='no'])
            for key, values in new.items():
                if len(values)>=3 and len(old.get(key,[]))>=3:
                    base = sum(old[key])/len(old[key])
                    if base>0:
                        differences.append((sum(values)/len(values)/base-1)*100)
                        comparable += len(values)
            if differences:
                growth = round(sum(differences)/len(differences),1)
        return dict(sent=len(tasks),completed=len(graded),target=24,
            average=round(sum(t['score'] for t in graded)/len(graded),1) if graded else None,
            growth=growth,comparable=comparable,baseline_day=baseline_day,
            growth_note='Ước lượng từ rubric AI cố định; chưa phải phép đo năng lực chuẩn hóa.',
            assisted=sum(t['assistance']=='yes' for t in graded),
            unaided=sum(t['assistance']=='no' for t in graded),
            skills={k:round(sum(v)/len(v),1) for k,v in groups.items()})
