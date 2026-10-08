"""Save work per exercise; submit and release results atomically for twelve types."""
import json,time,uuid
from collections import Counter
from pathlib import Path
from .curriculum import BATCH_SIZE,SCHEDULE
from .media import MAX_TEXT,MAX_IMAGES,verify_upload

FINAL={'graded','needs_evidence'}


def batch_state(store,cycle=None):
    highest=store.one('SELECT max(seq) AS n FROM assignments WHERE sent>0 AND archived=0')['n'] or 1
    if cycle is None:
        outstanding=store.one("SELECT min((a.seq-1)/12+1) AS cycle FROM assignments a WHERE a.sent>0 AND a.archived=0 AND NOT EXISTS(SELECT 1 FROM batches b WHERE b.cycle=(a.seq-1)/12+1 AND b.status IN ('graded','needs_evidence'))")
        if outstanding['cycle']:cycle=outstanding['cycle']
    cycle=max(1,int(cycle or ((highest-1)//BATCH_SIZE+1)))
    start=(cycle-1)*BATCH_SIZE+1
    rows=store.rows('SELECT a.id,a.seq,a.category,a.skill,a.title,a.sent,a.status,d.text,d.files,d.complete,d.assistance FROM assignments a LEFT JOIN drafts d ON d.assignment_id=a.id WHERE a.seq>=? AND a.seq<? AND a.archived=0 ORDER BY a.seq',(start,start+BATCH_SIZE))
    by_seq={r['seq']:r for r in rows};items=[]
    for seq in range(start,start+BATCH_SIZE):
        category,skill=SCHEDULE[(seq-1)%len(SCHEDULE)]
        row=by_seq.get(seq)
        items.append(dict(slot=seq-start+1,id=row['id'] if row else '',category=category,skill=skill,
            title=row['title'] if row and row['sent'] else 'Chưa đến giờ nhận đề',available=bool(row and row['sent']),
            complete=bool(row and row['complete']),has_draft=bool(row and (row['text'] or json.loads(row['files'] or '[]')))))
    latest=store.one('SELECT * FROM batches WHERE cycle=? ORDER BY created DESC LIMIT 1',(cycle,))
    results=[];finished=0
    if latest:
        submitted=store.rows('SELECT a.id,a.title,a.category,a.skill,s.status,s.evaluation,s.error FROM batch_items b JOIN assignments a ON a.id=b.assignment_id JOIN submissions s ON s.id=b.submission_id WHERE b.batch_id=? ORDER BY a.seq',(latest['id'],))
        finished=sum(r['status'] in FINAL for r in submitted)
        if latest['status'] in FINAL:
            results=[dict(r,evaluation=json.loads(r['evaluation'])) for r in submitted]
    complete=sum(r['available'] and r['complete'] and r['has_draft'] for r in items)
    return {'cycle':cycle,'size':BATCH_SIZE,'items':items,'complete':complete,'available':sum(r['available'] for r in items),
        'can_submit':complete==BATCH_SIZE and not (latest and latest['status'] in ('queued','running','failed')),
        'batch':latest,'graded_count':finished,'results':results,'lesson_set':store.one('SELECT * FROM lesson_sets WHERE cycle=?',(cycle,))}


def save_draft(store,task_id,text,files,complete=False,assistance='unknown'):
    task=store.one('SELECT * FROM assignments WHERE id=?',(task_id,))
    if not task or not task['sent']:raise ValueError('Chỉ lưu bài cho đề đã có trong app.')
    if task.get('archived'):raise ValueError('Đề thuộc lịch cũ, đã được giữ trong lịch sử. Chọn một bộ mới để làm và chấm.')
    cycle=(task['seq']-1)//BATCH_SIZE+1
    if store.one("SELECT id FROM batches WHERE cycle=? AND status IN ('queued','running','failed')",(cycle,)):
        raise ValueError('Bộ bài đã gửi đang chấm hoặc cần thử lại; bản gửi đã được giữ nguyên.')
    if assistance not in ('unknown','yes','no'):raise ValueError('Khai báo tham khảo đáp án chưa hợp lệ.')
    if len(text)>MAX_TEXT or len(files)>MAX_IMAGES:raise ValueError('Bài quá lớn; tối đa 120.000 ký tự và 40 file.')
    for name in files:
        path=Path(name).resolve()
        if not path.is_relative_to((store.root/'uploads').resolve()) or not path.is_file():raise ValueError('File nháp chưa hợp lệ.')
        verify_upload(path)
    if complete and not text.strip() and not files:raise ValueError('Thêm bài làm trước khi đánh dấu hoàn thành.')
    if task.get('answer_viewed') and not task.get('completed'):assistance='yes'
    store.execute('INSERT INTO drafts(assignment_id,text,files,complete,assistance,updated) VALUES(?,?,?,?,?,?) ON CONFLICT(assignment_id) DO UPDATE SET text=excluded.text,files=excluded.files,complete=excluded.complete,assistance=excluded.assistance,updated=excluded.updated',
        (task_id,text,json.dumps(files),bool(complete),assistance,time.time()))
    return batch_state(store,cycle)


def submit_batch(engine,cycle,request_id):
    store=engine.store
    with store.lock:
        existing=store.one('SELECT * FROM batches WHERE id=?',(request_id,))
        if existing:
            if existing['cycle']!=int(cycle):raise ValueError('Mã gửi bộ bài bị trùng.')
            return existing['id']
        state=batch_state(store,cycle)
        if not state['can_submit']:raise ValueError('Cần hoàn thành đủ 12 bài của cùng bộ: 8 nhóm khác + 2 Writing + 2 Speaking. Chưa gửi bài nào đi chấm.')
        tasks=store.rows('SELECT * FROM assignments WHERE seq>=? AND seq<? AND archived=0 ORDER BY seq',((state['cycle']-1)*BATCH_SIZE+1,state['cycle']*BATCH_SIZE+1))
        required=Counter((c,s if c=='IELTS' else '') for c,s in SCHEDULE[:BATCH_SIZE])
        observed=Counter((r['category'],r['skill'] if r['category']=='IELTS' else '') for r in tasks)
        if len(tasks)!=BATCH_SIZE or observed!=required:raise ValueError('Bộ đề chưa đủ các loại yêu cầu.')
        drafts=[]
        for task in tasks:
            draft=store.one('SELECT * FROM drafts WHERE assignment_id=?',(task['id'],))
            files=json.loads(draft['files'])
            for name in files:verify_upload(name)
            drafts.append((task,draft,files))
        now=time.time()
        try:
            store.db.execute('INSERT INTO batches(id,cycle,status,created) VALUES(?,?,?,?)',(request_id,state['cycle'],'queued',now))
            for task,draft,files in drafts:
                sid=uuid.uuid4().hex
                store.db.execute('INSERT INTO submissions(id,assignment_id,created,text,files,status,assistance) VALUES(?,?,?,?,?,?,?)',(sid,task['id'],now,draft['text'],json.dumps(files),'queued',draft['assistance']))
                store.db.execute('INSERT INTO batch_items VALUES(?,?,?)',(request_id,task['id'],sid))
                store.db.execute('INSERT INTO jobs(kind,payload,dedupe,created) VALUES(?,?,?,?)',('grade',json.dumps({'id':sid}),'grade:'+sid,now))
            store.db.commit()
        except Exception:
            store.db.rollback();raise
    store.event('batch','Đã lưu và gửi trọn bộ '+str(state['cycle'])+' · 12 đề. Kết quả mở cùng lúc sau khi chấm hết.')
    engine.wake.set()
    return request_id


def finalize(engine,sid):
    store=engine.store
    item=store.one('SELECT batch_id FROM batch_items WHERE submission_id=?',(sid,))
    if not item:return False
    batch=store.one('SELECT * FROM batches WHERE id=?',(item['batch_id'],))
    if batch['status'] in FINAL:return False
    rows=store.rows('SELECT s.*,a.title,a.seq FROM batch_items b JOIN submissions s ON s.id=b.submission_id JOIN assignments a ON a.id=b.assignment_id WHERE b.batch_id=? ORDER BY a.seq',(batch['id'],))
    if any(r['status'] in ('queued','analyzing') for r in rows):
        store.execute("UPDATE batches SET status='running' WHERE id=?",(batch['id'],));return False
    if any(r['status']=='failed' for r in rows):
        if batch['status']!='failed':
            store.execute("UPDATE batches SET status='failed' WHERE id=?",(batch['id'],))
            store.event('error','Bộ '+str(batch['cycle'])+' chưa chấm xong. Bài đã lưu; bấm Thử lại để tiếp tục các bài lỗi.')
            if store.get('telegram_chat_id'):engine.telegram.queue_text('Bộ '+str(batch['cycle'])+' chưa chấm xong; các bài đã được lưu. Mở Hourly Coach → Thử lại. Kết quả đầy đủ sẽ mở sau khi chấm hết.','batch-error:'+batch['id'])
        return False
    if len(rows)!=BATCH_SIZE or any(not r['evaluation'] for r in rows):return False
    evaluations=[json.loads(r['evaluation']) for r in rows]
    now=time.time();status='graded' if all(e['complete'] for e in evaluations) else 'needs_evidence'
    with store.lock:
        for row,evaluation in zip(rows,evaluations):
            store.db.execute('UPDATE assignments SET status=?,score=?,evaluation=?,completed=?,assistance=? WHERE id=?',
                (row['status'],evaluation['score'],row['evaluation'],now,row['assistance'],row['assignment_id']))
        store.db.execute('UPDATE batches SET status=?,completed=? WHERE id=?',(status,now,batch['id']))
        store.db.commit()
    folder=store.root/'batches';folder.mkdir(exist_ok=True)
    (folder/(batch['id']+'.txt')).write_text('\n\n'.join(engine.evaluation_text({'id':r['assignment_id']},e) for r,e in zip(rows,evaluations)),encoding='utf-8-sig')
    engine.advance_level()
    store.event('batch','Đã chấm xong trọn bộ '+str(batch['cycle'])+' · 12 đề; kết quả đã mở cùng lúc.')
    if store.get('telegram_chat_id'):
        engine.telegram.queue_text('Đã chấm xong bộ '+str(batch['cycle'])+' · 12 đề. Mở Hourly Coach → Bộ bài & chấm để xem tất cả nhận xét, sửa lỗi và điểm.','batch-result:'+batch['id'])
    return True
