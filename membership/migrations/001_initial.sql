CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY);
CREATE TABLE admins(
 id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1))
);
CREATE TABLE sessions(
 token_hash TEXT PRIMARY KEY, admin_id TEXT NOT NULL REFERENCES admins(id),
 csrf TEXT NOT NULL, expires_at INTEGER NOT NULL
);
CREATE TABLE applications(
 id TEXT PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
 email TEXT NOT NULL UNIQUE COLLATE NOCASE, phone TEXT NOT NULL,
 address TEXT NOT NULL DEFAULT '', city TEXT NOT NULL DEFAULT '', country TEXT NOT NULL DEFAULT '',
 profession TEXT NOT NULL DEFAULT '', function TEXT NOT NULL DEFAULT '', category TEXT NOT NULL, motivation TEXT NOT NULL DEFAULT '',
 photo_path TEXT NOT NULL UNIQUE, consent_at TEXT NOT NULL, consent_version TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('soumise','en_attente_de_paiement','en_attente_de_validation','validee','refusee','carte_generee')),
 approved_at TEXT, approved_by TEXT REFERENCES admins(id), refusal_reason TEXT,
 member_number TEXT UNIQUE, joined_on TEXT, expires_on TEXT,
 card_path TEXT UNIQUE, card_url TEXT, card_error TEXT,
 version INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 CHECK(member_number IS NULL OR (approved_at IS NOT NULL AND joined_on IS NOT NULL AND expires_on IS NOT NULL))
);
CREATE TABLE payments(
 application_id TEXT PRIMARY KEY REFERENCES applications(id), provider TEXT NOT NULL,
 amount_minor INTEGER NOT NULL CHECK(amount_minor > 0), currency TEXT NOT NULL,
 reference TEXT NOT NULL, confirmed_at TEXT NOT NULL, confirmed_by TEXT NOT NULL REFERENCES admins(id)
);
CREATE TABLE sequences(year INTEGER PRIMARY KEY, value INTEGER NOT NULL CHECK(value > 0));
CREATE TABLE audit(
 id INTEGER PRIMARY KEY, application_id TEXT NOT NULL REFERENCES applications(id),
 actor TEXT NOT NULL, action TEXT NOT NULL, old_status TEXT, new_status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX audit_application ON audit(application_id,id);
CREATE TABLE downloads(
 token_hash TEXT PRIMARY KEY, application_id TEXT NOT NULL REFERENCES applications(id), expires_at INTEGER NOT NULL
);
CREATE TABLE outbox(
 id INTEGER PRIMARY KEY, application_id TEXT NOT NULL REFERENCES applications(id),
 kind TEXT NOT NULL, recipient TEXT NOT NULL, payload TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0,
 available_at INTEGER NOT NULL DEFAULT 0, sent_at TEXT,
 UNIQUE(application_id,kind)
);
CREATE TABLE rate_limits(key TEXT PRIMARY KEY, count INTEGER NOT NULL, expires_at INTEGER NOT NULL);
INSERT INTO schema_migrations VALUES(1);
