"""Durable outbox; sending is explicitly enabled by SMTP configuration and the CLI worker."""
import json
import os
import smtplib
import ssl
import time
from datetime import datetime
from email.message import EmailMessage
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from .service import now
from .security import digest, email


def _message(row, data, sender):
    subjects = {'reception': 'Demande d’adhésion reçue', 'validation': 'Adhésion validée', 'refus': 'Suite à votre demande d’adhésion', 'carte': 'Votre carte de membre est disponible'}
    bodies = {
        'reception': 'Nous avons bien reçu votre demande d’adhésion. L’association examinera votre dossier et vous informera des suites données.',
        'validation': 'Votre adhésion est validée et votre paiement confirmé. Votre numéro de membre : ' + data.get('number', '') + '. La carte sera disponible après sa génération.',
        'refus': 'L’association n’a pas retenu votre demande. Motif : ' + data.get('reason', ''),
        'carte': 'Votre carte ' + data.get('number', '') + ' est disponible. Ce lien privé est valable 7 jours à compter de cet envoi, tant que votre adhésion reste active :\n' + data.get('link', '') + '\nNe partagez pas ce lien.',
    }
    msg = EmailMessage()
    msg['From'], msg['To'], msg['Subject'] = sender, row['recipient'], subjects[row['kind']]
    msg['Message-ID'] = f'<lnh-outbox-{row["id"]}@{sender.split("@")[1]}>'
    msg.set_content(bodies[row['kind']] + '\n\nLa Nature et l’Humain\nRÉSEAUX · PARTENARIATS · SOLUTIONS')
    return msg


def _send(msg, host, transport):
    if transport is not None:
        transport(msg)
        return
    port = int(os.environ.get('LNH_SMTP_PORT', '465'))
    context = ssl.create_default_context()
    mode = os.environ.get('LNH_SMTP_SECURITY', 'ssl')
    if mode not in ('ssl', 'starttls'):
        raise ValueError('SMTP chiffré obligatoire.')
    # Socket operations time out after 30 seconds; this is not a total SMTP deadline.
    with (smtplib.SMTP_SSL(host, port, timeout=30, context=context) if mode == 'ssl' else smtplib.SMTP(host, port, timeout=30)) as smtp:
        if mode == 'starttls':
            smtp.starttls(context=context)
        if os.environ.get('LNH_SMTP_USER'):
            smtp.login(os.environ['LNH_SMTP_USER'], os.environ['LNH_SMTP_PASSWORD'])
        smtp.send_message(msg)


def flush(service, transport=None):
    host = os.environ.get('LNH_SMTP_HOST', '')
    if not host and transport is None:
        return {'enabled': False, 'sent': 0, 'failed': 0}
    sender = email(os.environ.get('LNH_SMTP_FROM', 'contact@lanatureetlhumain.org'))
    sent = failed = 0
    while True:
        stamp = int(time.time())
        with service.transaction() as db:
            db.execute("UPDATE outbox SET state='pending' WHERE state='processing' AND available_at<?", (stamp,))
            row = db.execute("SELECT * FROM outbox WHERE state='pending' AND available_at<=? ORDER BY id LIMIT 1", (stamp,)).fetchone()
            if not row:
                break
            db.execute("UPDATE outbox SET state='processing',available_at=?,attempts=attempts+1 WHERE id=?", (stamp + 300, row['id']))
        claim_id, application_id, attempt = row['id'], row['application_id'], row['attempts'] + 1
        try:
            # The database-wide writer lock also serializes Service.change(refuse).
            # Low-volume trade-off: other writes wait during SMTP. A refusal committed
            # first cancels delivery; once transport starts, refusal waits and cannot
            # recall that email. A crash after SMTP acceptance may still cause a retry.
            with service.transaction() as db:
                row = db.execute("""SELECT o.*,a.status AS member_status,a.expires_on AS member_expires
                                    FROM outbox o JOIN applications a ON a.id=o.application_id
                                    WHERE o.id=? AND o.application_id=? AND o.state='processing' AND o.attempts=?""",
                                 (claim_id, application_id, attempt)).fetchone()
                if not row:
                    continue  # Cancelled, deleted, or reclaimed by a newer worker.
                stamp = int(time.time())
                today = datetime.fromtimestamp(stamp, ZoneInfo(service.cfg.timezone)).date().isoformat()
                if (row['kind'] == 'validation' and row['member_status'] not in ('validee', 'carte_generee')) or (
                    row['kind'] == 'carte' and (row['member_status'] != 'carte_generee' or (row['member_expires'] or '') < today)
                ):
                    db.execute("UPDATE outbox SET state='cancelled' WHERE id=?", (claim_id,))
                    continue
                data = json.loads(row['payload'])
                msg = _message(row, data, sender)
                if row['kind'] == 'carte':
                    tokens = parse_qs(urlsplit(data.get('link', '')).fragment).get('token', [])
                    if len(tokens) != 1 or not 20 <= len(tokens[0]) <= 100:
                        raise ValueError('Lien de carte incorrect.')
                    # Renew only an existing grant belonging to this application.
                    # Never recreate a revoked token, or log the payload/token.
                    updated = db.execute('UPDATE downloads SET expires_at=? WHERE token_hash=? AND application_id=?',
                                         (stamp + 7 * 86400, digest(tokens[0]), application_id))
                    if updated.rowcount != 1:
                        db.execute("UPDATE outbox SET state='cancelled' WHERE id=?", (claim_id,))
                        continue
                _send(msg, host, transport)
                db.execute("UPDATE outbox SET state='sent',sent_at=?,payload='{}' WHERE id=?", (now(), claim_id))
            sent += 1
        except Exception:
            # Rollback also restores the previous token expiry on a failed send.
            # Fence retries with the claim's attempt so a stale worker cannot
            # overwrite a cancellation or another worker's reservation.
            with service.transaction() as db:
                db.execute("""UPDATE outbox SET state='pending',available_at=?
                              WHERE id=? AND application_id=? AND state='processing' AND attempts=?""",
                           (int(time.time()) + min(3600, 60 * 2 ** min(attempt - 1, 6)), claim_id, application_id, attempt))
            failed += 1
    return {'enabled': True, 'sent': sent, 'failed': failed}
