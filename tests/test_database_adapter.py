"""Adapter contract tests: no driver installation or network access required."""

import importlib
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, Mock, call, patch

from membership import database


class DatabaseAdapterTest(unittest.TestCase):
    def setUp(self):
        self.raw = MagicMock()
        self.driver = ModuleType('psycopg')
        self.driver.connect = Mock(return_value=self.raw)
        self.conninfo = ModuleType('psycopg.conninfo')
        self.conninfo.conninfo_to_dict = Mock(return_value={'host': 'db.example.org'})
        self.modules = patch.dict(sys.modules, {'psycopg': self.driver, 'psycopg.conninfo': self.conninfo})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        # Deliberately fictitious credentials; never connect to this host.
        self.dsn = 'postgresql://private-user:private-password@db.example.org/database'

    def connect(self):
        result = database.connection(self.dsn)
        self.raw.reset_mock()
        return result

    def test_import_is_lazy(self):
        with patch('importlib.import_module', side_effect=AssertionError('Driver loaded eagerly')):
            importlib.reload(database)
        self.driver.connect.assert_not_called()

    def test_optional_driver_missing(self):
        with patch.dict(sys.modules, {'psycopg': None}):
            with self.assertRaisesRegex(RuntimeError, 'psycopg v3'):
                database.connection(self.dsn)
        self.driver.connect.assert_not_called()

    def test_connection_tls_pooler_and_private_session_settings(self):
        database.connection(self.dsn)
        self.driver.connect.assert_called_once_with(
            self.dsn, autocommit=True, prepare_threshold=None, sslmode='require',
            connect_timeout=30, row_factory=database._row_factory)
        self.assertEqual(self.raw.execute.call_args_list, [
            call('SET search_path TO lnh_private'),
            call("SET lock_timeout = '30s'"),
            call("SET statement_timeout = '60s'")])
        self.assertEqual(self.raw.execute.return_value.close.call_count, 3)

    def test_verified_tls_modes_are_preserved(self):
        for mode in ('require', 'verify-ca', 'verify-full'):
            with self.subTest(mode=mode):
                self.conninfo.conninfo_to_dict.return_value = {'host': 'db.example.org', 'sslmode': mode}
                database.connection(self.dsn)
                self.assertEqual(self.driver.connect.call_args.kwargs['sslmode'], mode)

    def test_external_weak_tls_is_rejected(self):
        for mode in ('disable', 'allow', 'prefer', ''):
            with self.subTest(mode=mode):
                self.conninfo.conninfo_to_dict.return_value = {'host': 'db.example.org', 'sslmode': mode}
                with self.assertRaisesRegex(ValueError, 'sslmode'):
                    database.connection(self.dsn)
        self.driver.connect.assert_not_called()

    def test_disable_is_only_allowed_on_explicit_loopback(self):
        for host in ('localhost', '127.0.0.1', 'localhost,127.0.0.1'):
            with self.subTest(host=host):
                self.conninfo.conninfo_to_dict.return_value = {'host': host, 'sslmode': 'disable'}
                database.connection(self.dsn)
                self.assertEqual(self.driver.connect.call_args.kwargs['sslmode'], 'disable')
        self.driver.connect.reset_mock()
        for parameters in (
            {'sslmode': 'disable'},
            {'host': 'localhost.evil.example', 'sslmode': 'disable'},
            {'host': '127.0.0.1,db.example.org', 'sslmode': 'disable'},
            {'host': 'localhost', 'hostaddr': '192.0.2.1', 'sslmode': 'disable'},
            {'host': '/tmp', 'sslmode': 'disable'},
        ):
            with self.subTest(parameters=parameters):
                self.conninfo.conninfo_to_dict.return_value = parameters
                with self.assertRaises(ValueError):
                    database.connection(self.dsn)
        self.driver.connect.assert_not_called()

    def test_private_dsn_not_disclosed_in_errors(self):
        for target in (self.conninfo.conninfo_to_dict, self.driver.connect):
            with self.subTest(target=target):
                target.side_effect = ValueError(self.dsn)
                with self.assertRaises((ValueError, RuntimeError)) as raised:
                    database.connection(self.dsn)
                self.assertNotIn('private-user', str(raised.exception))
                self.assertNotIn('private-password', str(raised.exception))
                self.assertTrue(raised.exception.__suppress_context__)
                target.side_effect = None

    def test_empty_configuration_never_connects(self):
        for dsn in ('', ' ', None):
            with self.subTest(dsn=dsn), self.assertRaises(ValueError):
                database.connection(dsn)
        self.driver.connect.assert_not_called()

    def test_initialization_failure_closes_connection(self):
        self.raw.execute.side_effect = RuntimeError(self.dsn)
        with self.assertRaisesRegex(RuntimeError, 'Connexion PostgreSQL impossible'):
            database.connection(self.dsn)
        self.raw.close.assert_called_once_with()

    def test_cleanup_failure_does_not_disclose_private_dsn(self):
        self.raw.execute.side_effect = RuntimeError(self.dsn)
        self.raw.close.side_effect = RuntimeError(self.dsn)
        with self.assertRaisesRegex(RuntimeError, 'Connexion PostgreSQL impossible') as raised:
            database.connection(self.dsn)
        self.assertNotIn('private-password', str(raised.exception))
        self.assertTrue(raised.exception.__suppress_context__)

    def test_row_mapping_position_slices_and_values(self):
        factory = database._row_factory(SimpleNamespace(description=[
            SimpleNamespace(name='id'), SimpleNamespace(name='email')]))
        row = factory((17, 'member@example.org'))
        self.assertEqual(row[0], 17)
        self.assertEqual(row[-1], 'member@example.org')
        self.assertEqual(row[:1], (17,))
        self.assertEqual(row['email'], 'member@example.org')
        self.assertEqual(dict(row), {'id': 17, 'email': 'member@example.org'})
        self.assertEqual(tuple(row), (17, 'member@example.org'))
        self.assertEqual(len(row), 2)
        with self.assertRaises(IndexError):
            _ = row['missing']
        self.assertTrue(callable(database._row_factory(SimpleNamespace(description=None))))

    def test_execute_keeps_values_bound_and_cursor_api(self):
        db = self.connect()
        cursor = MagicMock()
        row = database.Row(('id',), (9,))
        cursor.fetchone.side_effect = [row, None]
        cursor.fetchall.return_value = [row]
        cursor.__iter__.return_value = iter([row])
        cursor.rowcount = 1
        self.raw.execute.return_value = cursor
        params = ("' OR 1=1 -- ? %",)
        result = db.execute('SELECT id FROM applications WHERE email=?', params)
        self.raw.execute.assert_called_once_with('SELECT id FROM applications WHERE email=%s', params)
        self.assertIs(result.fetchone(), row)
        self.assertIsNone(result.fetchone())
        self.assertEqual(result.fetchall(), [row])
        self.assertEqual([dict(item) for item in result], [{'id': 9}])
        self.assertEqual(result.rowcount, 1)
        self.raw.commit.assert_not_called()

    def test_qmarks_preserve_quotes_comments_and_percent_literals(self):
        sql = "SELECT '?', 'l''ami ?', \"field?\", ? /* ? /* nested ? */ ? */ -- ?\n WHERE x LIKE '50%' AND y % 2=?"
        expected = "SELECT '?', 'l''ami ?', \"field?\", %s /* ? /* nested ? */ ? */ -- ?\n WHERE x LIKE '50%%' AND y %% 2=%s"
        self.assertEqual(database._parameters(sql), expected)
        db = self.connect()
        db.execute("SELECT '? 50%' -- no parameters")
        self.raw.execute.assert_called_once_with("SELECT '? 50%' -- no parameters")

    def test_begin_immediate_serializes_writers_until_commit(self):
        db = self.connect()
        cursor = db.execute('  begin immediate; ')
        self.assertIs(cursor, self.raw.execute.return_value)
        db.execute('UPDATE sequences SET value=? WHERE year=?', (2, 2026))
        self.assertEqual(self.raw.execute.call_args_list, [
            call('BEGIN'), call('SELECT pg_advisory_xact_lock(%s)', (database.WRITER_LOCK,)),
            call('UPDATE sequences SET value=%s WHERE year=%s', (2, 2026))])
        self.raw.commit.assert_not_called()
        db.commit()
        self.raw.commit.assert_called_once_with()
        db.execute('BEGIN IMMEDIATE')
        db.rollback()
        self.raw.rollback.assert_called_once_with()

    def test_begin_lock_failure_rolls_back_and_allows_retry(self):
        db = self.connect()
        self.raw.execute.side_effect = [MagicMock(), TimeoutError('lock timeout')]
        with self.assertRaises(TimeoutError):
            db.execute('BEGIN IMMEDIATE')
        self.raw.rollback.assert_called_once_with()
        self.raw.execute.side_effect = None
        db.execute('BEGIN IMMEDIATE')

    def test_nested_begin_is_rejected_without_second_lock(self):
        db = self.connect()
        db.execute('BEGIN IMMEDIATE')
        with self.assertRaisesRegex(RuntimeError, 'déjà ouverte'):
            db.execute('BEGIN IMMEDIATE')
        self.assertEqual(self.raw.execute.call_count, 2)

    def test_isolated_write_is_locked_and_committed(self):
        db = self.connect()
        db.execute('INSERT INTO sequences VALUES(?,1)', (2026,))
        self.assertEqual(self.raw.execute.call_args_list, [
            call('BEGIN'), call('SELECT pg_advisory_xact_lock(%s)', (database.WRITER_LOCK,)),
            call('INSERT INTO sequences VALUES(%s,1)', (2026,))])
        self.raw.commit.assert_called_once_with()

    def test_isolated_write_failure_rolls_back(self):
        db = self.connect()
        self.raw.execute.side_effect = [MagicMock(), MagicMock(), ValueError('constraint')]
        with self.assertRaises(ValueError):
            db.execute('UPDATE sequences SET value=?', (0,))
        self.raw.rollback.assert_called_once_with()
        self.raw.commit.assert_not_called()

    def test_explicit_transaction_failure_is_left_for_caller_rollback(self):
        db = self.connect()
        db.execute('BEGIN IMMEDIATE')
        self.raw.execute.side_effect = ValueError('constraint')
        with self.assertRaises(ValueError):
            db.execute('UPDATE sequences SET value=?', (0,))
        self.raw.rollback.assert_not_called()
        db.rollback()
        db.close()
        self.raw.rollback.assert_called_once_with()
        self.raw.close.assert_called_once_with()
        self.raw.commit.assert_not_called()

    def test_migration_preserves_columns_types_and_constraints(self):
        folder = Path(database.__file__).parent / 'migrations'
        sqlite = (folder / '001_initial.sql').read_text(encoding='utf-8')
        postgres = (folder / 'postgres' / '001_initial.sql').read_text(encoding='utf-8')
        # Compare full DDL after only the intentional PostgreSQL differences.
        ddl = postgres.split('-- No browser/API policies:')[0]
        equivalent = ddl.replace('id BIGSERIAL PRIMARY KEY', 'id INTEGER PRIMARY KEY')
        expected = sqlite.replace(' COLLATE NOCASE', '').replace('INSERT INTO schema_migrations VALUES(1);', '')
        self.assertEqual(equivalent.strip(), expected.strip())
        self.assertIn('INSERT INTO schema_migrations VALUES(1);', postgres)
        for table in ('schema_migrations', 'admins', 'sessions', 'applications', 'payments',
                      'sequences', 'audit', 'downloads', 'outbox', 'rate_limits'):
            self.assertIn(f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;', postgres)


if __name__ == '__main__':
    unittest.main()
