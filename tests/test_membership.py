import base64
import contextlib
import io
import json
import tempfile
import unittest
import shutil
import uuid
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from pypdf import PdfReader

from membership.config import ROOT, Settings
from membership.mail import flush
from membership.security import Problem
from membership.service import CONSENT_VERSION, Service
from membership.web import Application


class MembershipTest(unittest.TestCase):
    def setUp(self):
        # Windows sandbox tokens cannot use CPython's owner-only temporary ACL.
        directory = ROOT.parent / ('test-data-' + uuid.uuid4().hex)
        directory.mkdir()
        self.temp = SimpleNamespace(name=str(directory))
        self.cfg = Settings(data=Path(self.temp.name), fee_minor=5000, currency='KMF')
        self.app = Application(self.cfg)
        self.service = self.app.service
        self.service.add_admin('admin@example.org', 'test-password-private-123')
        self.cookie = self.csrf = ''
        self.login()

    def tearDown(self):
        directory = Path(self.temp.name).resolve()
        self.assertEqual(directory.parent, ROOT.parent.resolve())
        self.assertTrue(directory.name.startswith('test-data-'))
        shutil.rmtree(directory)

    def request(self, path, data=None, authenticated=False, csrf=True, origin=None, method=None, raw=None, content_type='application/json'):
        body = raw if raw is not None else (json.dumps(data).encode() if data is not None else b'')
        path, _, query = path.partition('?')
        env = {'REQUEST_METHOD': method or ('POST' if data is not None or raw is not None else 'GET'), 'PATH_INFO': path,
               'QUERY_STRING': query, 'CONTENT_LENGTH': str(len(body)), 'CONTENT_TYPE': content_type,
               'wsgi.input': io.BytesIO(body), 'REMOTE_ADDR': '127.0.0.1',
               'HTTP_ORIGIN': origin or self.cfg.origin}
        if authenticated:
            env['HTTP_COOKIE'] = self.cookie
            if csrf:
                env['HTTP_X_CSRF_TOKEN'] = self.csrf
        captured = {}
        def start(status, headers):
            captured.update(code=int(status.split()[0]), headers=dict(headers))
        result = b''.join(self.app(env, start))
        captured['raw'] = result
        captured['body'] = json.loads(result) if captured['headers']['Content-Type'].startswith('application/json') else result
        return captured

    def login(self):
        result = self.request('/api/login', {'email': 'admin@example.org', 'password': 'test-password-private-123'})
        self.assertEqual(result['code'], 200)
        self.cookie = result['headers']['Set-Cookie'].split(';')[0]
        self.csrf = result['body']['csrf']

    def payload(self, suffix='one'):
        image = Image.new('RGB', (600, 800), '#b6cbd1')
        raw = io.BytesIO()
        image.save(raw, 'JPEG', exif=b'Exif\x00\x00metadata-to-strip')
        return {'first_name': 'Youssouf', 'last_name': 'Ben Ali ' + suffix, 'email': suffix + '@example.org',
                'phone': '+269 000 00 00', 'profession': 'Profession déclarée privée', 'category': 'actif',
                'motivation': 'Contribuer aux initiatives de biodiversité et de coopération.',
                'consent': True, 'consent_version': CONSENT_VERSION,
                'photo': {'name': 'photo.jpg', 'mime': 'image/jpeg', 'base64': base64.b64encode(raw.getvalue()).decode()}}

    def submit(self, suffix='one'):
        result = self.request('/api/membership/applications', self.payload(suffix))
        self.assertEqual(result['code'], 202, result['body'])
        with contextlib.closing(self.service.connection()) as db:
            return db.execute('SELECT id FROM applications WHERE email=?', (suffix + '@example.org',)).fetchone()[0]

    def test_motivation_required_for_new_public_requests(self):
        for value in (None, '', ' \n\t '):
            payload = self.payload('motivation-required')
            if value is None:
                payload.pop('motivation')
            else:
                payload['motivation'] = value
            self.assertEqual(self.request('/api/membership/applications', payload)['code'], 400)
        with contextlib.closing(self.service.connection()) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM applications').fetchone()[0], 0)

    def action(self, identifier, action, **values):
        member = self.service.detail(identifier)
        return self.request('/api/admin/applications/' + identifier + '/action',
                            {'action': action, 'version': member['version'], **values}, authenticated=True)

    def approve(self, identifier, payment_first=False):
        self.assertEqual(self.action(identifier, 'function', function='Responsable Environnement et Climat')['code'], 200)
        actions = ['payment', 'approve'] if payment_first else ['approve', 'payment']
        for action in actions:
            result = self.action(identifier, action, amount_minor=5000, currency='KMF', reference='Reçu test 001')
            self.assertEqual(result['code'], 200, result['body'])
            if action == actions[0]:
                self.assertIsNone(result['body']['member_number'])
                self.assertIsNone(result['body']['card_path'])
        return self.service.detail(identifier)

    def test_full_workflow_both_orders_pdf_and_audit(self):
        first = self.submit('first')
        self.assertEqual(self.action(first, 'approve')['code'], 409)
        before = self.service.detail(first)
        self.assertIsNone(before['member_number'])
        self.assertFalse(before['function'])
        first = self.approve(first)
        second = self.approve(self.submit('second'), payment_first=True)
        self.assertTrue(first['member_number'].endswith('-001'))
        self.assertTrue(second['member_number'].endswith('-002'))
        self.assertEqual(first['status'], 'carte_generee', first['card_error'])
        self.assertTrue(first['card_url'].startswith('/api/admin/'))
        reader = PdfReader(self.cfg.data / first['card_path'])
        self.assertEqual(len(reader.pages), 2)
        for page in reader.pages:
            self.assertAlmostEqual(float(page.mediabox.width) / 72 * 25.4, 85.60, places=3)
            self.assertAlmostEqual(float(page.mediabox.height) / 72 * 25.4, 53.98, places=3)
        text = '\n'.join(page.extract_text() for page in reader.pages)
        self.assertIn('Responsable Environnement et Climat', text)
        self.assertIn('RÉSEAUX · PARTENARIATS · SOLUTIONS', text)
        self.assertNotIn('Profession déclarée privée', text)
        self.assertIn('Signature du membre (simulée)', text)
        self.assertTrue(any(x['action'] == 'generate' for x in first['history']))
        repeated = self.action(first['id'], 'generate')
        self.assertEqual(repeated['body']['member_number'], first['member_number'])
        self.assertEqual(self.action(first['id'], 'payment', amount_minor=5000, currency='KMF', reference='doublon')['code'], 409)

    def test_public_function_is_never_used_and_duplicates_do_not_create_records(self):
        payload = self.payload()
        payload['function'] = 'Président auto-attribué'
        self.assertEqual(self.request('/api/membership/applications', payload)['code'], 202)
        self.assertEqual(self.request('/api/membership/applications', payload)['code'], 202)
        member = self.service.detail(self.service.list()['items'][0]['id'])
        self.assertEqual(member['function'], '')
        self.assertEqual(self.service.list()['total'], 1)
        self.assertEqual(len(list((self.cfg.data / 'photos').iterdir())), 1)
        with Image.open(self.cfg.data / member['photo_path']) as image:
            self.assertNotIn('exif', image.info)

    def test_access_controls_csrf_origin_private_paths_and_logout(self):
        identifier = self.submit()
        for path in ('/api/admin/applications', '/api/admin/applications/' + identifier,
                     '/api/admin/applications/' + identifier + '/photo', '/api/admin/applications/' + identifier + '/card'):
            self.assertEqual(self.request(path)['code'], 401, path)
        for path in ('/var/members.sqlite3', '/membership/config.py', '/.git/config', '/.env', '/adhesion/assets/../config.py'):
            self.assertEqual(self.request(path)['code'], 404, path)
        action = {'action': 'review', 'version': 1}
        self.assertEqual(self.request('/api/admin/applications/' + identifier + '/action', action, authenticated=True, csrf=False)['code'], 403)
        self.assertEqual(self.request('/api/membership/applications', self.payload('blocked'), origin='https://evil.example')['code'], 403)
        self.assertEqual(self.request('/api/login', raw=b'email=admin', content_type='application/x-www-form-urlencoded')['code'], 415)
        self.assertEqual(self.request('/api/login', {'email': 'admin@example.org', 'password': 'incorrect'})['code'], 401)
        self.assertIn('HttpOnly', self.app.cookie('test')[1])
        self.assertIn('SameSite=Strict', self.app.cookie('test')[1])
        secure = Application(Settings(data=Path(self.temp.name), origin='https://adhesions.example.org', secure_cookies=True))
        self.assertIn('; Secure', secure.cookie('test')[1])
        self.assertEqual(self.request('/api/logout', {}, authenticated=True)['code'], 200)
        self.assertFalse(self.request('/api/session', authenticated=True)['body']['authenticated'])

    def test_bad_upload_consent_json_and_payment_are_rejected(self):
        for modification in ('consent', 'photo', 'category'):
            data = self.payload()
            if modification == 'consent': data['consent'] = False
            if modification == 'photo': data['photo']['base64'] = base64.b64encode(b'<script>bad</script>').decode()
            if modification == 'category': data['category'] = 'admin'
            self.assertEqual(self.request('/api/membership/applications', data)['code'], 400)
        image = self.payload(); image['photo']['name'] = 'attack.jpg.html'
        self.assertEqual(self.request('/api/membership/applications', image)['code'], 400)
        self.assertEqual(self.request('/api/membership/applications', raw=b'{bad')['code'], 400)
        self.assertEqual(self.request('/api/membership/applications', raw=b' ' * (self.cfg.max_body + 1))['code'], 413)
        identifier = self.submit()
        self.assertEqual(self.action(identifier, 'payment', amount_minor=4999, currency='KMF', reference='x')['code'], 400)
        self.assertIsNone(self.service.detail(identifier)['member_number'])
        self.assertIsNone(self.service.detail(identifier)['payment'])

    def test_parallel_numbering_conflicts_and_restart(self):
        identifiers = [self.submit(str(i)) for i in range(6)]
        with contextlib.closing(self.service.connection()) as db:
            actor = db.execute('SELECT id FROM admins').fetchone()[0]
        def issue(identifier):
            for action, values in [('function', {'function': 'Membre actif'}), ('approve', {}), ('payment', {'amount_minor': 5000, 'currency': 'KMF', 'reference': 'R-' + identifier})]:
                row = self.service.detail(identifier)
                self.service.change(identifier, actor, {'action': action, 'version': row['version'], **values})
            return self.service.detail(identifier)['member_number']
        with ThreadPoolExecutor(max_workers=6) as executor:
            numbers = list(executor.map(issue, identifiers))
        self.assertEqual(len(set(numbers)), 6)
        self.assertFalse(any(number is None for number in numbers))
        member = self.service.detail(identifiers[0])
        request = {'action': 'generate', 'version': member['version']}
        self.service.change(member['id'], actor, request)
        with self.assertRaises(Problem) as caught:
            self.service.change(member['id'], actor, request)
        self.assertEqual(caught.exception.status, 409)
        restored = Service(self.cfg)
        self.assertEqual(restored.list()['total'], 6)
        self.assertEqual({x['member_number'] for x in restored.list()['items']}, set(numbers))

    def test_generation_failure_retry_download_revocation_and_mail(self):
        identifier = self.submit()
        with patch('membership.cards.make_card', side_effect=OSError('fixture')):
            member = self.approve(identifier)
        self.assertEqual(member['status'], 'validee')
        self.assertIsNotNone(member['member_number'])
        number = member['member_number']
        self.assertTrue(member['card_error'])
        member = self.action(identifier, 'generate')['body']
        self.assertEqual(member['status'], 'carte_generee', member['card_error'])
        self.assertEqual(member['member_number'], number)
        with contextlib.closing(self.service.connection()) as db:
            data = json.loads(db.execute("SELECT payload FROM outbox WHERE kind='carte'").fetchone()[0])
        token = data['link'].split('#token=')[1]
        self.assertEqual(self.request('/api/card-download', {'token': token})['code'], 200)
        self.assertEqual(self.request('/api/card-download', {'token': 'invalid'})['code'], 404)
        self.assertFalse(flush(self.service)['enabled'])
        sent = []
        self.assertEqual(flush(self.service, sent.append)['sent'], 3)
        self.assertEqual(flush(self.service, sent.append)['sent'], 0)
        self.assertEqual(len(sent), 3)
        self.assertEqual(self.action(identifier, 'refuse', reason='Décision test')['code'], 200)
        self.assertEqual(self.request('/api/card-download', {'token': token})['code'], 404)
        self.assertEqual(self.request('/api/admin/applications/' + identifier + '/card', authenticated=True)['code'], 404)

    def test_existing_site_navigation_and_static_resources(self):
        self.assertEqual(self.request('/')['code'], 200)
        self.assertIn('href="adhesion/"', self.request('/')['raw'].decode())
        for path in ('/adhesion/', '/admin/adhesions/', '/adhesion/carte.html', '/adhesion/confidentialite.html', '/adhesion/assets/logo.png'):
            self.assertEqual(self.request(path)['code'], 200, path)
        self.assertIn('RÉSEAUX · PARTENARIATS · SOLUTIONS', self.request('/adhesion/')['raw'].decode())
        self.assertEqual(self.request('/membre/ANH-2026-001')['code'], 404)
        self.cfg.public_verification = True
        self.assertNotIn('email', self.service.verification('ANH-2026-001'))

    def test_public_build_excludes_private_data_and_keeps_newer_homepage(self):
        from scripts.prepare_public import public_files
        files = {str(path.relative_to(ROOT)).replace('\\', '/') for path in public_files()}
        self.assertIn('assets/accueil-1.webp', files)
        self.assertIn('adhesion/assets/config.js', files)
        self.assertFalse(any(path.startswith(('membership/', 'var/', '.qa/', 'tests/')) or path == '.env' for path in files))
        html = self.request('/')['raw'].decode()
        self.assertIn('id="don"', html)
        self.assertIn('+33 7 45 95 39 60', html)
        self.assertIn('60 traverse Moulin de la Villette', html)
        self.assertNotIn('data:image/', html)
        self.assertEqual((ROOT / 'CNAME').read_text().strip(), 'www.lanatureetlhumain.org')
        for path in ('/assets/logo-officiel.jpg', '/assets/accueil-1.webp', '/assets/accueil-2.webp', '/assets/accueil-3.webp', '/assets/ali-abdallah-youssouf-ben.webp'):
            self.assertEqual(self.request(path)['code'], 200, path)
        for path in ('/adhesion', '/admin/adhesions'):
            response = self.request(path)
            self.assertEqual(response['code'], 301)
            self.assertEqual(response['headers']['Location'], path + '/')
        for path in ('/assets/../membership/web.py', '/assets/private.jpg', '/docs/ADHESION.md'):
            self.assertEqual(self.request(path)['code'], 404)

    def test_local_membership_date_and_configured_validity(self):
        identifier = self.submit('timezone')
        with patch('membership.service.now', return_value='2026-02-28T22:30:00+00:00'):
            member = self.approve(identifier)
        self.assertEqual(member['joined_on'], '2026-03-01')
        self.assertEqual(member['expires_on'], '2027-03-01')

    def test_admin_password_preserves_intentional_spaces(self):
        password = '  phrase de passe longue  '
        self.service.add_admin('spaces@example.org', password)
        self.assertEqual(self.request('/api/login', {'email': 'spaces@example.org', 'password': password})['code'], 200)

    def test_card_text_is_checked_before_number_and_failed_card_can_be_corrected(self):
        payload = self.payload('long-name')
        payload.update(first_name='W' * 80, last_name='W' * 80)
        self.assertEqual(self.request('/api/membership/applications', payload)['code'], 400)
        identifier = self.submit('function-length')
        self.assertEqual(self.action(identifier, 'function', function='W' * 80)['code'], 400)
        self.assertIsNone(self.service.detail(identifier)['member_number'])
        with patch('membership.cards.make_card', side_effect=OSError('fixture')):
            member = self.approve(identifier)
        number = member['member_number']
        corrected = self.action(identifier, 'function', function='Membre actif')
        self.assertEqual(corrected['code'], 200)
        self.assertEqual(corrected['body']['member_number'], number)
        self.assertEqual(corrected['body']['status'], 'carte_generee')
        self.assertEqual(self.action(identifier, 'function', function='Membre')['code'], 409)

    def test_parallel_initial_migrations(self):
        root = self.cfg.data / 'new-install'
        settings = Settings(data=root)
        with ThreadPoolExecutor(max_workers=4) as executor:
            databases = list(executor.map(lambda _: Service(settings).database, range(4)))
        self.assertEqual(len(set(databases)), 1)
        with contextlib.closing(Service(settings).connection()) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM schema_migrations').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
