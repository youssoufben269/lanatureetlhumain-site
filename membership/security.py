import base64
import hashlib
import hmac
import re
import secrets


class Problem(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status
        super().__init__(message)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password):
    if len(password) < 14 or len(password) > 256 or not password.strip():
        raise Problem('Choisissez un mot de passe de 14 à 256 caractères.')
    salt = secrets.token_bytes(16)
    value = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return 'scrypt$' + base64.b64encode(salt).decode() + '$' + base64.b64encode(value).decode()


def verify_password(password, encoded):
    try:
        method, salt, expected = encoded.split('$')
        if method != 'scrypt' or len(password) > 256:
            return False
        value = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=16384, r=8, p=1)
        return hmac.compare_digest(value, base64.b64decode(expected))
    except (ValueError, TypeError):
        return False


def clean(value, field, maximum, required=True):
    if not isinstance(value, str):
        raise Problem(f'Champ incorrect : {field}.')
    value = value.strip()
    if (required and not value) or len(value) > maximum or any(ord(x) < 32 and x not in '\n\t' for x in value):
        raise Problem(f'Champ incorrect : {field} (maximum {maximum} caractères).')
    return value


def email(value):
    value = clean(value, 'email', 254).lower()
    if not re.fullmatch(r'[^\s<>@\r\n]+@[^\s<>@\r\n]+\.[^\s<>@\r\n]+', value):
        raise Problem('Adresse email incorrecte.')
    return value
