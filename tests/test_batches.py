import copy,json,threading,time,unittest
from unittest.mock import patch
from test_coach import Case
from coach.batches import batch_state,save_draft,submit_batch,finalize
from coach.curriculum import SCHEDULE
from coach.server import create_server
from pathlib import Path
import requests


class BatchTests(Case):
    def make_set(self,start=1):
        ids=[]
        for seq in range(start,start+12):
            category,skill=SCHEDULE[(seq-1)%24]
            tid=self.task(seq=seq,category=category,skill=skill)
            save_draft(self.store,tid,'My complete work for '+tid,[],True,'no');ids.append(tid)
        return ids

    def test_each_half_day_has_all_twelve_types(self):
        for schedule in [SCHEDULE[:12],SCHEDULE[12:]]:
            self.assertEqual(len({c for c,s in schedule}),9)
            self.assertEqual({s for c,s in schedule if c=='IELTS'},{'Speaking','Writing','Reading','Listening'})
    def test_incomplete_batch_is_not_partially_submitted(self):
        tid=self.task();save_draft(self.store,tid,'Partial answer',[],True)
        with self.assertRaises(ValueError):submit_batch(self.engine,1,'a'*32)
        self.assertFalse(self.store.rows('SELECT * FROM submissions'))
        self.assertFalse(self.store.rows("SELECT * FROM jobs WHERE kind='grade'"))
    def test_blank_answer_cannot_be_marked_complete(self):
        tid=self.task()
        with self.assertRaises(ValueError):save_draft(self.store,tid,'',[],True)
        save_draft(self.store,tid,'',[],False)
        self.assertEqual(batch_state(self.store,1)['complete'],0)
    def test_batch_submit_is_atomic_and_idempotent(self):
        self.make_set();self.assertTrue(batch_state(self.store,1)['can_submit'])
        submit_batch(self.engine,1,'b'*32);submit_batch(self.engine,1,'b'*32)
        self.assertEqual(len(self.store.rows('SELECT * FROM submissions')),12)
        self.assertEqual(len(self.store.rows("SELECT * FROM jobs WHERE kind='grade'")),12)
        with self.assertRaises(ValueError):submit_batch(self.engine,1,'c'*32)
        with self.assertRaises(ValueError):save_draft(self.store,'HC-00001','Changed',[],True)
    def test_both_cycles_accept_content_skill_variants(self):
        self.make_set(13);submit_batch(self.engine,2,'d'*32)
        self.assertEqual(len(self.store.rows('SELECT * FROM submissions')),12)
    def test_results_released_once_after_all_twelve_and_one_notification(self):
        ids=self.make_set();submit_batch(self.engine,1,'e'*32)
        self.store.set(telegram_chat_id='123')
        submissions=self.store.rows('SELECT * FROM submissions ORDER BY created,id')
        evaluation={'score':80,'complete':True,'observed_points':80,'criteria':[],**{k:'Full feedback' for k in ('summary','corrections','model_answer','next_steps','evidence_limits')}}
        for row in submissions[:-1]:
            self.store.execute("UPDATE submissions SET status='graded',evaluation=? WHERE id=?",(json.dumps(evaluation),row['id']))
            self.assertFalse(finalize(self.engine,row['id']))
        self.assertFalse(batch_state(self.store,1)['results'])
        self.assertTrue(all(r['evaluation'] is None for r in self.store.rows('SELECT evaluation FROM assignments')))
        last=submissions[-1]
        self.store.execute("UPDATE submissions SET status='graded',evaluation=? WHERE id=?",(json.dumps(evaluation),last['id']))
        self.assertTrue(finalize(self.engine,last['id']))
        self.assertEqual(len(batch_state(self.store,1)['results']),12)
        self.assertEqual(len(self.store.rows('SELECT * FROM outbox')),1)
        self.assertFalse(finalize(self.engine,last['id']))
        self.assertEqual(len(self.store.rows('SELECT * FROM outbox')),1)
    def test_grade_does_not_publish_a_partial_batch_result(self):
        self.make_set();submit_batch(self.engine,1,'f'*32)
        row=self.store.one("SELECT s.* FROM submissions s JOIN assignments a ON a.id=s.assignment_id WHERE a.category='Content'")
        body=json.loads(self.store.one('SELECT body FROM assignments WHERE id=?',(row['assignment_id'],))['body'])
        evaluation={'criteria':[dict(r,score=20,feedback='Evidence') for r in body['rubric']],**{k:'Full detailed answer' for k in ('summary','corrections','model_answer','next_steps','evidence_limits')}}
        self.store.set(telegram_chat_id='123')
        with patch.object(self.engine.gateway,'ask',return_value=json.dumps(evaluation)):self.engine.grade(row['id'])
        self.assertEqual(self.store.one('SELECT status FROM submissions WHERE id=?',(row['id'],))['status'],'graded')
        self.assertFalse(self.store.one('SELECT evaluation FROM assignments WHERE id=?',(row['assignment_id'],))['evaluation'])
        self.assertFalse(self.store.rows('SELECT * FROM outbox'))
    def test_next_cycle_draft_can_be_saved_while_earlier_batch_grades(self):
        self.make_set();submit_batch(self.engine,1,'1'*32)
        tid=self.task(seq=13,category='IELTS',skill='Listening')
        save_draft(self.store,tid,'Work on the next set',[],False)
        self.assertTrue(self.store.one('SELECT text FROM drafts WHERE assignment_id=?',(tid,)))
    def test_video_timecoded_frames_are_retained_as_evidence(self):
        tid=self.task(category='Edit',skill='')
        folder=self.root/'uploads'/'video';folder.mkdir(parents=True)
        video=folder/'answer.mp4';video.write_bytes(b'video-fixture')
        image=folder/'frame.png'
        from PIL import Image
        Image.new('RGB',(8,8),'red').save(image)
        sid=self.engine.submit(tid,'Video with context',[str(video)])
        info={'duration_seconds':5,'frames':[{'path':str(image),'time_seconds':2.5}],'has_audio':False,'limits':'Only sampled frames.'}
        body=json.loads(self.store.one('SELECT body FROM assignments WHERE id=?',(tid,))['body'])
        evaluation={'criteria':[dict(r,score=20,feedback='Based on sampled evidence') for r in body['rubric']],**{k:'Full detailed answer' for k in ('summary','corrections','model_answer','next_steps','evidence_limits')}}
        with patch('coach.engine.extract_video',return_value=info),patch.object(self.engine.gateway,'ask',side_effect=['Visible image content',json.dumps(evaluation)]):self.engine.grade(sid)
        evidence=json.loads(self.store.one('SELECT analysis FROM submissions WHERE id=?',(sid,))['analysis'])
        self.assertEqual(evidence['videos'][0]['frame_times'],[2.5])
        self.assertIn('2.5',evidence['images'][0])


