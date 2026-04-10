"""Load or create the application master key for secret encryption (moonshot_config)."""

from __future__ import annotations

import base64
import secrets

from application.ports.moonshot_config_repository import MoonshotConfigRepository
from domain.services.secret_encryption import MOONSHOT_SECRETS_MASTER_KEY_CONFIG_KEY


class SecretsMasterKeyService:
    def __init__(self, moonshot_config: MoonshotConfigRepository) -> None:
        self._moonshot_config = moonshot_config

    def get_or_create_master_key_bytes(self) -> bytes:
        entity = self._moonshot_config.get_by_key(MOONSHOT_SECRETS_MASTER_KEY_CONFIG_KEY)
        if entity and entity.value:
            raw = base64.b64decode(entity.value.encode("ascii"), validate=True)
            if len(raw) != 32:
                raise ValueError(
                    f"moonshot_config[{MOONSHOT_SECRETS_MASTER_KEY_CONFIG_KEY!r}] must decode to 32 bytes"
                )
            return raw
        raw = secrets.token_bytes(32)
        b64 = base64.b64encode(raw).decode("ascii")
        self._moonshot_config.set(MOONSHOT_SECRETS_MASTER_KEY_CONFIG_KEY, b64)
        return raw
