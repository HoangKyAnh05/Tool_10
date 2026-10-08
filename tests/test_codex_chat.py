import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_selected_medium_is_sent_to_codex_without_overriding_model(self):
        self.store.set(codex_reasoning_effort='medium')
        chat = SimulatedChat(self.store, 'Complete response')
        result = chat.ask('Keep the configured model', request_id='medium-test-1')
        self.assertEqual(chat.last_turn_params['effort'], 'medium')
        self.assertNotIn('model', chat.last_turn_params)
        self.assertEqual(result['model'], 'configured-chat-model')
        self.assertEqual(result['answer'], 'Complete response')

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
