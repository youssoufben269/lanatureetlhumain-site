import hmac
import html
import json
import logging
import mimetypes
import re
import secrets
from http import HTTPStatus
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

from .config import Settings
from .security import Problem
from .service import CONSENT_VERSION, Service

LOG = logging.getLogger('membership')


class Application:
    def __init__(self, settings=None):
        self.cfg = settings or Settings.from_env()
        self.service = Service(self.cfg)

    def __call__(self, env, start_response):
        origin = env.get('HTTP_ORIGIN', '')
        trusted = (self.cfg.origin, *self.cfg.allowed_origins)
        method, path = env['REQUEST_METHOD'], env.get('PATH_INFO', '/')
        headers = [('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer'),
                   ('X-Frame-Options', 'DENY'), ('Cache-Control', 'no-store'),
                   ('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')]
        if self.cfg.secure_cookies:
            headers.append(('Strict-Transport-Security', 'max-age=31536000'))
        if origin in trusted:
            headers += [('Access-Control-Allow-Origin', origin), ('Access-Control-Allow-Credentials', 'true'), ('Vary', 'Origin')]
        try:
            if method == 'OPTIONS':
                if origin not in trusted:
                    raise Problem('Origine non autorisée.', 403)
                headers += [('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'), ('Access-Control-Allow-Headers', 'Content-Type, X-CSRF-Token')]
                status, mime, body = 204, 'text/plain', b''
            else:
                if method not in ('GET', 'POST'):
                    raise Problem('Méthode non autorisée.', 405)
                if method == 'POST' and origin not in trusted:
                    raise Problem('Origine non autorisée.', 403)
                data = self.body(env) if method == 'POST' else None
                status, mime, body, extra = self.dispatch(env, method, path, data)
                headers += extra
        except Problem as exc:
            status, mime, body = exc.status, 'application/json', json.dumps({'error': exc.message}, ensure_ascii=False).encode()
        except Exception:
            incident = secrets.token_hex(5)
            LOG.error('Erreur serveur incident=%s', incident, exc_info=True)
            status, mime, body = 500, 'application/json', json.dumps({'error': 'Erreur serveur. Référence : ' + incident}).encode()
        headers += [('Content-Type', mime + ('; charset=utf-8' if mime.startswith('text/') or mime == 'application/json' else '')), ('Content-Length', str(len(body)))]
        start_response(f'{status} {HTTPStatus(status).phrase}', headers)
        return [body]

    def body(self, env):
        if env.get('CONTENT_TYPE', '').split(';')[0].lower() != 'application/json':
            raise Problem('Contenu JSON attendu.', 415)
        try:
            size = int(env.get('CONTENT_LENGTH', '0'))
        except ValueError:
            raise Problem('Taille de requête incorrecte.')
        if size <= 0 or size > self.cfg.max_body:
            raise Problem('Requête vide ou trop volumineuse.', 413)
        try:
            data = json.loads(env['wsgi.input'].read(size))
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except (ValueError, UnicodeDecodeError):
            raise Problem('JSON incorrect.')

    def cookie(self, token, clear=False):
        return ('Set-Cookie', f'lnh_session={token}; HttpOnly; Path=/; SameSite=Strict; Max-Age={0 if clear else self.cfg.session_seconds}' + ('; Secure' if self.cfg.secure_cookies else ''))

    def auth(self, env, mutate=False):
        cookies = SimpleCookie()
        try:
            cookies.load(env.get('HTTP_COOKIE', ''))
        except Exception:
            raise Problem('Session incorrecte.', 401)
        token = cookies['lnh_session'].value if 'lnh_session' in cookies else ''
        session = self.service.session(token)
        if mutate and not hmac.compare_digest(env.get('HTTP_X_CSRF_TOKEN', ''), session['csrf']):
            raise Problem('La protection de session a expiré. Recharge la page.', 403)
        return token, session

    def json(self, data, status=200, headers=None):
        return status, 'application/json', json.dumps(data, ensure_ascii=False).encode(), headers or []

    def card(self, member):
        if not member.get('card_path') or member['status'] != 'carte_generee':
            raise Problem('La carte n’est pas disponible.', 404)
        try:
            content = self.service.storage.get(member['card_path'])
        except FileNotFoundError:
            raise Problem('Fichier indisponible. Contacte l’association.', 404)
        return 200, 'application/pdf', content, [('Content-Disposition', 'attachment; filename="' + member['member_number'] + '.pdf"')]

    def dispatch(self, env, method, path, data):
        remote = env.get('REMOTE_ADDR', 'unknown')  # Do not trust client-supplied X-Forwarded-For.
        if path == '/api/health' and method == 'GET':
            return self.json({'ok': True})
        if path == '/api/membership/config' and method == 'GET':
            return self.json({'categories': self.cfg.categories, 'fee_minor': self.cfg.fee_minor,
                              'currency': self.cfg.currency, 'consent_version': CONSENT_VERSION,
                              'privacy_contact': self.cfg.privacy_contact, 'retention_days': self.cfg.retention_days})
        if path == '/api/membership/applications' and method == 'POST':
            self.service.submit(data, remote)
            return self.json({'message': 'Ta demande a été prise en compte. L’association examinera les informations reçues. Si cette adresse a déjà été utilisée, contacte-nous pour suivre ton dossier.'}, 202)
        if path == '/api/session' and method == 'GET':
            try:
                _, session = self.auth(env)
            except Problem:
                return self.json({'authenticated': False})
            return self.json({'authenticated': True, 'csrf': session['csrf'], 'email': session['email']})
        if path == '/api/login' and method == 'POST':
            token, csrf = self.service.login(data, remote)
            return self.json({'authenticated': True, 'csrf': csrf}, headers=[self.cookie(token)])
        if path == '/api/logout' and method == 'POST':
            token, _ = self.auth(env, True)
            self.service.logout(token)
            return self.json({'ok': True}, headers=[self.cookie('', clear=True)])
        if path == '/api/card-download' and method == 'POST':
            self.service.rate_limit('download:' + remote, 60, 3600)
            return self.card(self.service.download(data.get('token')))
        if path == '/api/admin/applications' and method == 'GET':
            self.auth(env)
            try:
                offset = int(parse_qs(env.get('QUERY_STRING', '')).get('offset', ['0'])[0])
                if not 0 <= offset <= 1_000_000:
                    raise ValueError()
            except ValueError:
                raise Problem('Pagination incorrecte.')
            return self.json(self.service.list(offset))
        match = re.fullmatch(r'/api/admin/applications/([a-f0-9]{32})(?:/(photo|card|action))?', path)
        if match:
            identifier, item = match.groups()
            _, session = self.auth(env, method == 'POST')
            if item == 'action' and method == 'POST':
                return self.json(self.service.change(identifier, session['admin_id'], data))
            if method != 'GET':
                raise Problem('Méthode non autorisée.', 405)
            member = self.service.detail(identifier)
            if not item:
                return self.json(member)
            if item == 'photo':
                return 200, 'image/jpeg', self.service.storage.get(member['photo_path']), []
            if item == 'card':
                return self.card(member)
        if re.fullmatch(r'/membre/ANH-\d{4}-\d{3,}', path) and method == 'GET':
            result = self.service.verification(path.split('/')[-1])
            page = '<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="robots" content="noindex"><meta name="viewport" content="width=device-width"><title>Vérifier une carte</title><body><main><h1>La Nature et l’Humain</h1><p>' + html.escape(result['number']) + '</p><p>' + ('Carte active' if result['active'] else 'Carte inactive ou inconnue') + '</p></main></body></html>'
            return 200, 'text/html', page.encode(), []
        if path.startswith('/api/'):
            raise Problem('Ressource introuvable.', 404)
        if method != 'GET':
            raise Problem('Méthode non autorisée.', 405)
        if path in ('/adhesion', '/admin/adhesions'):
            return 301, 'text/plain', b'', [('Location', path + '/')]
        # Explicit public surface. Never mount the repository root or private data directory.
        aliases = {'/': 'index.html', '/index.html': 'index.html', '/adhesion': 'adhesion/index.html',
                   '/adhesion/': 'adhesion/index.html', '/admin/adhesions': 'admin/adhesions/index.html',
                   '/admin/adhesions/': 'admin/adhesions/index.html', '/robots.txt': 'robots.txt', '/sitemap.xml': 'sitemap.xml'}
        relative = aliases.get(path)
        if relative is None and (path in ('/adhesion/carte.html', '/adhesion/confidentialite.html') or re.fullmatch(r'/adhesion/assets/[a-z0-9-]+\.(?:css|js|mjs|png)', path) or re.fullmatch(r'/assets/(?:logo-officiel\.jpg|accueil-[1-3]\.webp)', path)):
            relative = path.lstrip('/')
        if relative is None:
            raise Problem('Page introuvable.', 404)
        file = self.cfg.root / relative
        if not file.is_file():
            raise Problem('Page introuvable.', 404)
        mime = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        extra = []
        if path.startswith(('/adhesion', '/admin')):
            extra.append(('Content-Security-Policy', "default-src 'self'; script-src 'self'; worker-src 'self' blob:; style-src 'self'; font-src 'self' data: blob:; img-src 'self' data: blob:; connect-src 'self' " + ' '.join((self.cfg.origin, *self.cfg.allowed_origins)) + "; frame-src 'self' blob:; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"))
        return 200, mime, file.read_bytes(), extra
