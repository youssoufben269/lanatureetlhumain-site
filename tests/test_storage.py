import io
import os
import shutil
import traceback
import unittest
import uuid
from http.client import IncompleteRead
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib import error, request

from membership.config import ROOT
from membership.storage import LocalStorage, StorageError, StorageNotFound, SupabaseStorage


PHOTO = 'photos/' + 'a1' * 16 + '.jpg'
CARD = 'cards/' + 'b2' * 16 + '.pdf'
INVALID_PATHS = (
    '', '../' + PHOTO, '/' + PHOTO, 'photos/../' + CARD, 'photos//' + PHOTO[7:],
    PHOTO.replace('/', '\\'), PHOTO + '\n', PHOTO + '?token=secret', PHOTO + '#fragment',
    'photos/%2e%2e/' + CARD, 'photos/%2f' + PHOTO[7:], 'photos/user/' + PHOTO[7:],
    'public/' + PHOTO[7:], PHOTO.replace('.jpg', '.pdf'), CARD.replace('.pdf', '.jpg'),
    PHOTO.replace('.jpg', '.png'), PHOTO.upper(), 'photos/a.jpg', 'photos/' + 'a' * 33 + '.jpg',
    'photos/' + 'g' * 32 + '.jpg', 'C:/' + PHOTO, PHOTO + ':stream', PHOTO + '\x00',
    None, Path(PHOTO),
)


class LocalStorageTest(unittest.TestCase):
    def setUp(self):
        # Temporary files stay outside the site repository, with Windows-friendly ACLs.
        self.directory = ROOT.parent / ('test-storage-' + uuid.uuid4().hex)
        self.directory.mkdir()
        self.addCleanup(self.remove_directory)
        self.store = LocalStorage(self.directory / 'private')

    def remove_directory(self):
        directory = self.directory.resolve()
        self.assertEqual(directory.parent, ROOT.parent.resolve())
        self.assertRegex(directory.name, r'^test-storage-[0-9a-f]{32}$')
        shutil.rmtree(directory)

    def test_roundtrip_overwrite_delete_and_reopen(self):
        for path in (PHOTO, CARD):
            with self.subTest(path=path):
                self.assertFalse(self.store.exists(path))
                self.assertIsNone(self.store.put(path, b'first\x00\xff'))
                self.assertEqual(self.store.get(path), b'first\x00\xff')
                self.assertTrue(self.store.exists(path))
                self.store.put(path, b'replacement')
                reopened = LocalStorage(self.store.data)
                self.assertEqual(reopened.get(path), b'replacement')
                self.assertIsNone(reopened.delete(path))
                self.assertFalse(self.store.exists(path))
        self.assertFalse(list(self.store.data.rglob('.upload-*')))

    def test_empty_bytes_and_uuid_hex_are_valid(self):
        path = 'photos/' + uuid.uuid4().hex + '.jpg'
        self.store.put(path, b'')
        self.assertTrue(self.store.exists(path))
        self.assertEqual(self.store.get(path), b'')

    def test_missing_get_and_delete_are_typed(self):
        for method in (self.store.get, self.store.delete):
            with self.subTest(method=method.__name__), self.assertRaises(StorageNotFound) as caught:
                method(PHOTO)
            self.assertIsInstance(caught.exception, FileNotFoundError)
            self.assertEqual(str(caught.exception), 'Storage object not found.')

    def test_reject_paths_for_every_operation(self):
        for path in INVALID_PATHS:
            for name in ('put', 'get', 'exists', 'delete'):
                with self.subTest(path=path, method=name), self.assertRaises(ValueError):
                    getattr(self.store, name)(path, b'test') if name == 'put' else getattr(self.store, name)(path)
        self.assertEqual(list(self.store.data.iterdir()), [])

    def test_reject_non_bytes(self):
        for data in ('text', None, bytearray(b'test')):
            with self.subTest(data=data), self.assertRaises(TypeError):
                self.store.put(PHOTO, data)
        self.assertFalse(self.store.exists(PHOTO))

    def test_failed_replace_preserves_old_object_and_removes_temporary(self):
        self.store.put(PHOTO, b'old')
        with patch('membership.storage.Path.replace', side_effect=OSError('private path')):
            with self.assertRaisesRegex(StorageError, '^Storage unavailable\\.$'):
                self.store.put(PHOTO, b'new')
        self.assertEqual(self.store.get(PHOTO), b'old')
        self.assertFalse(list(self.store.data.rglob('.upload-*')))

    def test_io_failures_are_generic_and_exists_does_not_hide_them(self):
        for name, operation in (('get', 'read_bytes'), ('exists', 'stat'), ('delete', 'unlink')):
            with self.subTest(method=name):
                with patch('membership.storage.Path.' + operation, side_effect=PermissionError('private path')):
                    with self.assertRaisesRegex(StorageError, '^Storage unavailable\\.$'):
                        getattr(self.store, name)(PHOTO)

    def test_parent_and_file_symlinks_cannot_escape_or_change_prefix(self):
        outside = self.directory / 'outside'
        outside.mkdir()
        sentinel = outside / PHOTO[7:]
        sentinel.write_bytes(b'keep')
        link = self.store.data / 'photos'
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Creating symlinks requires Windows privileges.')
        try:
            self.assert_blocked_symlink()
        finally:
            link.unlink()
        link.mkdir()
        target = self.store.data / PHOTO
        target.symlink_to(sentinel)
        try:
            self.assert_blocked_symlink()
        finally:
            target.unlink()
        self.assertEqual(sentinel.read_bytes(), b'keep')

    def assert_blocked_symlink(self):
        for name in ('put', 'get', 'exists', 'delete'):
            with self.subTest(method=name), self.assertRaises(StorageError):
                getattr(self.store, name)(PHOTO, b'overwrite') if name == 'put' else getattr(self.store, name)(PHOTO)

    def test_windows_junction_guard(self):
        with patch('membership.storage.Path.is_junction', return_value=True):
            self.assert_blocked_symlink()

    @unittest.skipIf(os.name == 'nt', 'POSIX permission bits only')
    def test_private_permissions(self):
        self.store.put(PHOTO, b'test')
        self.assertEqual(self.store.data.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.store.data / 'photos').stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.store.data / PHOTO).stat().st_mode & 0o777, 0o600)


