import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Settings:
    root: Path = ROOT
    data: Path = field(default_factory=lambda: Path(os.environ.get('LNH_DATA_DIR', ROOT / 'var')).resolve())
    origin: str = field(default_factory=lambda: os.environ.get('LNH_MODULE_ORIGIN', 'http://127.0.0.1:8787').rstrip('/'))
    website: str = 'https://www.lanatureetlhumain.org'
    allowed_origins: tuple = ()
    secure_cookies: bool = False
    categories: tuple = ('actif', 'sympathisant', 'institutionnel')
    fee_minor: int | None = None
    currency: str = 'EUR'
    validity_months: int = 12
    qr_mode: str = 'website'
    public_verification: bool = False
    privacy_contact: str = 'contact@lanatureetlhumain.org'
    retention_days: int = 90
    max_body: int = 4_400_000
    session_seconds: int = 28_800
    timezone: str = 'Indian/Comoro'

    @classmethod
    def from_env(cls):
        origin = os.environ.get('LNH_MODULE_ORIGIN', 'http://127.0.0.1:8787').rstrip('/')
        fee = os.environ.get('LNH_FEE_MINOR', '').strip()
        obj = cls(origin=origin, secure_cookies=origin.startswith('https://'),
                  website=os.environ.get('LNH_WEBSITE_URL', 'https://www.lanatureetlhumain.org').rstrip('/'),
                  allowed_origins=tuple(filter(None, os.environ.get('LNH_ALLOWED_ORIGINS', '').split(','))),
                  categories=tuple(os.environ.get('LNH_CATEGORIES', 'actif,sympathisant,institutionnel').split(',')),
                  fee_minor=int(fee) if fee else None, currency=os.environ.get('LNH_CURRENCY', 'EUR'),
                  validity_months=int(os.environ.get('LNH_VALIDITY_MONTHS', '12')),
                  qr_mode=os.environ.get('LNH_QR_MODE', 'website'),
                  public_verification=os.environ.get('LNH_PUBLIC_VERIFICATION') == '1',
                  privacy_contact=os.environ.get('LNH_PRIVACY_CONTACT', 'contact@lanatureetlhumain.org'),
                  retention_days=int(os.environ.get('LNH_RETENTION_DAYS', '90')),
                  timezone=os.environ.get('LNH_TIMEZONE', 'Indian/Comoro'))
        obj.validate()
        return obj

    def validate(self):
        ZoneInfo(self.timezone)
        for url in (self.origin, self.website, *self.allowed_origins):
            parts = urlsplit(url)
            if parts.scheme not in ('http', 'https') or not parts.netloc or parts.username or parts.path not in ('', '/') or parts.query or parts.fragment:
                raise ValueError('Utiliser des origines complètes sans chemin ni paramètres.')
            if parts.scheme != 'https' and parts.hostname not in ('127.0.0.1', 'localhost'):
                raise ValueError('HTTPS obligatoire hors poste local.')
        if not self.categories or any(not x or len(x) > 60 for x in self.categories):
            raise ValueError('Catégories incorrectes.')
        if self.fee_minor is not None and self.fee_minor <= 0:
            raise ValueError('Le droit doit être positif et exprimé en unité monétaire minimale.')
        if len(self.currency) != 3 or not self.currency.isalpha() or self.currency != self.currency.upper():
            raise ValueError('Devise ISO requise.')
        if not 1 <= self.validity_months <= 120 or not 1 <= self.retention_days <= 3650:
            raise ValueError('Durées incorrectes.')
        if self.qr_mode not in ('website', 'member') or (self.qr_mode == 'member' and not self.public_verification):
            raise ValueError('Activer la vérification publique avant le QR individuel.')
