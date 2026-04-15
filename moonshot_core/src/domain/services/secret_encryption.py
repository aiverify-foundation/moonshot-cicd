"""AES-256-GCM encryption for LLM provider API keys (per-row salt, HKDF from app master key)."""

from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# moonshot_config row key for the 32-byte master secret (stored as standard Base64 text).
MOONSHOT_SECRETS_MASTER_KEY_CONFIG_KEY = "moonshot_secrets_master_key_b64"

# Pre-encryption placeholder in llm_provider_api_key.salt/nonce/authentication_tag.
LEGACY_API_KEY_STORAGE_PLACEHOLDER = "unused"

HKDF_INFO = b"moonshot-v1-llm-api-key"
_SALT_LEN = 32
_NONCE_LEN = 12
_AES_KEY_LEN = 32
_TAG_LEN = 16


class LegacyApiKeyStorageError(Exception):
    """Stored row uses legacy placeholders; user must re-save the API key."""


class SecretDecryptionError(Exception):
    """Decryption failed (wrong key, tampered ciphertext, or corrupt encoding)."""


@dataclass(frozen=True)
class EncryptedApiKeyFields:
    """Base64-encoded ciphertext, salt, nonce, and GCM tag for DB columns."""

    encrypted_key: str
    salt: str
    nonce: str
    authentication_tag: str


def is_legacy_row(salt: str, nonce: str, authentication_tag: str) -> bool:
    p = LEGACY_API_KEY_STORAGE_PLACEHOLDER
    return salt == p or nonce == p or authentication_tag == p


def _derive_aes_key(master_key: bytes, salt: bytes) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=_AES_KEY_LEN,
        salt=salt,
        info=HKDF_INFO,
    )
    return hkdf.derive(master_key)


def encrypt_api_key(plaintext: str, master_key: bytes) -> EncryptedApiKeyFields:
    if len(master_key) != _AES_KEY_LEN:
        raise ValueError("master_key must be 32 bytes")
    salt = secrets.token_bytes(_SALT_LEN)
    nonce = secrets.token_bytes(_NONCE_LEN)
    aes_key = _derive_aes_key(master_key, salt)
    aesgcm = AESGCM(aes_key)
    pt = plaintext.encode("utf-8")
    ct_with_tag = aesgcm.encrypt(nonce, pt, None)
    ciphertext, tag = ct_with_tag[:-_TAG_LEN], ct_with_tag[-_TAG_LEN:]
    if len(tag) != _TAG_LEN:
        raise RuntimeError("unexpected GCM tag length")
    return EncryptedApiKeyFields(
        encrypted_key=base64.b64encode(ciphertext).decode("ascii"),
        salt=base64.b64encode(salt).decode("ascii"),
        nonce=base64.b64encode(nonce).decode("ascii"),
        authentication_tag=base64.b64encode(tag).decode("ascii"),
    )


def decrypt_api_key(
    encrypted_key_b64: str,
    salt_b64: str,
    nonce_b64: str,
    authentication_tag_b64: str,
    master_key: bytes,
) -> str:
    if is_legacy_row(salt_b64, nonce_b64, authentication_tag_b64):
        raise LegacyApiKeyStorageError(
            "API key row uses legacy storage; re-save the key in the UI or API."
        )
    try:
        salt = base64.b64decode(salt_b64.encode("ascii"), validate=True)
        nonce = base64.b64decode(nonce_b64.encode("ascii"), validate=True)
        ciphertext = base64.b64decode(encrypted_key_b64.encode("ascii"), validate=True)
        tag = base64.b64decode(authentication_tag_b64.encode("ascii"), validate=True)
    except (ValueError, TypeError) as e:
        raise SecretDecryptionError("invalid Base64 in stored API key fields") from e
    if len(master_key) != _AES_KEY_LEN:
        raise ValueError("master_key must be 32 bytes")
    aes_key = _derive_aes_key(master_key, salt)
    aesgcm = AESGCM(aes_key)
    try:
        pt = aesgcm.decrypt(nonce, ciphertext + tag, None)
    except InvalidTag as e:
        raise SecretDecryptionError("API key decryption failed") from e
    return pt.decode("utf-8")
