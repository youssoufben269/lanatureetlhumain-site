import json
import contextlib
import unittest
from membership.config import ROOT
from scripts.prepare_public import public_files
import test_membership as fixtures


class EmailMembershipTest(unittest.TestCase):
    def setUp(self):
        self.harness = fixtures.MembershipTest(methodName='runTest')
        self.harness.setUp()
        self.addCleanup(self.harness.tearDown)

    def envelope(self):
        data = self.harness.payload('email-import')
        data['function'] = 'Président auto-attribué'
        return {'format':'lnh-membership-request','version':1,'application':data}

    def test_legacy_import_without_motivation_remains_readable(self):
        value = self.envelope()
        value['application'].pop('motivation')
        result = self.harness.request('/api/admin/applications/import', {'request':value}, authenticated=True)
        self.assertEqual(result['code'], 200)
        self.assertEqual(result['body']['motivation'], '')
        self.assertIsNone(result['body']['member_number'])

    def test_private_import_validation_duplicate_photo_and_card_gates(self):
        h = self.harness
        request = {'request':self.envelope()}
        path = '/api/admin/applications/import'
        self.assertEqual(h.request(path, request)['code'], 401)
        self.assertEqual(h.request(path, request, authenticated=True, csrf=False)['code'], 403)
        imported = h.request(path, request, authenticated=True)
        self.assertEqual(imported['code'], 200, imported['body'])
        member = imported['body']
        self.assertEqual(member['function'], '')
        self.assertIsNone(member['member_number'])
        self.assertIsNone(member['card_path'])
        self.assertEqual(member['history'][0]['action'], 'import_email')
        self.assertNotEqual(member['history'][0]['actor'], 'public')
        self.assertEqual(h.request('/api/admin/applications/' + member['id'] + '/photo', authenticated=True)['code'], 200)
        second = h.request(path, request, authenticated=True)
        self.assertEqual(second['body']['id'], member['id'])
        self.assertEqual(h.service.list()['total'], 1)
        self.assertEqual(len(list((h.cfg.data / 'photos').iterdir())), 1)
        self.assertEqual(h.action(member['id'], 'generate')['code'], 409)
        self.assertEqual(h.approve(member['id'])['status'], 'carte_generee')

    def test_import_rejects_incompatible_file_consent_and_upload(self):
        h = self.harness
        for value in ({}, {'format':'wrong','version':1,'application':{}}, {'format':'lnh-membership-request','version':True,'application':{}}):
            self.assertEqual(h.request('/api/admin/applications/import', {'request':value}, authenticated=True)['code'], 400)
        for field in ('consent','photo','email'):
            value = self.envelope()
            if field == 'consent': value['application']['consent'] = False
            elif field == 'email': value['application']['email'] = ''
            else: value['application']['photo']['base64'] = 'not-base64'
            self.assertEqual(h.request('/api/admin/applications/import', {'request':value}, authenticated=True)['code'], 400)
        self.assertEqual(h.service.list()['total'], 0)

    def test_public_artifact_is_email_only_and_has_the_named_recipient(self):
        paths = {p.relative_to(ROOT).as_posix() for p in public_files()}
        self.assertIn('adhesion/settings.json', paths)
        self.assertIn('adhesion/assets/email.js', paths)
        self.assertFalse(any(p.startswith(('admin/','membership/','var/','tests/')) for p in paths))
        self.assertNotIn('adhesion/carte.html', paths)
        self.assertNotIn('adhesion/assets/admin.js', paths)
        self.assertNotIn('adhesion/assets/card.js', paths)
        self.assertNotIn('adhesion/assets/pdf.mjs', paths)
        settings = json.loads((ROOT / 'adhesion/settings.json').read_text())
        self.assertEqual(settings['emailRecipient'], 'lanaturetlhumain@gmail.com')
        self.assertIn('adhesion/assets/direct.js', paths)
        self.assertFalse(any(p.startswith('google-apps-script/') for p in paths))

    def test_google_consent_import_keeps_actual_version_and_legacy_compatibility(self):
        h = self.harness
        value = self.envelope()
        value['application']['consent_version'] = '2026-11-11-v2'
        imported = h.request('/api/admin/applications/import', {'request':value}, authenticated=True)
        self.assertEqual(imported['code'], 200)
        with contextlib.closing(h.service.connection()) as db:
            row = db.execute('SELECT consent_version FROM applications WHERE id=?', (imported['body']['id'],)).fetchone()
        self.assertEqual(row['consent_version'], '2026-11-11-v2')
