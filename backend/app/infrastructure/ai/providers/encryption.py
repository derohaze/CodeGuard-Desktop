from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    # Derive stable key from mongodb_uri + app_name, not stored in code
    raw = f"{settings.mongodb_uri}:{settings.app_name}:provider-key-v1".encode()
    digest = hashlib.sha256(raw).digest()  # 32 bytes
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_api_key(plain: str) -> str:
    if not plain:
        return ""
    f = _get_fernet()
    return f.encrypt(plain.encode()).decode()


def decrypt_api_key(token: str) -> str:
    if not token:
        return ""
    f = _get_fernet()
    try:
        return f.decrypt(token.encode()).decode()
    except InvalidToken:
        # Fallback: token might be plain (migration from env)
        return token


def mask_api_key(plain: str) -> str:
    if not plain or len(plain) < 8:
        return "****"
    return f"{plain[:4]}****{plain[-4:]}"
