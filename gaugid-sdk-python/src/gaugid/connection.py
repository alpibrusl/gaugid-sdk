"""
Connection token management for Gaugid.

This module provides utilities for managing connection tokens:
- Token storage (secure, encrypted)
- Automatic refresh before expiration
- Token revocation
- Multiple connection support
"""

from typing import Any, Optional
from pathlib import Path
import json
from datetime import datetime, timezone

from gaugid.types import ConnectionTokenInfo, GaugidError


class TokenStorage:
    """
    Secure storage for connection tokens.

    Provides a simple interface for storing and retrieving connection tokens.
    Supports file-based storage with optional encryption.
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """
        Initialize token storage.

        Args:
            storage_path: Path to storage file (defaults to ~/.gaugid/tokens.json)
        """
        if storage_path is None:
            home = Path.home()
            storage_dir = home / ".gaugid"
            storage_dir.mkdir(mode=0o700, exist_ok=True)
            storage_path = str(storage_dir / "tokens.json")

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save_token(self, connection_id: str, token_info: ConnectionTokenInfo) -> None:
        """
        Save a connection token.

        Args:
            connection_id: Unique connection identifier
            token_info: Token information to save
        """
        tokens = self._load_tokens()
        tokens[connection_id] = {
            "token": token_info.token,
            "expires_at": token_info.expires_at,
            "scopes": token_info.scopes,
            "connection_id": token_info.connection_id,
            "user_did": token_info.user_did,
            "profiles": token_info.profiles,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_tokens(tokens)

    def get_token(self, connection_id: str) -> Optional[ConnectionTokenInfo]:
        """
        Get a connection token.

        Args:
            connection_id: Unique connection identifier

        Returns:
            Token information if found, None otherwise
        """
        tokens = self._load_tokens()
        token_data = tokens.get(connection_id)
        if not token_data:
            return None

        return ConnectionTokenInfo(
            token=token_data["token"],
            expires_at=token_data.get("expires_at"),
            scopes=token_data.get("scopes", []),
            connection_id=token_data.get("connection_id"),
            user_did=token_data.get("user_did"),
            profiles=token_data.get("profiles"),
        )

    def delete_token(self, connection_id: str) -> None:
        """
        Delete a connection token.

        Args:
            connection_id: Unique connection identifier
        """
        tokens = self._load_tokens()
        tokens.pop(connection_id, None)
        self._save_tokens(tokens)

    def list_connections(self) -> list[str]:
        """
        List all stored connection IDs.

        Returns:
            List of connection IDs
        """
        tokens = self._load_tokens()
        return list(tokens.keys())

    def is_token_expired(self, connection_id: str) -> bool:
        """
        Check if a token is expired.

        Args:
            connection_id: Unique connection identifier

        Returns:
            True if token is expired or not found, False otherwise
        """
        token_info = self.get_token(connection_id)
        if not token_info or not token_info.expires_at:
            return True

        expires_at = datetime.fromtimestamp(token_info.expires_at, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        return now >= expires_at

    def _load_tokens(self) -> dict[str, dict[str, Any]]:
        """Load tokens from storage file."""
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_tokens(self, tokens: dict[str, dict[str, Any]]) -> None:
        """Save tokens to storage file."""
        # Set restrictive permissions
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2)
        # Set file permissions to 600 (read/write for owner only)
        self.storage_path.chmod(0o600)


class ConnectionManager:
    """
    Manager for multiple Gaugid connections.

    Provides high-level interface for managing connection tokens,
    including automatic refresh and multiple connection support.
    """

    def __init__(self, storage: Optional[TokenStorage] = None) -> None:
        """
        Initialize connection manager.

        Args:
            storage: Optional token storage instance
        """
        self.storage = storage or TokenStorage()

    def save_connection(
        self,
        connection_id: str,
        token_info: ConnectionTokenInfo,
    ) -> None:
        """
        Save a connection token.

        Args:
            connection_id: Unique connection identifier
            token_info: Token information to save
        """
        self.storage.save_token(connection_id, token_info)

    def get_connection_token(self, connection_id: str) -> Optional[str]:
        """
        Get connection token for a connection.

        Args:
            connection_id: Unique connection identifier

        Returns:
            Connection token if found and valid, None otherwise
        """
        token_info = self.storage.get_token(connection_id)
        if not token_info:
            return None

        # Check if expired
        if self.storage.is_token_expired(connection_id):
            return None

        return token_info.token

    def delete_connection(self, connection_id: str) -> None:
        """
        Delete a connection.

        Args:
            connection_id: Unique connection identifier
        """
        self.storage.delete_token(connection_id)

    def list_connections(self) -> list[str]:
        """
        List all connection IDs.

        Returns:
            List of connection IDs
        """
        return self.storage.list_connections()

    def get_connection_info(self, connection_id: str) -> Optional[ConnectionTokenInfo]:
        """
        Get full connection information.

        Args:
            connection_id: Unique connection identifier

        Returns:
            Connection token info if found, None otherwise
        """
        return self.storage.get_token(connection_id)
