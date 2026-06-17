"""Fernet 对称加密 — 用于 API Key 和网站密码的本地加密存储。"""
from pathlib import Path
from cryptography.fernet import Fernet
from config import KEY_PATH


def _load_or_create_key() -> bytes:
    if KEY_PATH.exists():
        return KEY_PATH.read_bytes()
    key = Fernet.generate_key()
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    KEY_PATH.write_bytes(key)
    return key


def _fernet() -> Fernet:
    return Fernet(_load_or_create_key())


def encrypt(plain_text: str) -> str:
    if not plain_text:
        return ""
    return _fernet().encrypt(plain_text.encode()).decode()


def decrypt(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    try:
        return _fernet().decrypt(cipher_text.encode()).decode()
    except Exception:
        return ""
