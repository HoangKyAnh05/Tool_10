import copy,json,time,unittest
from unittest.mock import patch
from test_coach import Case
from coach.curriculum import SCHEDULE,validate_assignment
from coach.lessons import create_set,set_tasks,prepare_assets,publish_set,preparation_lead_seconds
from coach.practice_bank import bank_set,install_bank
from coach.novelty import fingerprint,validate_novelty
from coach.batches import batch_state,save_draft,submit_batch
from coach.charts import FORMAT_TYPES,render_chart,validate_chart
from coach.writing_formats import expected_format,validate_format


class BundleTests(Case):
    def configure(self):self.store.set(active=True,approved=True,ai_provider='codex_chat',codex_thread_id='test-thread',next_due=1000)
    def test_prepares_twelve_then_publishes_atomically_at_hour(self):
        self.configure();self.assertTrue(self.engine.prepare_once(900))
        data=bank_set(0)
        with patch.object(self.engine.gateway,'ask',side_effect=[json.dumps(d) for d in data]),patch('coach.engine.time.time',return_value=900):
            self.assertTrue(self.engine.generate_set(1))
        self.assertEqual(len(set_tasks(self.store,1)),12)
        self.store.execute('UPDATE lesson_sets SET preparation_started=800,ready_at=900 WHERE cycle=1')
        self.assertEqual(batch_state(self.store,1)['available'],0)
        self.assertFalse(self.engine.schedule_once(999))
        self.assertTrue(self.engine.schedule_once(1000))
        self.assertEqual(batch_state(self.store,1)['available'],12)
        self.assertEqual({r['sent'] for r in set_tasks(self.store,1)},{1000})
        self.assertEqual(self.store.get('next_due'),3600)
        self.assertEqual(self.store.one('SELECT count(*) AS n FROM lesson_sets')['n'],1)
        self.assertFalse(self.engine.prepare_once(2399))
        self.assertTrue(self.engine.prepare_once(2400))
        self.assertFalse(self.engine.schedule_once(1001))
    def test_preparation_adapts_to_real_duration_and_force_bypasses_window(self):
        self.configure();self.store.set(next_due=10000)
        self.assertEqual(preparation_lead_seconds(self.store),3600)
        prior=create_set(self.store,5000)
        self.store.execute("UPDATE lesson_sets SET preparation_started=1000,ready_at=2800,published=5000,status='published' WHERE cycle=?",(prior['cycle'],))
        self.assertEqual(preparation_lead_seconds(self.store),2370)
        self.assertFalse(self.engine.prepare_once(7629))
        self.assertTrue(self.engine.prepare_once(7630))
        self.assertFalse(self.engine.prepare_once(7631))
        self.store.execute('DELETE FROM lesson_sets WHERE published=0')
        self.assertTrue(self.engine.prepare_once(6000,force=True))
    def test_missing_one_exercise_never_opens_partial_set(self):
        self.configure();self.engine.prepare_once(900)
        data=bank_set(0)
        with patch.object(self.engine.gateway,'ask',side_effect=[json.dumps(data[0]),RuntimeError('temporary failure')]),patch('coach.engine.time.time',return_value=900):
            with self.assertRaises(RuntimeError):self.engine.generate_set(1)
        self.assertEqual(len(set_tasks(self.store,1)),1)
        self.assertEqual(batch_state(self.store,1)['available'],0)
        self.assertFalse(self.engine.schedule_once(1000))
        with patch.object(self.engine.gateway,'ask',side_effect=[json.dumps(d) for d in data[1:]]) as api,patch('coach.engine.time.time',return_value=1001):
            self.engine.generate_set(1)
        self.assertEqual(api.call_count,11)
        self.assertEqual(batch_state(self.store,1)['available'],12)
    def test_pause_does_not_start_new_requests_and_can_resume(self):
        self.configure();self.engine.prepare_once(900);self.store.set(active=False)
        with patch.object(self.engine.gateway,'ask') as api:self.assertFalse(self.engine.generate_set(1))
        api.assert_not_called();self.assertFalse(self.engine.schedule_once(1001))
        with patch('coach.engine.time.time',return_value=1500):self.engine.activate()
        self.assertEqual(self.store.one('SELECT count(*) AS n FROM lesson_sets')['n'],1)
        self.assertEqual(self.store.get('next_due'),3600)
    def test_one_notification_for_whole_bundle(self):
        self.configure();self.store.set(telegram_chat_id='123');self.engine.prepare_once(900)
        with patch.object(self.engine.gateway,'ask',side_effect=[json.dumps(d) for d in bank_set(0)]),patch('coach.engine.time.time',return_value=900):self.engine.generate_set(1)
        self.engine.schedule_once(1000)
        self.assertEqual(len(self.store.rows('SELECT * FROM outbox')),1)
        self.assertIn('12',self.store.one('SELECT payload FROM outbox')['payload'])
    def test_old_listening_is_archived_without_erasing_work(self):
        tid=self.task(skill='Listening');self.store.execute("DELETE FROM settings WHERE key='curriculum_version'")
        self.store.execute('INSERT INTO drafts(assignment_id,text) VALUES(?,?)',(tid,'Saved old work'))
        self.store.db.close()
        from coach.store import Store
        self.store=Store(self.root);self.engine.store=self.store
        self.assertEqual(self.store.one('SELECT archived FROM assignments')['archived'],1)
        self.assertEqual(self.store.one('SELECT text FROM drafts')['text'],'Saved old work')
        self.assertEqual(batch_state(self.store)['available'],0)


