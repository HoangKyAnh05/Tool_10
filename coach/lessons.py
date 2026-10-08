"""Durable hourly bundles: prepare all twelve before publishing any of them."""
import json,time
from collections import Counter
from .curriculum import BATCH_SIZE,SCHEDULE,validate_assignment,assignment_text
from .charts import render_chart
from .store import day_of


def create_set(store,due,source='gateway',seed_key=None):
    with store.lock:
        if seed_key:
            found=store.one('SELECT * FROM lesson_sets WHERE seed_key=?',(seed_key,))
            if found:return found
        highest=store.one('SELECT max(seq) AS n FROM assignments')['n'] or 0
        last=store.one('SELECT max(cycle) AS n FROM lesson_sets')['n'] or 0
        cycle=max((highest+BATCH_SIZE-1)//BATCH_SIZE,last)+1
        store.execute('INSERT INTO lesson_sets(cycle,due,created,source,level,seed_key) VALUES(?,?,?,?,?,?)',
                      (cycle,due,time.time(),source,store.get('level'),seed_key))
        return store.one('SELECT * FROM lesson_sets WHERE cycle=?',(cycle,))


def set_tasks(store,cycle):
    return store.rows('SELECT * FROM assignments WHERE seq>=? AND seq<? AND archived=0 ORDER BY seq',
                      ((cycle-1)*BATCH_SIZE+1,cycle*BATCH_SIZE+1))


def preparation_lead_seconds(store):
    rows=store.rows("SELECT ready_at-preparation_started AS elapsed FROM lesson_sets WHERE source='gateway' AND ready_at>preparation_started AND preparation_started>0 ORDER BY cycle DESC LIMIT 3")
    # Until the first real duration is known, allow the entire hour for twelve requests.
    if not rows:return 3600
    return min(3600,max(1200,int(max(r['elapsed'] for r in rows)*1.25)+120))


def save_exercise(store,cycle,slot,data):
    lesson=store.one('SELECT * FROM lesson_sets WHERE cycle=?',(cycle,))
    if not lesson:raise ValueError('Bộ đề chưa được tạo.')
    seq=(cycle-1)*BATCH_SIZE+slot
    category,skill=SCHEDULE[(seq-1)%len(SCHEDULE)]
    data=validate_assignment(data,category,skill)
    data['category']=category;data['skill']=skill
    if skill=='Writing':
        from .writing_formats import FORMAT_NAMES
        data['task1_format']=data['chart']['type'];data['task1_format_label']=FORMAT_NAMES[data['chart']['type']]
    data.setdefault('source','Đề mới qua API AI đã cấu hình · kiểm tra cấu trúc và trùng nội dung')
    task_id=f'HC-{seq:05d}'
    store.execute('INSERT INTO assignments(id,seq,day,category,skill,level,title,body,status,created) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,body=excluded.body WHERE assignments.sent=0 AND assignments.completed=0',
        (task_id,seq,day_of(lesson['due']),category,skill,lesson['level'],data['title'],json.dumps(data,ensure_ascii=False),'ready',time.time()))
    return task_id


def prepare_assets(engine,cycle):
    store=engine.store;tasks=set_tasks(store,cycle)
    expected=Counter((c,s if c=='IELTS' else '') for c,s in SCHEDULE[:BATCH_SIZE])
    actual=Counter((r['category'],r['skill'] if r['category']=='IELTS' else '') for r in tasks)
    if len(tasks)!=BATCH_SIZE or expected!=actual:raise ValueError('Bộ đề cần 8 nhóm khác, 2 Writing và 2 Speaking.')
    for task in tasks:
        data=validate_assignment(json.loads(task['body']),task['category'],task['skill'])
        folder=store.root/'assignments'/task['id'];folder.mkdir(parents=True,exist_ok=True)
        if data.get('chart'):render_chart(data['chart'],folder)
        (folder/(task['id']+'-de-bai.txt')).write_text(assignment_text(task),encoding='utf-8-sig')
        (folder/(task['id']+'-dap-an-day-du.txt')).write_text(engine.answer_text(task),encoding='utf-8-sig')
    store.execute("UPDATE lesson_sets SET status='ready',error='',ready_at=CASE WHEN ready_at>0 THEN ready_at ELSE ? END WHERE cycle=? AND published=0",(time.time(),cycle))


def publish_set(engine,cycle,now=None,notify=True):
    store=engine.store;now=time.time() if now is None else now
    with store.lock:
        lesson=store.one('SELECT * FROM lesson_sets WHERE cycle=?',(cycle,))
        if not lesson or lesson['status']!='ready' or lesson['published']:return False
        tasks=set_tasks(store,cycle)
        if len(tasks)!=BATCH_SIZE:raise ValueError('Chưa có đủ 12 đề để mở bộ.')
        try:
            store.db.execute("UPDATE assignments SET sent=?,due=?,day=?,status='sent',error='' WHERE seq>=? AND seq<? AND archived=0",(now,now+3600,day_of(now),(cycle-1)*BATCH_SIZE+1,cycle*BATCH_SIZE+1))
            store.db.execute("UPDATE lesson_sets SET status='published',published=?,error='' WHERE cycle=?",(now,cycle))
            store.db.commit()
        except Exception:store.db.rollback();raise
    store.event('sent',f'Bộ {cycle} · Đã mở đủ 12 đề: 8 nhóm khác + 2 Writing + 2 Speaking.')
    if notify and store.get('telegram_chat_id'):
        engine.telegram.queue_text(f'Có bộ đề mới · Bộ {cycle} · đủ 12 đề\n8 nhóm khác + 2 Writing + 2 Speaking.\nMở Hourly Coach trên laptop → Bộ bài & chấm để làm. Không có Listening/Reading.',f'lesson-set:{cycle}')
        store.enqueue('notify',{},f'lesson-set-notify:{cycle}');engine.wake.set()
    return True


def set_summary(store):
    rows=store.rows('SELECT l.*,count(a.id) AS prepared,sum(CASE WHEN a.sent>0 THEN 1 ELSE 0 END) AS available FROM lesson_sets l LEFT JOIN assignments a ON (a.seq-1)/12+1=l.cycle AND a.archived=0 GROUP BY l.cycle ORDER BY l.cycle DESC')
    return rows
