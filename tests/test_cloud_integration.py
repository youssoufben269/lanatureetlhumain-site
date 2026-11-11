import contextlib
import io
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader
from membership.config import ROOT, Settings
from membership.service import Service
from membership.web import Application
import test_membership as fixtures


class MemoryPrivateStorage:
    def __init__(self):
        self.objects = {}

    def put(self, path, data):
        self.objects[path] = data

    def get(self, path):
        if path not in self.objects:
            raise FileNotFoundError()
        return self.objects[path]

    def delete(self, path):
        if path not in self.objects:
            raise FileNotFoundError()
        del self.objects[path]


class CloudIntegrationTest(unittest.TestCase):
    def test_remote_photo_card_retry_restart_and_revocation(self):
        harness = fixtures.MembershipTest(methodName='runTest')
        harness.setUp()
        self.addCleanup(harness.tearDown)
        harness.cfg.storage_backend = 'supabase'
        harness.cfg.supabase_url = 'https://storage.example.org'
        harness.cfg.supabase_service_key = 'fake-key-only-for-test'
        storage = MemoryPrivateStorage()
        with patch('membership.storage.SupabaseStorage', return_value=storage):
            harness.app = Application(harness.cfg)
            harness.service = harness.app.service
            identifier = harness.submit('remote')
            before = harness.service.detail(identifier)
            self.assertIn(before['photo_path'], storage.objects)
            self.assertFalse((harness.cfg.data / before['photo_path']).exists())
            self.assertEqual(harness.request('/api/admin/applications/' + identifier + '/photo')['code'], 401)
            self.assertEqual(harness.request('/api/admin/applications/' + identifier + '/photo', authenticated=True)['code'], 200)
            with patch('membership.cards.make_card', side_effect=OSError('fixture')):
                failed = harness.approve(identifier)
            self.assertEqual(failed['status'], 'validee')
            number = failed['member_number']
            member = harness.action(identifier, 'generate')['body']
            self.assertEqual(member['status'], 'carte_generee', member['card_error'])
            self.assertEqual(member['member_number'], number)
            self.assertFalse((harness.cfg.data / member['card_path']).exists())
            pdf = storage.objects[member['card_path']]
            self.assertEqual(len(PdfReader(io.BytesIO(pdf)).pages), 2)
            self.assertFalse(list(harness.cfg.data.glob('render-*')))
            restarted = Application(harness.cfg)
            self.assertEqual(restarted.service.detail(identifier)['member_number'], number)
            result = harness.request('/api/admin/applications/' + identifier + '/card', authenticated=True)
            self.assertEqual(result['raw'], pdf)
            harness.action(identifier, 'refuse', reason='Test de révocation')
            self.assertEqual(harness.request('/api/admin/applications/' + identifier + '/card', authenticated=True)['code'], 404)

    def test_ephemeral_host_never_falls_back_to_local_private_data(self):
        with self.assertRaises(ValueError):
            Settings(require_remote_storage=True).validate()
        with self.assertRaises(ValueError):
            Settings(database_url='postgresql://user@db.example.org/db', require_remote_storage=True).validate()
        with self.assertRaises(ValueError):
            Settings(database_url='postgresql://user@db.example.org:6543/db').validate()

    def test_first_admin_bootstrap_never_changes_an_existing_account(self):
        directory = ROOT.parent / ('test-bootstrap-' + uuid.uuid4().hex)
        directory.mkdir()
        self.addCleanup(shutil.rmtree, directory)
        service = Service(Settings(data=directory))
        self.assertTrue(service.bootstrap_admin('first@example.org', 'Unique-test-password-123!'))
        self.assertFalse(service.bootstrap_admin('other@example.org', 'Replacement-test-password-123!'))
        with contextlib.closing(service.connection()) as db:
            rows = db.execute('SELECT email FROM admins').fetchall()
        self.assertEqual([row[0] for row in rows], ['first@example.org'])
