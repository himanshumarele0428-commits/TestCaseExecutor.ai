import logging
from cryptography.fernet import Fernet, InvalidToken
from app.config import get_settings

logger = logging.getLogger(__name__)
_generated_key: bytes | None = None


def _get_or_create_key() -> bytes:
    global _generated_key
    if _generated_key is not None:
        return _generated_key

    settings = get_settings()
    key_str = settings.FERNET_KEY

    if key_str:
        try:
            key_bytes = key_str.encode()
            Fernet(key_bytes)
            _generated_key = key_bytes
            return _generated_key
        except Exception:
            pass

    _generated_key = Fernet.generate_key()
    return _generated_key


def encrypt_value(value: str) -> str:
    f = Fernet(_get_or_create_key())
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    f = Fernet(_get_or_create_key())
    try:
        return f.decrypt(encrypted.encode()).decode()
    except InvalidToken:
        logger.warning("Failed to decrypt value: Fernet key may have changed")
        raise ValueError("Encrypted value cannot be decrypted (key mismatch)")
