import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

from coach.store import Store
from coach.codex_chat import CodexChat

spec=importlib.util.spec_from_file_location('desktop_reconnect',Path(__file__).resolve().parents[1]/'RECONNECT-CODEX.py')
reconnect=importlib.util.module_from_spec(spec);spec.loader.exec_module(reconnect)


class OfflineRecoveryTests(unittest.TestCase):
    def test_offline_restart_recovers_saved_work_and_preserves_schedule(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);data=root/'data';store=Store(data)
            CodexChat(store);store.set(active=True,next_due=3600,codex_reasoning_effort='medium')
            jid=store.enqueue('grade',{'id':'saved-submission'},'saved-job')
            store.execute("UPDATE jobs SET status='running' WHERE id=?",(jid,))
            store.execute("INSERT INTO codex_requests(id,status,created) VALUES('interrupted-request','running',1)")
            (data/'session.json').write_text(json.dumps({'pid':10,'token':'test-session'}))
            def start():
                recovered=Store(data,recover=True);recovered.db.close()
                (data/'session.json').write_text(json.dumps({'pid':20,'token':'test-session'}))
            state=Mock(ok=True)
            health=Mock();health.json.return_value={'online':True,'model':'test-model','reasoning_effort':'medium'}
            client=Mock();client.get.side_effect=[state,health];client.post.return_value=Mock(ok=True)
            with patch.object(reconnect,'ROOT',root),patch.object(reconnect,'DATA',data),patch.object(reconnect,'process_alive',side_effect=lambda pid:pid==20),patch.object(reconnect,'start_app',side_effect=start),patch.object(reconnect.subprocess,'run',return_value=Mock(returncode=0)),patch.object(reconnect.requests,'Session',return_value=client),patch.object(reconnect.time,'sleep'):
                proof,_=reconnect.reconnect()
            self.assertTrue(proof['success'])
            self.assertTrue(store.get('active'))
            self.assertEqual(store.get('next_due'),3600)
            self.assertEqual(store.get('reconnect_until'),0)
            self.assertEqual(store.one('SELECT status FROM jobs WHERE id=?',(jid,))['status'],'pending')
            self.assertEqual(store.one('SELECT status FROM codex_requests')['status'],'failed')
            store.db.close()