class BankTests(Case):
    def test_writing_rotates_every_format_and_renders_each_visual(self):
        writings=[d for i in range(10) for d in bank_set(i) if d['skill']=='Writing']
        kinds=[d['chart']['type'] for d in writings]
        self.assertEqual(set(kinds),set(FORMAT_TYPES))
        self.assertTrue(all(a!=b for a,b in zip(kinds,kinds[1:])))
        for i,d in enumerate(writings):
            validate_format(d,FORMAT_TYPES[i%len(FORMAT_TYPES)])
            self.assertTrue(render_chart(d['chart'],self.root/'format-test').is_file())
        invalid=copy.deepcopy(writings[2]['chart']);invalid['series'][0]['values'][0]+=1
        with self.assertRaises(ValueError):validate_chart(invalid)
        invalid=copy.deepcopy(writings[5]['chart']);invalid['layouts'][0]['features'][0]['x']=99
        with self.assertRaises(ValueError):validate_chart(invalid)

    def test_120_complete_questions_are_distinct_and_only_selected_skills(self):
        all_data=[d for i in range(10) for d in bank_set(i)]
        self.assertEqual(len(all_data),120)
        self.assertEqual(len({d['title'] for d in all_data}),120)
        self.assertEqual(len({fingerprint(d) for d in all_data}),120)
        writing=[d for d in all_data if d['skill']=='Writing'];speaking=[d for d in all_data if d['skill']=='Speaking']
        self.assertEqual(len(writing),20);self.assertEqual(len(speaking),20)
        self.assertEqual(len({d['writing_tasks'][1] for d in writing}),20)
        self.assertEqual(len({d['speaking_tasks']['part2']['cue_card'] for d in speaking}),20)
        for d in writing:
            self.assertGreaterEqual(len(d['writing_model_answers'][0].split()),150)
            self.assertGreaterEqual(len(d['writing_model_answers'][1].split()),250)
        for d in speaking:self.assertGreaterEqual(len(d['answer_key'].split()),1000)
        self.assertEqual({d['skill'] for d in all_data if d['category']=='IELTS'},{'Writing','Speaking'})
    def test_install_preserves_real_statistics_and_is_idempotent(self):
        cycles=install_bank(self.engine)
        self.assertEqual(len(cycles),10)
        self.assertEqual(self.store.one('SELECT count(*) AS n FROM assignments')['n'],120)
        for c in cycles:
            self.assertEqual(batch_state(self.store,c)['available'],12)
            self.assertEqual(batch_state(self.store,c)['complete'],0)
        self.assertFalse(self.store.rows('SELECT * FROM submissions'))
        self.assertTrue(all(r['score'] is None for r in set_tasks(self.store,cycles[0])))
        install_bank(self.engine)
        self.assertEqual(self.store.one('SELECT count(*) AS n FROM assignments')['n'],120)
    def test_renaming_existing_question_is_rejected(self):
        tid=self.task();old=json.loads(self.store.one('SELECT body FROM assignments')['body'])
        old['title']='A new title for an old task'
        with self.assertRaises(ValueError):validate_novelty(self.store,old,'IELTS','Writing')
    def test_non_ielts_skill_label_change_does_not_bypass_duplicate_check(self):
        old=bank_set(0)[3];tid=self.task(category='Content',skill='Short-form')
        self.store.execute('UPDATE assignments SET body=? WHERE id=?',(json.dumps(old),tid))
        same=copy.deepcopy(old);same['title']='Renamed story';same['skill']='Storytelling'
        with self.assertRaises(ValueError):validate_novelty(self.store,same,'Content','Storytelling')
    def test_same_speaking_cue_or_writing_question_is_rejected(self):
        data=bank_set(0);tid=self.task(skill='Speaking')
        self.store.execute('UPDATE assignments SET body=? WHERE id=?',(json.dumps(data[1]),tid))
        same=copy.deepcopy(bank_set(1)[1]);same['speaking_tasks']['part2']['cue_card']=data[1]['speaking_tasks']['part2']['cue_card']
        with self.assertRaises(ValueError):validate_novelty(self.store,same,'IELTS','Speaking')
        wid=self.task(seq=2,skill='Writing')
        self.store.execute('UPDATE assignments SET body=? WHERE id=?',(json.dumps(data[0]),wid))
        same=copy.deepcopy(bank_set(1)[0]);same['writing_tasks'][1]=data[0]['writing_tasks'][1]
        with self.assertRaises(ValueError):validate_novelty(self.store,same,'IELTS','Writing')

if __name__=='__main__':unittest.main()
