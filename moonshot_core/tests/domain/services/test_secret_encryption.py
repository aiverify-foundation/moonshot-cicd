"""Tests for AES-GCM API key encryption helpers."""

from __future__ import annotations

import base64

import pytest

from domain.services.secret_encryption import (
    LEGACY_API_KEY_STORAGE_PLACEHOLDER,
    LegacyApiKeyStorageError,
    SecretDecryptionError,
    decrypt_api_key,
    encrypt_api_key,
    is_legacy_row,
)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


@pytest.fixture
def master_key() -> bytes:
    return b"x" * 32


class TestSecretEncryption:
    def test_round_trip(self, master_key):
        fields = encrypt_api_key("sk-test-secret", master_key)
        assert fields.encrypted_key != "sk-test-secret"
        out = decrypt_api_key(
            fields.encrypted_key,
            fields.salt,
            fields.nonce,
            fields.authentication_tag,
            master_key,
        )
        assert out == "sk-test-secret"

    def test_unique_salt_per_encrypt(self, master_key):
        a = encrypt_api_key("same", master_key)
        b = encrypt_api_key("same", master_key)
        assert a.salt != b.salt
        assert a.nonce != b.nonce

    def test_wrong_master_key_fails(self, master_key):
        fields = encrypt_api_key("secret", master_key)
        other = b"y" * 32
        with pytest.raises(SecretDecryptionError, match="decryption failed"):
            decrypt_api_key(
                fields.encrypted_key,
                fields.salt,
                fields.nonce,
                fields.authentication_tag,
                other,
            )

    def test_tampered_tag_fails(self, master_key):
        fields = encrypt_api_key("secret", master_key)
        tag_bytes = bytearray(base64.b64decode(fields.authentication_tag.encode("ascii")))
        tag_bytes[0] ^= 0xFF
        bad_tag = _b64(bytes(tag_bytes))
        with pytest.raises(SecretDecryptionError, match="decryption failed"):
            decrypt_api_key(
                fields.encrypted_key,
                fields.salt,
                fields.nonce,
                bad_tag,
                master_key,
            )

    def test_legacy_row_raises(self, master_key):
        with pytest.raises(LegacyApiKeyStorageError, match="legacy"):
            decrypt_api_key("anything", LEGACY_API_KEY_STORAGE_PLACEHOLDER, "a", "b", master_key)

    def test_is_legacy_row(self):
        p = LEGACY_API_KEY_STORAGE_PLACEHOLDER
        assert is_legacy_row(p, "a", "b") is True
        assert is_legacy_row("a", p, "b") is True
        assert is_legacy_row("a", "b", p) is True
        assert is_legacy_row("a", "b", "c") is False

    def test_invalid_b64_raises(self, master_key):
        with pytest.raises(SecretDecryptionError, match="Base64"):
            decrypt_api_key("not!!!", _b64(b"s" * 32), _b64(b"n" * 12), _b64(b"t" * 16), master_key)
