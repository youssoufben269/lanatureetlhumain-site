import argparse
import contextlib
import getpass
import json
import logging
import os
import time
from pathlib import Path
from wsgiref.simple_server import make_server, WSGIRequestHandler

from .config import Settings
from .mail import flush
from .service import Service
from .web import Application


def main():
    parser = argparse.ArgumentParser(description='Administration du module adhésion LNH')
    parser.add_argument('command', choices=('migrate', 'create-admin', 'serve-dev', 'serve', 'flush-email', 'purge-closed'))
    parser.add_argument('--email')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--confirm', action='store_true', help='Confirmer la suppression des dossiers refusés expirés')
    args = parser.parse_args()
    settings = Settings.from_env()
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
                        (settings.data / row[key]).unlink(missing_ok=True)
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
