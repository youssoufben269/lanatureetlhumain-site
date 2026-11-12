import base64
import calendar
import contextlib
import io
import json
import os
import secrets
import sqlite3
import shutil
import time
import uuid
import warnings
from datetime import datetime, timezone, date
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageOps, UnidentifiedImageError

from .payments import ManualPayments
from .security import Problem, clean, digest, email, hash_password, verify_password

Image.MAX_IMAGE_PIXELS = 16_000_000
CONSENT_VERSION = '2026-11-11-v1'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Service:
    def __init__(self, settings):
        self.cfg = settings
        settings.validate()
        for directory in (settings.data, settings.data / 'photos', settings.data / 'cards'):
            directory.mkdir(parents=True, exist_ok=True, mode=0o777 if os.name == 'nt' else 0o700)
            if os.name != 'nt':
                directory.chmod(0o700)
        self.database = settings.data / 'members.sqlite3'
        from .storage import LocalStorage, SupabaseStorage
        self.storage = (SupabaseStorage(settings.supabase_url, settings.supabase_service_key, settings.storage_bucket)
                        if settings.storage_backend == 'supabase' else LocalStorage(settings.data))
        self.migrate()
        if not settings.database_url and os.name != 'nt':
            self.database.chmod(0o600)

    def connection(self):
        if self.cfg.database_url:
            from .database import connection
            return connection(self.cfg.database_url)
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=30000')
        return db

    @contextlib.contextmanager
    def transaction(self):
        with contextlib.closing(self.connection()) as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    def migrate(self):
        if not self.cfg.database_url:
            self.enable_wal()
        migrations = Path(__file__).parent / 'migrations'
        if self.cfg.database_url:
            migrations = migrations / 'postgres'
        with self.transaction() as db:
            if self.cfg.database_url:
                db.execute('CREATE SCHEMA IF NOT EXISTS lnh_private')
                db.execute('REVOKE ALL ON SCHEMA lnh_private FROM PUBLIC')
            db.execute('CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY)')
            applied = {row[0] for row in db.execute('SELECT version FROM schema_migrations')}
            for path in sorted(migrations.glob('*.sql')):
                if int(path.name.split('_')[0]) not in applied:
                    statement = ''
                    for line in path.read_text(encoding='utf-8').splitlines(keepends=True):
                        statement += line
                        if sqlite3.complete_statement(statement):
                            db.execute(statement)
                            statement = ''
                    if statement.strip():
                        raise ValueError('Migration SQL incomplète : ' + path.name)

    def enable_wal(self):
        with contextlib.closing(self.connection()) as db:
            deadline = time.monotonic() + 30
            while True:
                try:
                    db.execute('PRAGMA journal_mode=WAL')
                    break
                except sqlite3.OperationalError as exc:
                    # SQLite can return BUSY immediately for simultaneous journal-mode
                    # changes, even with busy_timeout. Retry only this startup race.
                    if getattr(exc, 'sqlite_errorcode', None) not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or time.monotonic() >= deadline:
                        raise
                    time.sleep(.05)

    def rate_limit(self, key, limit, seconds):
        stamp = int(time.time())
        with self.transaction() as db:
            db.execute('DELETE FROM rate_limits WHERE expires_at < ?', (stamp,))
            row = db.execute('SELECT * FROM rate_limits WHERE key=?', (key,)).fetchone()
            if row and row['count'] >= limit:
                raise Problem('Trop de tentatives. Veuillez réessayer plus tard.', 429)
            db.execute('INSERT INTO rate_limits VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=rate_limits.count+1', (key, stamp + seconds))

    def add_admin(self, address, password):
        with self.transaction() as db:
            db.execute('INSERT INTO admins VALUES(?,?,?,1)', (uuid.uuid4().hex, email(address), hash_password(password)))

    def bootstrap_admin(self, address, password):
        # Free hosts may have no interactive shell. Never reset an existing account.
        with self.transaction() as db:
            if db.execute('SELECT 1 FROM admins LIMIT 1').fetchone():
                return False
            db.execute('INSERT INTO admins VALUES(?,?,?,1)', (uuid.uuid4().hex, email(address), hash_password(password)))
        return True

    def login(self, data, remote):
        self.rate_limit('login-ip:' + digest(remote), 15, 900)
        address = email(data.get('email'))
        self.rate_limit('login-account:' + digest(address), 15, 900)
        password = data.get('password')
        if not isinstance(password, str) or not 1 <= len(password) <= 256:
            raise Problem('Identifiants incorrects.', 401)
        with self.transaction() as db:
            admin = db.execute('SELECT * FROM admins WHERE email=? AND active=1', (address,)).fetchone()
            # Spend the same KDF work for unknown users; do not expose the admin directory.
            dummy = 'scrypt$MDAwMDAwMDAwMDAwMDAwMA==$' + base64.b64encode(bytes(64)).decode()
            valid = verify_password(password, admin['password_hash'] if admin else dummy)
            if not admin or not valid:
                raise Problem('Identifiants incorrects.', 401)
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE expires_at < ?', (int(time.time()),))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?)',
                       (digest(token), admin['id'], csrf, int(time.time()) + self.cfg.session_seconds))
        return token, csrf

    def session(self, token):
        with contextlib.closing(self.connection()) as db:
            row = db.execute('SELECT s.*,a.email FROM sessions s JOIN admins a ON a.id=s.admin_id WHERE s.token_hash=? AND s.expires_at>? AND a.active=1',
                             (digest(token), int(time.time()))).fetchone()
        if not row:
            raise Problem('Veuillez vous connecter à l’administration.', 401)
        return dict(row)

    def logout(self, token):
        with self.transaction() as db:
            db.execute('DELETE FROM sessions WHERE token_hash=?', (digest(token),))

    def photo(self, data):
        if not isinstance(data, dict) or data.get('mime') not in ('image/jpeg', 'image/png'):
            raise Problem('La photo doit être un fichier JPEG ou PNG.')
        filename = clean(data.get('name'), 'nom du fichier', 180)
        if Path(filename).suffix.lower() not in ('.jpg', '.jpeg', '.png'):
            raise Problem('Extension de photo non autorisée.')
        encoded = data.get('base64')
        if not isinstance(encoded, str) or len(encoded) > 4_000_000:
            raise Problem('La photo ne doit pas dépasser 3 Mo.')
        try:
            raw = base64.b64decode(encoded, validate=True)
            if not raw or len(raw) > 3_000_000:
                raise ValueError()
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(raw)) as source:
                    expected = 'JPEG' if data['mime'] == 'image/jpeg' else 'PNG'
                    if source.format != expected or source.width < 240 or source.height < 320 or getattr(source, 'n_frames', 1) != 1:
                        raise ValueError()
                    source.load()
                    image = ImageOps.exif_transpose(source).convert('RGB')
                    image.thumbnail((1200, 1600))
                    output = io.BytesIO()
                    # Re-encode into a fresh image: discard EXIF, GPS and other source metadata.
                    clean_image = Image.new('RGB', image.size, 'white')
                    clean_image.paste(image)
                    clean_image.save(output, 'JPEG', quality=95)
                    return output.getvalue()
        except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise Problem('Photo invalide : JPEG/PNG non animé, au moins 240 × 320 pixels, maximum 3 Mo et 16 mégapixels.')

    def submit(self, data, remote, *, actor='public'):
        self.rate_limit(('submission:' + digest(remote)) if actor == 'public' else ('import:' + digest(actor)), 10 if actor == 'public' else 120, 3600)
        if data.get('website', ''):
            raise Problem('Demande non recevable.')
        if data.get('consent') is not True or data.get('consent_version') not in ({CONSENT_VERSION, '2026-11-11-v2'} if actor != 'public' else {CONSENT_VERSION}):
            raise Problem('Le consentement à la notice de confidentialité est nécessaire.')
        values = {key: clean(data.get(key, ''), key, maximum, required)
                  for key, maximum, required in (
                      ('first_name', 80, True), ('last_name', 80, True), ('phone', 40, True),
                      ('address', 250, False), ('city', 100, False), ('country', 100, False),
                      ('profession', 120, False), ('motivation', 2000, actor == 'public'), ('category', 60, True))}
        if values['category'] not in self.cfg.categories:
            raise Problem('Catégorie de membre inconnue.')
        if any(ch in values['first_name'] + values['last_name'] for ch in '\n\t'):
            raise Problem('Nom et prénom sur une seule ligne.')
        self.validate_card_text(values)
        address, image = email(data.get('email')), self.photo(data.get('photo'))
        identifier, stamp = uuid.uuid4().hex, now()
        photo_path = 'photos/' + identifier + '.jpg'
        with self.transaction() as db:
            # Same response for duplicate submissions; no public email enumeration.
            existing = db.execute('SELECT id FROM applications WHERE email=?', (address,)).fetchone()
            if existing:
                return existing['id']
            self.storage.put(photo_path, image)
            try:
                keys = [*values, 'id', 'email', 'photo_path', 'consent_at', 'consent_version', 'status', 'created_at', 'updated_at']
                db.execute(f'INSERT INTO applications({",".join(keys)}) VALUES({",".join("?" for _ in keys)})',
                           [*values.values(), identifier, address, photo_path, stamp, data['consent_version'], 'soumise', stamp, stamp])
                self.audit(db, identifier, actor, 'submit' if actor == 'public' else 'import_email', None, 'soumise')
                if actor == 'public':
                    self.enqueue(db, identifier, 'reception', address, {})
            except Exception:
                self.storage.delete(photo_path)
                raise
        return identifier

    def audit(self, db, identifier, actor, action, old, new):
        db.execute('INSERT INTO audit(application_id,actor,action,old_status,new_status,created_at) VALUES(?,?,?,?,?,?)',
                   (identifier, actor, action, old, new, now()))

    def validate_card_text(self, values):
        from .cards import validate_card_text
        try:
            validate_card_text(values)
        except ValueError:
            raise Problem('Le nom, la catégorie ou la fonction dépasse la place disponible sur la carte. Contactez l’association ou utilisez une fonction plus courte.')

    def enqueue(self, db, identifier, kind, recipient, payload):
        db.execute('INSERT INTO outbox(application_id,kind,recipient,payload) VALUES(?,?,?,?) ON CONFLICT DO NOTHING',
                   (identifier, kind, recipient, json.dumps(payload)))

    def list(self, offset=0):
        with contextlib.closing(self.connection()) as db:
            rows = db.execute('SELECT id,first_name,last_name,email,status,member_number,created_at FROM applications ORDER BY created_at DESC,id LIMIT 50 OFFSET ?', (offset,)).fetchall()
            total = db.execute('SELECT count(*) FROM applications').fetchone()[0]
        return {'items': [dict(row) for row in rows], 'total': total}

    def detail(self, identifier):
        with contextlib.closing(self.connection()) as db:
            row = db.execute('SELECT * FROM applications WHERE id=?', (identifier,)).fetchone()
            if not row:
                raise Problem('Demande introuvable.', 404)
            result = dict(row)
            payment = db.execute('SELECT * FROM payments WHERE application_id=?', (identifier,)).fetchone()
            result['payment'] = dict(payment) if payment else None
            result['history'] = [dict(x) for x in db.execute('SELECT action,actor,old_status,new_status,created_at FROM audit WHERE application_id=? ORDER BY id', (identifier,))]
        return result

    def change(self, identifier, actor, data):
        action, stamp = data.get('action'), now()
        generate = False
        with self.transaction() as db:
            row = db.execute('SELECT * FROM applications WHERE id=?', (identifier,)).fetchone()
            if not row:
                raise Problem('Demande introuvable.', 404)
            if type(data.get('version')) is not int or row['version'] != data['version']:
                raise Problem('La fiche a changé. Recharge-la avant de continuer.', 409)
            old, state = row['status'], row['status']
            if old == 'refusee':
                raise Problem('Cette demande est clôturée.', 409)
            paid = db.execute('SELECT 1 FROM payments WHERE application_id=?', (identifier,)).fetchone() is not None
            approved = bool(row['approved_at'])
            if action == 'function':
                if row['card_path']:
                    raise Problem('Une carte délivrée ne peut pas être modifiée par ce formulaire.', 409)
                function = clean(data.get('function'), 'fonction attribuée', 80)
                if '\n' in function or '\t' in function:
                    raise Problem('La fonction doit tenir sur une ligne.')
                self.validate_card_text({**dict(row), 'function': function})
                db.execute('UPDATE applications SET function=? WHERE id=?', (function, identifier))
            elif action == 'review':
                if row['member_number']:
                    raise Problem('Cette carte est déjà délivrée.', 409)
                state = 'en_attente_de_validation' if paid else 'en_attente_de_paiement'
            elif action == 'payment':
                if paid:
                    raise Problem('Le paiement est déjà confirmé.', 409)
                ManualPayments().confirm(db, identifier, actor, data, self.cfg, stamp)
                paid = True
                state = 'en_attente_de_validation'
            elif action == 'approve':
                if approved:
                    raise Problem('Cette demande est déjà approuvée.', 409)
                if not row['function']:
                    raise Problem('L’association doit attribuer une fonction avant validation.', 409)
                approved = True
                state = 'en_attente_de_paiement'
                db.execute('UPDATE applications SET approved_at=?,approved_by=? WHERE id=?', (stamp, actor, identifier))
            elif action == 'refuse':
                reason = clean(data.get('reason'), 'motif de refus', 1000)
                state = 'refusee'
                db.execute('UPDATE applications SET refusal_reason=? WHERE id=?', (reason, identifier))
                db.execute('DELETE FROM downloads WHERE application_id=?', (identifier,))
                # Cancel unsent approval/card notices, including obsolete private links.
                db.execute("UPDATE outbox SET state='cancelled' WHERE application_id=? AND kind IN ('validation','carte') AND state != 'sent'", (identifier,))
                self.enqueue(db, identifier, 'refus', row['email'], {'reason': reason})
            elif action == 'generate':
                if not paid or not approved or not row['member_number']:
                    raise Problem('Validation et paiement requis avant génération.', 409)
            else:
                raise Problem('Action inconnue.')
            if state != 'refusee' and paid and approved:
                if action != 'function':
                    self.validate_card_text(dict(row))
                if not row['member_number']:
                    joined = datetime.fromisoformat(stamp).astimezone(ZoneInfo(self.cfg.timezone)).date()
                    year, month = divmod(joined.year * 12 + joined.month - 1 + self.cfg.validity_months, 12)
                    month += 1
                    expires = date(year, month, min(joined.day, calendar.monthrange(year, month)[1]))
                    seq = db.execute('INSERT INTO sequences VALUES(?,1) ON CONFLICT(year) DO UPDATE SET value=sequences.value+1 RETURNING value', (joined.year,)).fetchone()[0]
                    number = f'ANH-{joined.year}-{seq:03d}'
                    db.execute('UPDATE applications SET member_number=?,joined_on=?,expires_on=? WHERE id=?',
                               (number, joined.isoformat(), expires.isoformat(), identifier))
                    self.enqueue(db, identifier, 'validation', row['email'], {'number': number})
                state = 'carte_generee' if row['card_path'] else 'validee'
                generate = not row['card_path']
            db.execute('UPDATE applications SET status=?,version=version+1,updated_at=? WHERE id=?', (state, stamp, identifier))
            self.audit(db, identifier, actor, action, old, state)
        if generate:
            self.generate(identifier, actor)
        return self.detail(identifier)

    def generate(self, identifier, actor):
        from .cards import make_card
        # Lock the member record through generation; concurrent requests cannot issue twice.
        try:
            with self.transaction() as db:
                row = db.execute('SELECT * FROM applications WHERE id=?', (identifier,)).fetchone()
                if row['status'] != 'validee' or row['card_path']:
                    return
                path = 'cards/' + identifier + '.pdf'
                if self.cfg.storage_backend == 'local':
                    make_card(dict(row), self.cfg, self.cfg.data / path)
                else:
                    # Only this transient rendering workspace is local on a free host.
                    # Durable photo/PDF objects stay in the private remote bucket.
                    workspace = self.cfg.data / ('render-' + uuid.uuid4().hex)
                    workspace.mkdir(mode=0o700)
                    try:
                        output = workspace / 'card.pdf'
                        make_card(dict(row), self.cfg, output, photo_bytes=self.storage.get(row['photo_path']))
                        self.storage.put(path, output.read_bytes())
                    finally:
                        shutil.rmtree(workspace)
                url = '/api/admin/applications/' + identifier + '/card'
                db.execute("UPDATE applications SET status='carte_generee',card_path=?,card_url=?,card_error=NULL,version=version+1,updated_at=? WHERE id=?", (path, url, now(), identifier))
                token = secrets.token_urlsafe(32)
                db.execute('INSERT INTO downloads VALUES(?,?,?)', (digest(token), identifier, int(time.time()) + 7 * 86400))
                self.enqueue(db, identifier, 'carte', row['email'], {'number': row['member_number'], 'link': self.cfg.origin + '/adhesion/carte.html#token=' + token})
                self.audit(db, identifier, actor, 'generate', 'validee', 'carte_generee')
        except Exception:
            # Preserve the assigned number; allow an explicit retry after fixing assets/config.
            with self.transaction() as db:
                db.execute("UPDATE applications SET card_error='La génération a échoué. Vérifier les ressources serveur puis réessayer.',version=version+1 WHERE id=?", (identifier,))
                self.audit(db, identifier, actor, 'generation_failed', 'validee', 'validee')

    def download(self, token):
        if not isinstance(token, str) or not 20 <= len(token) <= 100:
            raise Problem('Lien incorrect ou expiré.', 404)
        with contextlib.closing(self.connection()) as db:
            row = db.execute("SELECT a.* FROM downloads d JOIN applications a ON a.id=d.application_id WHERE d.token_hash=? AND d.expires_at>? AND a.status='carte_generee' AND a.expires_on>=?", (digest(token), int(time.time()), datetime.now(ZoneInfo(self.cfg.timezone)).date().isoformat())).fetchone()
        if not row:
            raise Problem('Lien incorrect, expiré ou carte désactivée. Contactez l’association.', 404)
        return dict(row)

    def verification(self, number):
        if not self.cfg.public_verification:
            raise Problem('Page introuvable.', 404)
        with contextlib.closing(self.connection()) as db:
            row = db.execute('SELECT status,expires_on FROM applications WHERE member_number=?', (number,)).fetchone()
        # Deliberately exclude name, photo and contact details from this public endpoint.
        return {'number': number, 'active': bool(row and row['status'] == 'carte_generee' and row['expires_on'] >= datetime.now(ZoneInfo(self.cfg.timezone)).date().isoformat())}
