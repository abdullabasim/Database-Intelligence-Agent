import base64
from cryptography.fernet import Fernet
from app.core.config import get_settings

def _get_fernet() -> Fernet:
    settings = get_settings()
    # Fernet expects exactly 32 urlsafe base64-encoded bytes.
    return Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))

def encrypt_password(password: str) -> str:
    f = _get_fernet()
    encrypted = f.encrypt(password.encode('utf-8'))
    return encrypted.decode('utf-8')

def decrypt_password(encrypted_password: str) -> str:
    f = _get_fernet()
    decrypted = f.decrypt(encrypted_password.encode('utf-8'))
    return decrypted.decode('utf-8')