class SupabaseStorageTest(unittest.TestCase):
    def setUp(self):
        # No real network request, project, bucket or credential in this suite.
        guard = patch('membership.storage.request.build_opener')
        self.builder = guard.start()
        self.addCleanup(guard.stop)
        self.opener = self.builder.return_value
        self.response = MagicMock()
        self.response.status = 200
        self.response.read.return_value = b'object\x00\xff'
        self.opener.open.return_value.__enter__.return_value = self.response
        self.url = 'https://example.supabase.co'
        self.key = 'server-only-test-key'
        self.bucket = 'private-membership'
        self.store = SupabaseStorage(self.url + '/', self.key, self.bucket)
        self.opener.open.assert_not_called()

    def assert_request(self, method, path, prefix='', data=None):
        args, kwargs = self.opener.open.call_args
        req, = args
        self.assertEqual(kwargs, {'timeout': 30})
        self.assertEqual(req.get_method(), method)
        self.assertEqual(req.full_url, self.url + '/storage/v1/object/' + prefix + self.bucket + '/' + path)
        self.assertNotIn(self.key, req.full_url)
        self.assertNotIn('?', req.full_url)
        headers = {key.lower(): value for key, value in req.header_items()}
        self.assertEqual(headers['authorization'], 'Bearer ' + self.key)
        self.assertEqual(headers['apikey'], self.key)
        self.assertEqual(req.data, data)
        self.opener.open.return_value.__exit__.assert_called()
        return headers

    def test_upload_upsert_can_be_repeated_for_both_content_types(self):
        for path, mime in ((PHOTO, 'image/jpeg'), (CARD, 'application/pdf')):
            for _ in range(2):
                with self.subTest(path=path):
                    self.assertIsNone(self.store.put(path, b'upload'))
                    headers = self.assert_request('POST', path, data=b'upload')
                    self.assertEqual(headers['content-type'], mime)
                    self.assertEqual(headers['x-upsert'], 'true')

    def test_private_get(self):
        self.assertEqual(self.store.get(PHOTO), b'object\x00\xff')
        self.assert_request('GET', PHOTO, prefix='authenticated/')

    def test_exists_uses_authenticated_metadata_without_downloading_object(self):
        self.response.read.return_value = b''
        self.assertTrue(self.store.exists(CARD))
        self.assert_request('HEAD', CARD, prefix='info/')

    def test_delete_single_exact_object(self):
        self.assertIsNone(self.store.delete(CARD))
        self.assert_request('DELETE', CARD)

    def http_error(self, code):
        return error.HTTPError(self.url + '/?secret=' + self.key, code,
                               'Authorization: Bearer ' + self.key,
                               {'apikey': self.key}, io.BytesIO(self.key.encode()))

    def test_404_for_every_operation(self):
        for name in ('put', 'get', 'exists', 'delete'):
            with self.subTest(method=name):
                failure = self.http_error(404)
                self.opener.open.side_effect = failure
                if name == 'exists':
                    self.assertFalse(self.store.exists(PHOTO))
                else:
                    with self.assertRaises(StorageNotFound) as caught:
                        getattr(self.store, name)(PHOTO, b'test') if name == 'put' else getattr(self.store, name)(PHOTO)
                    self.assertIsInstance(caught.exception, FileNotFoundError)
                    self.assertEqual(str(caught.exception), 'Storage object not found.')
                self.assertTrue(failure.fp.closed)

    def test_other_http_errors_never_look_like_missing_and_hide_secrets(self):
        for code in (301, 302, 307, 400, 401, 403, 409, 429, 500, 503):
            for name in ('put', 'get', 'exists', 'delete'):
                with self.subTest(code=code, method=name):
                    failure = self.http_error(code)
                    self.opener.open.side_effect = failure
                    with self.assertRaises(StorageError) as caught:
                        getattr(self.store, name)(PHOTO, b'test') if name == 'put' else getattr(self.store, name)(PHOTO)
                    self.assert_generic_failure(caught.exception)
                    self.assertTrue(failure.fp.closed)

    def assert_generic_failure(self, exc):
        self.assertEqual(str(exc), 'Storage unavailable.')
        self.assertNotIsInstance(exc, FileNotFoundError)
        rendered = ''.join(traceback.format_exception(exc))
        for secret in (self.key, self.url, 'Authorization', 'apikey'):
            self.assertNotIn(secret, rendered)

    def test_network_and_read_errors_are_generic(self):
        for failure in (error.URLError(self.key), TimeoutError(self.key), OSError(self.url)):
            with self.subTest(error=type(failure).__name__):
                self.opener.open.side_effect = failure
                with self.assertRaises(StorageError) as caught:
                    self.store.get(PHOTO)
                self.assert_generic_failure(caught.exception)
        self.opener.open.side_effect = None
        for failure in (OSError(self.key), IncompleteRead(self.key.encode())):
            with self.subTest(read_error=type(failure).__name__):
                self.response.read.side_effect = failure
                with self.assertRaises(StorageError) as caught:
                    self.store.get(PHOTO)
                self.assert_generic_failure(caught.exception)

    def test_non_success_response_status_is_not_silently_accepted(self):
        for status in (302, 404, 503):
            with self.subTest(status=status):
                self.response.status = status
                expected = StorageNotFound if status == 404 else StorageError
                with self.assertRaises(expected):
                    self.store.get(PHOTO)

    def test_paths_and_payloads_are_validated_before_network(self):
        for path in INVALID_PATHS:
            for name in ('put', 'get', 'exists', 'delete'):
                with self.subTest(path=path, method=name), self.assertRaises(ValueError):
                    getattr(self.store, name)(path, b'test') if name == 'put' else getattr(self.store, name)(path)
        for data in ('text', None, bytearray(b'test')):
            with self.subTest(data=data), self.assertRaises(TypeError):
                self.store.put(PHOTO, data)
        self.opener.open.assert_not_called()

    def test_invalid_configuration_never_contacts_network(self):
        for url in ('http://example.supabase.co', self.url + '?key=secret', self.url + '#secret',
                    self.url + '/storage/v1', 'https://user:secret@example.supabase.co',
                    'https://example.supabase.co:invalid', self.url + '\n', None):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, '^Invalid storage configuration\\.$'):
                SupabaseStorage(url, self.key, self.bucket)
        for bucket in ('', '../public', 'a/b', 'private?public=true', 'photos%2fcards', None):
            with self.subTest(bucket=bucket), self.assertRaises(ValueError):
                SupabaseStorage(self.url, self.key, bucket)
        for key in ('', 'key\r\ninjection: value', 'key with spaces', None):
            with self.subTest(key=key), self.assertRaises(ValueError):
                SupabaseStorage(self.url, key, self.bucket)
        self.opener.open.assert_not_called()

    def test_redirects_are_disabled_so_credentials_cannot_be_forwarded(self):
        handler, = self.builder.call_args.args
        self.assertIsInstance(handler, request.HTTPRedirectHandler)
        req = request.Request(self.url, headers={'apikey': self.key})
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                self.assertIsNone(handler.redirect_request(req, None, code, 'redirect', {}, 'https://other.invalid'))


if __name__ == '__main__':
    unittest.main()