class BatchHttpTests(Case):
    make_set=BatchTests.make_set
    def setUp(self):
        super().setUp();self.server,self.token=create_server(self.engine,Path(__file__).parents[1]/'web',port=0)
        threading.Thread(target=self.server.serve_forever,daemon=True).start()
        self.url=f'http://127.0.0.1:{self.server.server_address[1]}'
        self.client=requests.Session();self.client.get(self.url+'/?session='+self.token)
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.client.close();super().tearDown()
    def test_http_incomplete_batch_and_individual_submit_are_blocked(self):
        tid=self.task();headers={'X-Coach-Request':'1'}
        self.assertEqual(self.client.post(self.url+'/api/batch/submit',json={'cycle':1,'request_id':'2'*32},headers=headers).status_code,400)
        self.assertEqual(self.client.post(self.url+'/api/submit',json={'id':tid,'text':'answer'},headers=headers).status_code,400)
        self.assertFalse(self.store.rows('SELECT * FROM submissions'))
    def test_http_draft_and_partial_result_remain_visible_and_hidden_respectively(self):
        self.make_set();submit_batch(self.engine,1,'3'*32)
        row=self.store.one('SELECT * FROM submissions ORDER BY id')
        self.store.execute("UPDATE submissions SET status='graded',evaluation=? WHERE id=?",(json.dumps({'summary':'PRIVATE PARTIAL RESULT'}),row['id']))
        response=self.client.get(self.url+'/api/task?id='+row['assignment_id'])
        self.assertEqual(response.status_code,200)
        self.assertNotIn('PRIVATE PARTIAL RESULT',response.text)
        self.assertTrue(response.json()['draft']['complete'])
        self.assertEqual(self.client.get(self.url+'/api/batch?cycle=1').json()['results'],[])


if __name__=='__main__':unittest.main()
