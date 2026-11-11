"""Small PostgreSQL bridge for the service's SQLite-style connection API.

The driver is optional until connection() is called. Supabase connections must
use its session pooler (port 5432), not its transaction pooler (port 6543): the
private search_path and timeouts are session settings.
"""

import importlib


# Stable across Python processes and releases; never use Python's salted hash().
WRITER_LOCK = 0x4C4E485F4D454D42  # LNH_MEMB, within PostgreSQL's signed bigint.


class Row:
    """sqlite3.Row's mapping and positional access used by the service."""

    def __init__(self, columns, values):
        self._columns = columns
        self._values = tuple(values)

    def keys(self):
        return list(self._columns)

    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            return self._values[key]
        try:
            return self._values[self._columns.index(key)]
        except ValueError:
            raise IndexError('No item with that key') from None

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)


def _row_factory(cursor):
    columns = tuple(column.name for column in cursor.description or ())
    return lambda values: Row(columns, values)


def _parameters(sql):
    """Translate project qmarks, preserving quoted SQL and comments.

    This is for the project's SQL, not PostgreSQL JSON '?' operators. Percent
    signs must be escaped when psycopg's parameter binding is in use.
    """
    result = []
    index = 0
    while index < len(sql):
        char = sql[index]
        if char in ("'", '"'):
            quote, start = char, index
            index += 1
            while index < len(sql):
                if sql[index] == quote:
                    index += 1
                    if index < len(sql) and sql[index] == quote:
                        index += 1
                        continue
                    break
                index += 1
            result.append(sql[start:index].replace('%', '%%'))
        elif sql.startswith('--', index):
            end = sql.find('\n', index)
            end = len(sql) if end == -1 else end
            result.append(sql[index:end].replace('%', '%%'))
            index = end
        elif sql.startswith('/*', index):
            start, depth = index, 1
            index += 2
            while index < len(sql) and depth:
                if sql.startswith('/*', index):
                    depth += 1
                    index += 2
                elif sql.startswith('*/', index):
                    depth -= 1
                    index += 2
                else:
                    index += 1
            result.append(sql[start:index].replace('%', '%%'))
        else:
            result.append('%s' if char == '?' else '%%' if char == '%' else char)
            index += 1
    return ''.join(result)


class Connection:
    """Buffered psycopg cursors retain fetch/iteration/rowcount after commit."""

    def __init__(self, raw):
        self._raw = raw
        self._in_transaction = False

    def _begin(self, writer):
        self._raw.execute('BEGIN').close()
        self._in_transaction = True
        try:
            if writer:
                return self._raw.execute('SELECT pg_advisory_xact_lock(%s)', (WRITER_LOCK,))
            return None
        except Exception:
            self.rollback()
            raise

    def execute(self, sql, params=None):
        command = sql.strip().rstrip(';').strip().upper()
        if command in ('BEGIN IMMEDIATE', 'BEGIN'):
            if self._in_transaction:
                raise RuntimeError('Une transaction est déjà ouverte.')
            return self._begin(writer=True)

        # Also serialize isolated writes if a caller omits BEGIN IMMEDIATE.
        reader = command.startswith(('SELECT ', 'SELECT\n', 'SHOW ', 'EXPLAIN '))
        automatic = not self._in_transaction and not reader
        if automatic:
            # Unknown commands (including WITH) take the writer lock as well.
            lock = self._begin(writer=True)
            if lock is not None:
                lock.close()
        try:
            cursor = self._raw.execute(_parameters(sql), params) if params is not None else self._raw.execute(sql)
            if automatic:
                try:
                    self.commit()
                except Exception:
                    cursor.close()
                    raise
            return cursor
        except Exception:
            if automatic:
                self.rollback()
            raise

    def commit(self):
        self._raw.commit()
        self._in_transaction = False

    def rollback(self):
        self._raw.rollback()
        self._in_transaction = False

    def close(self):
        # Closing an uncommitted psycopg connection rolls back and releases locks.
        self._raw.close()
        self._in_transaction = False


def connection(database_url):
    """Open a private DSN with TLS (except explicit loopback QA) and no preparation.

    Never include the DSN or a driver's connection diagnostics in an exception:
    malformed DSNs and connection errors can contain passwords or user names.
    """
    try:
        psycopg = importlib.import_module('psycopg')
        conninfo = importlib.import_module('psycopg.conninfo')
    except ImportError:
        raise RuntimeError('PostgreSQL nécessite psycopg v3 : installe la dépendance PostgreSQL du projet.') from None
    if not isinstance(database_url, str) or not database_url.strip():
        raise ValueError('Configuration PostgreSQL manquante.')
    try:
        parameters = conninfo.conninfo_to_dict(database_url)
    except Exception:
        raise ValueError('Configuration PostgreSQL invalide.') from None
    sslmode = parameters.get('sslmode', 'require')
    hosts = parameters.get('host', '').split(',')
    addresses = parameters.get('hostaddr', '').split(',') if parameters.get('hostaddr') else []
    loopback = all(host in ('localhost', '127.0.0.1') for host in hosts + addresses)
    if sslmode not in ('require', 'verify-ca', 'verify-full') and not (sslmode == 'disable' and loopback):
        raise ValueError('PostgreSQL impose sslmode=require, verify-ca ou verify-full.')
    raw = None
    try:
        raw = psycopg.connect(database_url, autocommit=True, prepare_threshold=None,
                             sslmode=sslmode, connect_timeout=30, row_factory=_row_factory)
        raw.execute('SET search_path TO lnh_private').close()
        raw.execute("SET lock_timeout = '30s'").close()
        raw.execute("SET statement_timeout = '60s'").close()
    except Exception:
        if raw is not None:
            try:
                raw.close()
            except Exception:
                pass  # Cleanup diagnostics must not disclose the private DSN.
        raise RuntimeError('Connexion PostgreSQL impossible. Vérifie la configuration privée et le réseau.') from None
    return Connection(raw)
