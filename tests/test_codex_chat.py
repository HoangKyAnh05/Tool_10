import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

import requests

from coach.store import Store
from coach.engine import Engine
from coach.server import create_server
from coach.codex_chat import CodexChat, ChatError


class SimulatedChat(CodexChat):
    def __init__(self, store, answer='', status='completed'):
        super().__init__(store)
        self.answer = answer
        self.status = status
        self.started_turns = 0

    def _connect(self):
        self.bound_thread = 'simulated-thread'
        self.bound_effort = self.store.get('codex_reasoning_effort') or ''
        self.info = {'model': 'configured-chat-model'}

    def _call(self, method, params, timeout=45):
        if method != 'turn/start':
            return {}
        self.last_turn_params = params
        self.started_turns += 1
        for message in [
            {'method': 'item/completed', 'params': {'threadId': 'simulated-thread', 'turnId': 'test-turn',
                'item': {'id': 'comment', 'type': 'agentMessage', 'phase': 'commentary', 'text': 'INTERNAL PROGRESS'}}},
            {'method': 'item/completed', 'params': {'threadId': 'simulated-thread', 'turnId': 'test-turn',
                'item': {'id': 'final', 'type': 'agentMessage', 'phase': 'final_answer', 'text': self.answer}}},
            {'method': 'turn/completed', 'params': {'threadId': 'simulated-thread',
                'turn': {'id': 'test-turn', 'status': self.status}}},
        ]:
            self.events.put(message)
        return {'turn': {'id': 'test-turn'}}


class ChatTransportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.directory.name))

    def tearDown(self):
        self.store.db.close()
        self.directory.cleanup()

    def test_account_file_change_restarts_connection_and_preserves_medium(self):
        self.store.set(codex_thread_id='private-test-thread',codex_reasoning_effort='medium')
        chat=CodexChat(self.store)
        old=Mock();old.poll.return_value=None
        chat.process=old;chat.bound_thread='private-test-thread';chat.bound_effort='medium';chat.auth_stamp=(1,2,3)
        with patch.object(chat,'_auth_stamp',return_value=(1,2,3)),patch('coach.codex_chat.subprocess.Popen') as spawn:
            chat._connect();spawn.assert_not_called()
        new=Mock();new.poll.return_value=None
        responses=[{}, {'account':{'type':'chatgpt'}}, {'modelProvider':'openai','model':'test-model','reasoningEffort':'medium','thread':{'status':{'type':'idle'}}}]
        with patch.object(chat,'_auth_stamp',return_value=(4,2,5)),patch('coach.codex_chat.shutil.which',return_value='codex'),patch('coach.codex_chat.subprocess.Popen',return_value=new) as spawn,patch('coach.codex_chat.threading.Thread'),patch.object(chat,'_send'),patch.object(chat,'_call',side_effect=responses) as rpc:
            chat._connect()
            old.terminate.assert_called_once();spawn.assert_called_once()
            self.assertEqual(chat.auth_stamp,(4,2,5))
            self.assertEqual(rpc.call_args_list[-1].args[1]['config']['model_reasoning_effort'],'medium')
            self.assertEqual(chat.info['auth_type'],'chatgpt')
        chat.close()

    def test_selected_medium_is_sent_to_codex_without_overriding_model(self):
        self.store.set(codex_reasoning_effort='medium')
        chat = SimulatedChat(self.store, 'Complete response')
        result = chat.ask('Keep the configured model', request_id='medium-test-1')
        self.assertEqual(chat.last_turn_params['effort'], 'medium')
        self.assertNotIn('model', chat.last_turn_params)
        self.assertEqual(result['model'], 'configured-chat-model')
        self.assertEqual(result['answer'], 'Complete response')

    def test_managed_chat_writer_conflict_forks_once_and_remembers_medium(self):
        self.store.set(codex_thread_id='managed-test-thread',codex_seed_thread_id='seed-test-thread',codex_reasoning_effort='medium')
        chat=CodexChat(self.store);process=Mock();process.poll.return_value=None
        replies=[{}, {'account':{'type':'chatgpt'}}, ChatError('thread managed-test-thread already has an active writer'),
                 {'modelProvider':'openai','model':'test-model','reasoningEffort':'medium','thread':{'id':'forked-test-thread','status':{'type':'idle'}}}, {}]
        with patch('coach.codex_chat.shutil.which',return_value='codex'),patch('coach.codex_chat.subprocess.Popen',return_value=process),patch('coach.codex_chat.threading.Thread'),patch.object(chat,'_send'),patch.object(chat,'_call',side_effect=replies) as rpc:
            chat._connect()
            self.assertEqual(self.store.get('codex_thread_id'),'forked-test-thread')
            self.assertEqual(chat.bound_thread,'forked-test-thread')
            fork=next(c for c in rpc.call_args_list if c.args[0]=='thread/fork')
            self.assertEqual(fork.args[1]['threadId'],'managed-test-thread')
            self.assertEqual(fork.args[1]['config']['model_reasoning_effort'],'medium')
            chat._connect()
            self.assertEqual(sum(c.args[0]=='thread/fork' for c in rpc.call_args_list),1)
        chat.close()

    def test_queued_generation_and_grading_are_served_in_arrival_order(self):
        chat=SimulatedChat(self.store,'Complete answer');entered=threading.Event();release=threading.Event()
        starts=[];results=[];original=chat._call
        def call(method,params,timeout=45):
            if method=='turn/start':
                starts.append(params['input'][0]['text'])
                if len(starts)==1:entered.set();release.wait(3)
            return original(method,params,timeout)
        chat._call=call
        def ask(prompt):
            try:results.append(chat.ask(prompt,request_id='queued-'+prompt)['answer'])
            except Exception as e:results.append(str(e))
        threads=[threading.Thread(target=ask,args=(p,)) for p in ('generation','grading','next-generation')]
        try:
            threads[0].start();self.assertTrue(entered.wait(2))
            self.assertTrue(chat.health()['busy'])
            for count,thread in enumerate(threads[1:],2):
                thread.start();deadline=time.monotonic()+2
                while len(chat.request_order)<count and time.monotonic()<deadline:time.sleep(.001)
                self.assertEqual(len(chat.request_order),count)
        finally:
            release.set()
            for thread in threads:
                if thread.ident:thread.join(3)
        self.assertEqual(starts,['generation','grading','next-generation'])
        self.assertEqual(results,['Complete answer']*3)

    def test_preserves_long_unicode_answer_and_excludes_progress(self):
        answer = ('Đây là lời giải đầy đủ — câu ①, không bị cắt.\n' * 3000) + 'DÒNG CUỐI'
        chat = SimulatedChat(self.store, answer)
        result = chat.ask('Nội dung bài', request_id='long-request-1')
        self.assertEqual(result['answer'], answer)
        self.assertEqual(self.store.one('SELECT answer FROM codex_requests')['answer'], answer)
        self.assertNotIn('INTERNAL PROGRESS', result['answer'])

    def test_idempotent_request_does_not_send_second_turn(self):
        chat = SimulatedChat(self.store, 'Kết quả')
        chat.ask('A', request_id='stable-request')
        result = chat.ask('A', request_id='stable-request')
        self.assertTrue(result['cached'])
        self.assertEqual(chat.started_turns, 1)
        with self.assertRaises(ChatError) as error:
            chat.ask('B', request_id='stable-request')
        self.assertEqual(error.exception.status, 409)

    def test_empty_and_interrupted_answers_are_failures(self):
        for index, (answer, status) in enumerate([('', 'completed'), ('Partial text', 'interrupted')]):
            chat = SimulatedChat(self.store, answer, status)
            with self.assertRaises(ChatError):
                chat.ask('A', request_id='failed-request-' + str(index))
            saved = self.store.one('SELECT * FROM codex_requests WHERE id=?', ('failed-request-' + str(index),))
            self.assertEqual(saved['status'], 'failed')
            self.assertIsNone(saved['answer'])

    def test_exit_unblocks_active_request_and_preserves_failure_for_retry(self):
        chat=SimulatedChat(self.store,'Unfinished answer');entered=threading.Event();released=threading.Event()
        process=Mock();process.poll.side_effect=[None,0,0];process.terminate.side_effect=released.set
        chat.process=process;errors=[]
        def next_message(deadline):
            entered.set();released.wait(3);raise ChatError('Application shutdown')
        chat._next=next_message
        def ask():
            try:chat.ask('Long generation',request_id='shutdown-request')
            except ChatError as error:errors.append(str(error))
        thread=threading.Thread(target=ask);thread.start()
        self.assertTrue(entered.wait(2));begin=time.monotonic();chat.close(force=True);thread.join(2)
        self.assertLess(time.monotonic()-begin,1)
        self.assertFalse(thread.is_alive());self.assertTrue(errors)
        saved=self.store.one("SELECT status,answer FROM codex_requests WHERE id='shutdown-request'")
        self.assertEqual(saved['status'],'failed');self.assertIsNone(saved['answer'])
        self.assertEqual(chat.request_order,[])

    def test_settings_never_expose_custom_key(self):
        self.store.secret('codex_access_key', 'a-private-custom-key')
        settings = self.store.settings()
        self.assertTrue(settings['codex_access_key_set'])
        self.assertNotIn('a-private-custom-key', json.dumps(settings))

    def test_http_requires_exact_key_and_returns_full_answer(self):
        engine = Engine(self.store)
        self.store.secret('codex_access_key', 'a-private-custom-key')
        answer = 'Tiếng Việt đầy đủ.\n' * 5000
        server, _ = create_server(engine, Path(__file__).parents[1] / 'web', port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = 'http://127.0.0.1:' + str(server.server_port) + '/ask'
        try:
            with patch.object(engine.gateway.codex, 'ask', return_value={'answer': answer}) as ask:
                for headers in [{}, {'Authorization': 'Bearer sk-fake-key'}, {'Authorization': 'Bearer a-private-custom-key-x'}]:
                    self.assertEqual(requests.post(url, json={'prompt': 'A'}, headers=headers).status_code, 401)
                ask.assert_not_called()
                good = requests.post(url, json={'prompt': 'A'}, headers={'Authorization': 'Bearer a-private-custom-key'})
                self.assertEqual(good.status_code, 200)
                self.assertEqual(good.json()['answer'], answer)
                self.assertIsNotNone(ask.call_args.kwargs['request_id'])
                denied = requests.post(url, json={'prompt': 'A'}, headers={
                    'Authorization': 'Bearer a-private-custom-key', 'Origin': 'https://untrusted.example'})
                self.assertEqual(denied.status_code, 403)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    unittest.main()
