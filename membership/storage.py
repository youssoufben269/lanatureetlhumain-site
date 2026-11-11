"""Private photo/card storage; configuration and access control belong to callers.

Supabase expects a project HTTPS origin and an existing private bucket. No bucket
is created or made public. Keep its service key exclusively on the server.
REST reference: https://supabase.com/docs/reference/self-hosting-storage
"""

import os
import re
import stat
import uuid
from http.client import HTTPException
from pathlib import Path
from urllib import error, request
from urllib.parse import urlsplit


class StorageError(OSError):
    """Storage failure with a message safe to expose to application logs."""


class StorageNotFound(FileNotFoundError):
    """The requested object does not exist."""


def _validate_path(path: str) -> None:
    if not isinstance(path, str) or not re.fullmatch(
        r'(?:photos/[0-9a-f]{32}\.jpg|cards/[0-9a-f]{32}\.pdf)', path
    ):
        raise ValueError('Invalid storage path.')


def _validate_data(data: bytes) -> None:
    if not isinstance(data, bytes):
        raise TypeError('Storage data must be bytes.')


class LocalStorage:
    """Store objects under a private directory controlled by the service account."""

    def __init__(self, data: Path):
        try:
            self.data = Path(data).resolve()
            self.data.mkdir(mode=0o700, parents=True, exist_ok=True)
        except (OSError, RuntimeError, ValueError, TypeError):
            raise StorageError('Storage unavailable.') from None

    def _target(self, path: str) -> Path:
        _validate_path(path)
        target = self.data / path
        try:
            # Reject directory redirects as well as final-file symlinks, including
            # Windows junctions. Never resolve an upload into a different prefix.
            for part in (self.data, target.parent, target):
                if part.is_symlink() or part.is_junction():
                    raise StorageError('Storage unavailable.')
            if self.data.resolve() != self.data or not target.resolve().is_relative_to(self.data):
                raise StorageError('Storage unavailable.')
        except (OSError, RuntimeError):
            raise StorageError('Storage unavailable.') from None
        return target

    def put(self, path: str, data: bytes) -> None:
        target = self._target(path)
        _validate_data(data)
        temporary = target.parent / ('.upload-' + uuid.uuid4().hex)
        try:
            target.parent.mkdir(mode=0o700, exist_ok=True)
            self._target(path)
            # Replace atomically: a failed/repeated upload cannot truncate the
            # previously stored photo or card. New files have private POSIX mode.
            descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(data)
            self._target(path)
            temporary.replace(target)
        except (OSError, RuntimeError):
            raise StorageError('Storage unavailable.') from None
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def get(self, path: str) -> bytes:
        target = self._target(path)
        try:
            return target.read_bytes()
        except FileNotFoundError:
            raise StorageNotFound('Storage object not found.') from None
        except OSError:
            raise StorageError('Storage unavailable.') from None

    def exists(self, path: str) -> bool:
        target = self._target(path)
        try:
            # stat(), rather than exists(), preserves permission/I/O failures.
            if not stat.S_ISREG(target.stat().st_mode):
                raise StorageError('Storage unavailable.')
            return True
        except FileNotFoundError:
            return False
        except OSError:
            raise StorageError('Storage unavailable.') from None

    def delete(self, path: str) -> None:
        target = self._target(path)
        try:
            target.unlink()
        except FileNotFoundError:
            raise StorageNotFound('Storage object not found.') from None
        except OSError:
            raise StorageError('Storage unavailable.') from None


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # urllib otherwise forwards custom authentication headers on redirects.
        return None


class SupabaseStorage:
    """Synchronous standard-library REST client, with no bucket management.

    put is an upsert and can safely be retried by the caller. get/delete raise
    StorageNotFound on HTTP 404; exists returns False only for HTTP 404.
    """

    def __init__(self, url, service_key, bucket):
        try:
            parsed = urlsplit(url)
            valid_url = (
                isinstance(url, str) and parsed.scheme == 'https' and parsed.hostname
                and parsed.username is None and parsed.password is None
                and parsed.path in ('', '/') and not parsed.query and not parsed.fragment
                and not any(ord(char) < 33 or ord(char) > 126 for char in url)
                and '\\' not in url and parsed.port in (None, 443)
            )
        except (ValueError, TypeError, AttributeError):
            valid_url = False
        if not valid_url or not isinstance(bucket, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}', bucket):
            raise ValueError('Invalid storage configuration.')
        if not isinstance(service_key, str) or not service_key or any(
            ord(char) < 33 or ord(char) > 126 for char in service_key
        ):
            raise ValueError('Invalid storage configuration.')
        self._base = url.rstrip('/') + '/storage/v1/object/'
        self._key = service_key
        self._bucket = bucket
        self._opener = request.build_opener(_NoRedirect())

    def _request(self, method, path, data=None, prefix='', headers=None):
        _validate_path(path)
        auth = {'Authorization': 'Bearer ' + self._key, 'apikey': self._key}
        auth.update(headers or {})
        try:
            req = request.Request(self._base + prefix + self._bucket + '/' + path,
                                  data=data, headers=auth, method=method)
            with self._opener.open(req, timeout=30) as response:
                if response.status == 404:
                    raise StorageNotFound('Storage object not found.')
                if not 200 <= response.status < 300:
                    raise StorageError('Storage unavailable.')
                return response.read()
        except error.HTTPError as exc:
            status = exc.code
            exc.close()
            if status == 404:
                raise StorageNotFound('Storage object not found.') from None
            raise StorageError('Storage unavailable.') from None
        except StorageNotFound:
            raise
        except (OSError, ValueError, HTTPException):
            # Do not retain response bodies, URLs, headers or exception messages.
            raise StorageError('Storage unavailable.') from None

    def put(self, path: str, data: bytes) -> None:
        _validate_path(path)
        _validate_data(data)
        content_type = 'image/jpeg' if path.startswith('photos/') else 'application/pdf'
        self._request('POST', path, data, headers={'Content-Type': content_type, 'x-upsert': 'true'})

    def get(self, path: str) -> bytes:
        return self._request('GET', path, prefix='authenticated/')

    def exists(self, path: str) -> bool:
        try:
            self._request('HEAD', path, prefix='info/')
            return True
        except StorageNotFound:
            return False

    def delete(self, path: str) -> None:
        self._request('DELETE', path)
