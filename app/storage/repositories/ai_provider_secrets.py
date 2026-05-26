from datetime import UTC, datetime

from cryptography.fernet import InvalidToken
from sqlalchemy.orm import Session

from app.services.secret_crypto import SecretCryptoService
from app.storage.tables import AIProviderSecretRow


class AIProviderSecretRepository:
    def __init__(self, session: Session, crypto: SecretCryptoService):
        self.session = session
        self.crypto = crypto

    def has_secret(self, secret_name: str) -> bool:
        row = self.session.get(AIProviderSecretRow, secret_name)
        return bool(row and row.encrypted_value)

    def get_secret(self, secret_name: str) -> str | None:
        row = self.session.get(AIProviderSecretRow, secret_name)
        if row is None:
            return None
        try:
            return self.crypto.decrypt(row.encrypted_value)
        except InvalidToken:
            return None

    def set_secret(
        self,
        *,
        secret_name: str,
        value: str,
        updated_by_user_id: str | None,
    ) -> AIProviderSecretRow:
        row = self.session.get(AIProviderSecretRow, secret_name)
        now = datetime.now(UTC)
        if row is None:
            row = AIProviderSecretRow(secret_name=secret_name, encrypted_value="")
            row.created_at = now
        row.encrypted_value = self.crypto.encrypt(value)
        row.updated_by_user_id = updated_by_user_id
        row.updated_at = now
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def clear_secret(self, secret_name: str) -> bool:
        row = self.session.get(AIProviderSecretRow, secret_name)
        if row is None:
            return False
        self.session.delete(row)
        self.session.commit()
        return True

