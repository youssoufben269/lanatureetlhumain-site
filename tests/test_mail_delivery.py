import contextlib
import json
import os
import shutil
import sqlite3
import threading
import time
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from membership.config import ROOT, Settings
from membership.mail import flush
from membership.security import Problem, digest
from membership.service import Service


class MailDeliveryTest(unittest.TestCase):
    def setUp(self):
        # Use the same Windows-compatible temporary-directory policy as the suite.
        self.directory = ROOT.parent / ('test-mail-' + uuid.uuid4().hex)
        self.directory.mkdir()
        self.addCleanup(self.remove_directory)
        self.service = Service(Settings(data=self.directory, fee_minor=5000, currency='KMF'))
        with self.service.transaction() as db:
            db.execute("INSERT INTO admins VALUES('admin','admin@example.org','unused',1)")
        # Fail closed if a test accidentally takes the real network path.
        for guard in (
            patch.dict(os.environ, {'LNH_SMTP_HOST': '', 'LNH_SMTP_FROM': 'contact@example.org'}),
            patch('membership.mail.smtplib.SMTP', side_effect=AssertionError('SMTP interdit en test')),
            patch('membership.mail.smtplib.SMTP_SSL', side_effect=AssertionError('SMTP interdit en test')),
        ):
            guard.start()
            self.addCleanup(guard.stop)

    def remove_directory(self):
        directory = self.directory.resolve()
        self.assertEqual(directory.parent, ROOT.parent.resolve())
        self.assertTrue(directory.name.startswith('test-mail-'))
        shutil.rmtree(directory)

    def seed(self, kind='carte'):
        identifier, token = uuid.uuid4().hex, uuid.uuid4().hex
        old_expiry = int(time.time()) - 86400
        with self.service.transaction() as db:
            db.execute("""INSERT INTO applications(
                          id,first_name,last_name,email,phone,category,photo_path,
                          consent_at,consent_version,status,created_at,updated_at,
                          approved_at,member_number,joined_on,expires_on,card_path)
                          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                       (identifier, 'Audit', 'Test', identifier + '@example.org', '+269', 'actif',
                        'photos/' + identifier + '.jpg', '2026-11-11', 'test', 'carte_generee',
                        '2026-11-11', '2026-11-11', '2026-11-11', 'ANH-2026-' + identifier,
                        '2026-11-11', '2099-12-31', 'cards/' + identifier + '.pdf'))
            db.execute('INSERT INTO payments VALUES(?,?,?,?,?,?,?)',
                       (identifier, 'manual', 5000, 'KMF', 'receipt', '2026-11-11', 'admin'))
            db.execute('INSERT INTO downloads VALUES(?,?,?)', (digest(token), identifier, old_expiry))
            self.service.enqueue(db, identifier, kind, identifier + '@example.org',
                                 {'number': 'ANH-2026-001',
                                  'link': self.service.cfg.origin + '/adhesion/carte.html#token=' + token})
            notice = db.execute('SELECT id FROM outbox WHERE application_id=?', (identifier,)).fetchone()[0]
        return identifier, token, notice, old_expiry

    def row(self, query, values=()):
        with contextlib.closing(self.service.connection()) as db:
            result = db.execute(query, values).fetchone()
            return dict(result) if result else None

    def refuse(self, identifier):
        member = self.service.detail(identifier)
        return self.service.change(identifier, 'admin',
                                   {'action': 'refuse', 'version': member['version'], 'reason': 'Décision de test'})

    @contextlib.contextmanager
    def after_reservation(self, callback):
        transaction = self.service.transaction
        armed = True

        @contextlib.contextmanager
        def intercepted():
            nonlocal armed
            with transaction() as db:
                yield db
            if armed:
                armed = False
                callback()

        with patch.object(self.service, 'transaction', intercepted):
            yield

    def test_refusal_after_reservation_cancels_validation_and_card(self):
        for kind in ('validation', 'carte'):
            with self.subTest(kind=kind):
                identifier, token, notice, _ = self.seed(kind)

                def cancel():
                    self.assertEqual(self.row('SELECT state FROM outbox WHERE id=?', (notice,))['state'], 'processing')
                    self.refuse(identifier)

                messages = []
                with self.after_reservation(cancel):
                    result = flush(self.service, messages.append)
                self.assertEqual(result, {'enabled': True, 'sent': 1, 'failed': 0})
                self.assertEqual([str(msg['Subject']) for msg in messages], ['Suite à votre demande d’adhésion'])
                self.assertEqual(self.row('SELECT state FROM outbox WHERE id=?', (notice,))['state'], 'cancelled')
                self.assertIsNone(self.row('SELECT * FROM downloads WHERE token_hash=?', (digest(token),)))

    def test_member_status_is_rechecked_even_if_notice_still_processing(self):
        identifier, _, notice, _ = self.seed()

        def change_status():
            with self.service.transaction() as db:
                db.execute("UPDATE applications SET status='refusee' WHERE id=?", (identifier,))

        messages = []
        with self.after_reservation(change_status):
            result = flush(self.service, messages.append)
        self.assertEqual(result['sent'], 0)
        self.assertFalse(messages)
        self.assertEqual(self.row('SELECT state FROM outbox WHERE id=?', (notice,))['state'], 'cancelled')

    def test_delayed_email_renews_existing_token_for_seven_days(self):
        identifier, token, notice, _ = self.seed()
        with self.assertRaises(Problem):
            self.service.download(token)
        dispatched_at = int(time.time())
        messages = []
        with patch('membership.mail.time.time', return_value=dispatched_at):
            result = flush(self.service, messages.append)
        self.assertEqual(result, {'enabled': True, 'sent': 1, 'failed': 0})
        grant = self.row('SELECT * FROM downloads WHERE token_hash=?', (digest(token),))
        self.assertEqual(grant['expires_at'], dispatched_at + 7 * 86400)
        self.assertEqual(self.service.download(token)['id'], identifier)
        self.assertIn('#token=' + token, messages[0].get_content())
        self.assertIn('7 jours à compter de cet envoi', messages[0].get_content())
        self.assertIn('tant que votre adhésion reste active', messages[0].get_content())
        self.assertEqual(self.row('SELECT state,payload FROM outbox WHERE id=?', (notice,)),
                         {'state': 'sent', 'payload': '{}'})

    def test_revoked_token_is_not_recreated_after_reservation(self):
        _, token, notice, _ = self.seed()

        def revoke():
            with self.service.transaction() as db:
                db.execute('DELETE FROM downloads WHERE token_hash=?', (digest(token),))

        messages = []
        with self.after_reservation(revoke):
            result = flush(self.service, messages.append)
        self.assertEqual(result['sent'], 0)
        self.assertFalse(messages)
        self.assertIsNone(self.row('SELECT * FROM downloads WHERE token_hash=?', (digest(token),)))
        self.assertEqual(self.row('SELECT state FROM outbox WHERE id=?', (notice,))['state'], 'cancelled')

    def test_expired_membership_is_not_renewed_by_email(self):
        identifier, token, notice, old_expiry = self.seed()
        with self.service.transaction() as db:
            db.execute("UPDATE applications SET expires_on='2000-01-01' WHERE id=?", (identifier,))
        messages = []
        result = flush(self.service, messages.append)
        self.assertEqual(result['sent'], 0)
        self.assertFalse(messages)
        self.assertEqual(self.row('SELECT expires_at FROM downloads WHERE token_hash=?', (digest(token),))['expires_at'], old_expiry)
        self.assertEqual(self.row('SELECT state FROM outbox WHERE id=?', (notice,))['state'], 'cancelled')

    def test_failed_transport_rolls_back_expiry_and_retry_renews_it(self):
        _, token, notice, old_expiry = self.seed()
        attempted = []
        first_time = int(time.time())

        def fail(msg):
            attempted.append(msg)
            raise OSError('Transport simulé indisponible')

        with patch('membership.mail.time.time', return_value=first_time):
            result = flush(self.service, fail)
        self.assertEqual(result, {'enabled': True, 'sent': 0, 'failed': 1})
        self.assertEqual(self.row('SELECT expires_at FROM downloads WHERE token_hash=?', (digest(token),))['expires_at'], old_expiry)
        pending = self.row('SELECT state,attempts,available_at,payload FROM outbox WHERE id=?', (notice,))
        self.assertEqual((pending['state'], pending['attempts']), ('pending', 1))
        self.assertGreater(pending['available_at'], first_time)
        self.assertIn(token, json.loads(pending['payload'])['link'])
        messages = []
        retry_time = first_time + 86400
        with patch('membership.mail.time.time', return_value=retry_time):
            self.assertEqual(flush(self.service, messages.append)['sent'], 1)
        self.assertEqual(self.row('SELECT expires_at FROM downloads WHERE token_hash=?', (digest(token),))['expires_at'], retry_time + 7 * 86400)
        self.assertEqual(messages[0]['Message-ID'], attempted[0]['Message-ID'])

    def test_stale_worker_does_not_send_a_newer_reservation(self):
        _, _, notice, _ = self.seed()

        def replace_claim():
            with self.service.transaction() as db:
                db.execute('UPDATE outbox SET attempts=attempts+1 WHERE id=?', (notice,))

        messages = []
        with self.after_reservation(replace_claim):
            result = flush(self.service, messages.append)
        self.assertEqual(result['sent'], 0)
        self.assertFalse(messages)
        self.assertEqual(self.row('SELECT state,attempts FROM outbox WHERE id=?', (notice,)),
                         {'state': 'processing', 'attempts': 2})

    def test_refusal_during_engaged_transport_waits_then_revokes_access(self):
        identifier, token, notice, _ = self.seed()
        started = threading.Event()
        messages, futures = [], []

        def concurrent_refusal():
            started.set()
            return self.refuse(identifier)

        with ThreadPoolExecutor(max_workers=1) as executor:
            def transport(msg):
                messages.append(msg)
                if str(msg['Subject']) != 'Votre carte de membre est disponible':
                    return
                futures.append(executor.submit(concurrent_refusal))
                self.assertTrue(started.wait(5))
                # A distinct connection cannot acquire the writer lock while the
                # transport is engaged. Service.change(refuse) must wait too.
                with contextlib.closing(sqlite3.connect(self.service.database, timeout=0, isolation_level=None)) as db:
                    with self.assertRaisesRegex(sqlite3.OperationalError, 'locked'):
                        db.execute('BEGIN IMMEDIATE')
                self.assertFalse(futures[0].done())

            result = flush(self.service, transport)
            self.assertGreaterEqual(result['sent'], 1)
            self.assertEqual(result['failed'], 0)
            self.assertEqual(futures[0].result(timeout=5)['status'], 'refusee')
        self.assertEqual(str(messages[0]['Subject']), 'Votre carte de membre est disponible')
        self.assertEqual(self.row('SELECT state FROM outbox WHERE id=?', (notice,))['state'], 'sent')
        with self.assertRaises(Problem):
            self.service.download(token)

    def test_without_smtp_configuration_no_notice_is_reserved(self):
        _, _, notice, _ = self.seed()
        self.assertEqual(flush(self.service), {'enabled': False, 'sent': 0, 'failed': 0})
        self.assertEqual(self.row('SELECT state,attempts FROM outbox WHERE id=?', (notice,)),
                         {'state': 'pending', 'attempts': 0})


if __name__ == '__main__':
    unittest.main()
