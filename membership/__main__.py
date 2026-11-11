import argparse
import contextlib
import getpass
import json
import logging
import os
import time
import webbrowser
from pathlib import Path
from wsgiref.simple_server import make_server, WSGIRequestHandler

from .config import Settings
from .mail import flush
from .service import Service
from .web import Application


def main():
    parser = argparse.ArgumentParser(description='Administration du module adhésion LNH')
    parser.add_argument('command', choices=('migrate', 'create-admin', 'serve-dev', 'serve', 'flush-email', 'purge-closed', 'manage-local'))
    parser.add_argument('--email')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--confirm', action='store_true', help='Confirmer la suppression des dossiers refusés expirés')
    args = parser.parse_args()
    settings = Settings.from_env()
    if args.command == 'manage-local':
        if args.host not in ('127.0.0.1', 'localhost'):
            parser.error('La gestion locale reste sur cet ordinateur.')
        settings.database_url = ''
        settings.storage_backend = 'local'
        settings.require_remote_storage = False
        settings.data = Path(__file__).resolve().parent.parent / 'var'
        settings.origin = f'http://127.0.0.1:{args.port}'
        settings.secure_cookies = False
        settings.allowed_origins = ()
        settings.qr_mode, settings.public_verification = 'website', False
    service = Service(settings)
    if args.command == 'create-admin':
        address = args.email or input('Email administrateur : ')
        password = getpass.getpass('Mot de passe (14 caractères minimum) : ')
        if password != getpass.getpass('Confirmer le mot de passe : '):
            parser.error('Les mots de passe diffèrent.')
        service.add_admin(address, password)
        print('Compte administrateur créé.')
    elif args.command == 'migrate':
        print('Migrations appliquées.')
    elif args.command == 'flush-email':
        print(json.dumps(flush(service)))
    elif args.command == 'purge-closed':
        # Preview by default; retention is a configured association policy, not a legal assertion.
        import datetime
        cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=settings.retention_days)).isoformat(timespec='seconds')
        with service.transaction() as db:
            rows = db.execute("SELECT id,photo_path,card_path FROM applications WHERE status='refusee' AND updated_at<? AND NOT EXISTS (SELECT 1 FROM payments WHERE payments.application_id=applications.id)", (cutoff,)).fetchall()
            print(f'{len(rows)} dossiers refusés éligibles à la purge.')
            if args.confirm:
                for row in rows:
                    for table in ('downloads', 'outbox', 'audit', 'payments'):
                        db.execute(f'DELETE FROM {table} WHERE application_id=?', (row['id'],))
                    db.execute('DELETE FROM applications WHERE id=?', (row['id'],))
        if args.confirm:
            for row in rows:
                for key in ('photo_path', 'card_path'):
                    if row[key]:
                        service.storage.delete(row[key])
    elif args.command == 'serve-dev':
        if args.host not in ('127.0.0.1', 'localhost'):
            parser.error('Le serveur de développement reste sur le poste local.')
        class QuietHandler(WSGIRequestHandler):
            def log_message(self, format, *values):
                pass  # No applicant data or private URLs in access logs.
        print(f'Aperçu local : http://{args.host}:{args.port}/adhesion/', flush=True)
        with make_server(args.host, args.port, Application(settings), handler_class=QuietHandler) as server:
            server.serve_forever()
    else:
        from waitress import serve
        if args.command == 'manage-local':
            with contextlib.closing(service.connection()) as db:
                needs_admin = db.execute('SELECT 1 FROM admins LIMIT 1').fetchone() is None
            if needs_admin:
                print('Première ouverture : protège l’administration locale avec ton email et un mot de passe.')
                address = input('Ton email : ')
                password = getpass.getpass('Mot de passe (14 caractères minimum) : ')
                if password != getpass.getpass('Confirmer le mot de passe : '):
                    parser.error('Les mots de passe diffèrent.')
                service.add_admin(address, password)
            print(f'Gestion locale : {settings.origin}/admin/adhesions/\nGarde cette fenêtre ouverte pendant l’utilisation.', flush=True)
            webbrowser.open(settings.origin + '/admin/adhesions/')
        bootstrap_email = os.environ.get('LNH_BOOTSTRAP_ADMIN_EMAIL', '')
        bootstrap_password = os.environ.get('LNH_BOOTSTRAP_ADMIN_PASSWORD', '')
        if bootstrap_email or bootstrap_password:
            if not bootstrap_email or not bootstrap_password:
                parser.error('Configurer les deux paramètres privés du premier administrateur.')
            service.bootstrap_admin(bootstrap_email, bootstrap_password)
        proxy = os.environ.get('LNH_TRUSTED_PROXY')
        proxy_options = ({'trusted_proxy': proxy, 'trusted_proxy_count': 1,
                          'trusted_proxy_headers': {'x-forwarded-for', 'x-forwarded-proto'}}
                         if proxy else {})
        serve(Application(settings), host=args.host, port=args.port, threads=4,
              **proxy_options,
              clear_untrusted_proxy_headers=True,
              max_request_body_size=settings.max_body, channel_timeout=30,
              expose_tracebacks=False)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
