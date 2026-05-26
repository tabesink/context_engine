import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import Settings


class SecretCryptoService:
    def __init__(self, key_material: str):
        self._fernet = Fernet(_fernet_key(key_material))

    @classmethod
    def from_settings(cls, settings: Settings) -> "SecretCryptoService":
        return cls(settings.ai_secret_encryption_key or settings.secret_key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")


def _fernet_key(key_material: str) -> bytes:
    raw = key_material.strip()
    if raw:
        try:
            decoded = base64.urlsafe_b64decode(raw.encode("ascii"))
            if len(decoded) == 32:
                return raw.encode("ascii")
        except Exception:
            pass
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)

