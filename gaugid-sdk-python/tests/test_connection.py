"""Tests for connection token management."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, mock_open
from gaugid.connection import TokenStorage, ConnectionManager
from gaugid.types import ConnectionTokenInfo


def test_token_storage_init_default_path() -> None:
    """Test TokenStorage initialization with default path."""
    with patch("pathlib.Path.home") as mock_home:
        mock_home.return_value = Path("/home/test")
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            storage = TokenStorage()
            assert storage.storage_path == Path("/home/test/.gaugid/tokens.json")
            mock_mkdir.assert_called()


def test_token_storage_init_custom_path() -> None:
    """Test TokenStorage initialization with custom path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "custom_tokens.json")
        storage = TokenStorage(storage_path=storage_path)
        assert storage.storage_path == Path(storage_path)


def test_token_storage_save_token() -> None:
    """Test saving a token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        token_info = ConnectionTokenInfo(
            token="token_123",
            expires_at=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            scopes=["a2p:preferences"],
            connection_id="conn_123",
            user_did="did:a2p:user:gaugid:alice",
        )

        storage.save_token("conn_123", token_info)

        # Verify token was saved
        saved_token = storage.get_token("conn_123")
        assert saved_token is not None
        assert saved_token.token == "token_123"
        assert saved_token.connection_id == "conn_123"
        assert saved_token.user_did == "did:a2p:user:gaugid:alice"


def test_token_storage_get_token() -> None:
    """Test getting a token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        token_info = ConnectionTokenInfo(
            token="token_123",
            expires_at=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            scopes=["a2p:preferences"],
        )

        storage.save_token("conn_123", token_info)
        retrieved = storage.get_token("conn_123")

        assert retrieved is not None
        assert retrieved.token == "token_123"
        assert retrieved.scopes == ["a2p:preferences"]


def test_token_storage_get_token_not_found() -> None:
    """Test getting a token that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        result = storage.get_token("nonexistent")
        assert result is None


def test_token_storage_delete_token() -> None:
    """Test deleting a token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        token_info = ConnectionTokenInfo(token="token_123")
        storage.save_token("conn_123", token_info)

        # Verify it exists
        assert storage.get_token("conn_123") is not None

        # Delete it
        storage.delete_token("conn_123")

        # Verify it's gone
        assert storage.get_token("conn_123") is None


def test_token_storage_delete_token_nonexistent() -> None:
    """Test deleting a token that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        # Should not raise error
        storage.delete_token("nonexistent")


def test_token_storage_list_connections() -> None:
    """Test listing all connections."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        # Save multiple tokens
        storage.save_token("conn_1", ConnectionTokenInfo(token="token_1"))
        storage.save_token("conn_2", ConnectionTokenInfo(token="token_2"))
        storage.save_token("conn_3", ConnectionTokenInfo(token="token_3"))

        connections = storage.list_connections()
        assert len(connections) == 3
        assert "conn_1" in connections
        assert "conn_2" in connections
        assert "conn_3" in connections


def test_token_storage_list_connections_empty() -> None:
    """Test listing connections when none exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        connections = storage.list_connections()
        assert connections == []


def test_token_storage_is_token_expired_not_found() -> None:
    """Test checking expiration for non-existent token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        assert storage.is_token_expired("nonexistent") is True


def test_token_storage_is_token_expired_no_expiration() -> None:
    """Test checking expiration for token without expiration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        token_info = ConnectionTokenInfo(token="token_123", expires_at=None)
        storage.save_token("conn_123", token_info)

        assert storage.is_token_expired("conn_123") is True


def test_token_storage_is_token_expired_valid() -> None:
    """Test checking expiration for valid token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        expires_at = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        token_info = ConnectionTokenInfo(
            token="token_123",
            expires_at=expires_at,
        )
        storage.save_token("conn_123", token_info)

        assert storage.is_token_expired("conn_123") is False


def test_token_storage_is_token_expired_expired() -> None:
    """Test checking expiration for expired token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)

        expires_at = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        token_info = ConnectionTokenInfo(
            token="token_123",
            expires_at=expires_at,
        )
        storage.save_token("conn_123", token_info)

        assert storage.is_token_expired("conn_123") is True


def test_token_storage_load_tokens_file_not_exists() -> None:
    """Test loading tokens when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "nonexistent.json")
        storage = TokenStorage(storage_path=storage_path)

        tokens = storage._load_tokens()
        assert tokens == {}


def test_token_storage_load_tokens_invalid_json() -> None:
    """Test loading tokens with invalid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "tokens.json"
        storage = TokenStorage(storage_path=str(storage_path))

        # Write invalid JSON
        storage_path.write_text("invalid json{", encoding="utf-8")

        tokens = storage._load_tokens()
        assert tokens == {}


def test_token_storage_save_tokens_permissions() -> None:
    """Test that saved tokens file has correct permissions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "tokens.json"
        storage = TokenStorage(storage_path=str(storage_path))

        token_info = ConnectionTokenInfo(token="token_123")
        storage.save_token("conn_123", token_info)

        # Check file permissions (should be 0o600)
        stat = storage_path.stat()
        assert oct(stat.st_mode)[-3:] == "600" or stat.st_mode & 0o777 == 0o600


def test_connection_manager_init() -> None:
    """Test ConnectionManager initialization."""
    manager = ConnectionManager()
    assert manager.storage is not None
    assert isinstance(manager.storage, TokenStorage)


def test_connection_manager_init_custom_storage() -> None:
    """Test ConnectionManager initialization with custom storage."""
    custom_storage = TokenStorage()
    manager = ConnectionManager(storage=custom_storage)
    assert manager.storage is custom_storage


def test_connection_manager_save_connection() -> None:
    """Test saving a connection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)
        manager = ConnectionManager(storage=storage)

        token_info = ConnectionTokenInfo(
            token="token_123",
            connection_id="conn_123",
        )

        manager.save_connection("conn_123", token_info)

        saved = manager.get_connection_info("conn_123")
        assert saved is not None
        assert saved.token == "token_123"


def test_connection_manager_get_connection_token() -> None:
    """Test getting connection token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)
        manager = ConnectionManager(storage=storage)

        expires_at = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        token_info = ConnectionTokenInfo(
            token="token_123",
            expires_at=expires_at,
        )

        manager.save_connection("conn_123", token_info)

        token = manager.get_connection_token("conn_123")
        assert token == "token_123"


def test_connection_manager_get_connection_token_not_found() -> None:
    """Test getting connection token that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)
        manager = ConnectionManager(storage=storage)

        token = manager.get_connection_token("nonexistent")
        assert token is None


def test_connection_manager_get_connection_token_expired() -> None:
    """Test getting connection token that is expired."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)
        manager = ConnectionManager(storage=storage)

        expires_at = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        token_info = ConnectionTokenInfo(
            token="token_123",
            expires_at=expires_at,
        )

        manager.save_connection("conn_123", token_info)

        token = manager.get_connection_token("conn_123")
        assert token is None  # Expired token returns None


def test_connection_manager_delete_connection() -> None:
    """Test deleting a connection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)
        manager = ConnectionManager(storage=storage)

        token_info = ConnectionTokenInfo(token="token_123")
        manager.save_connection("conn_123", token_info)

        assert manager.get_connection_info("conn_123") is not None

        manager.delete_connection("conn_123")

        assert manager.get_connection_info("conn_123") is None


def test_connection_manager_list_connections() -> None:
    """Test listing all connections."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)
        manager = ConnectionManager(storage=storage)

        manager.save_connection("conn_1", ConnectionTokenInfo(token="token_1"))
        manager.save_connection("conn_2", ConnectionTokenInfo(token="token_2"))

        connections = manager.list_connections()
        assert len(connections) == 2
        assert "conn_1" in connections
        assert "conn_2" in connections


def test_connection_manager_get_connection_info() -> None:
    """Test getting full connection info."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)
        manager = ConnectionManager(storage=storage)

        token_info = ConnectionTokenInfo(
            token="token_123",
            expires_at=int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            scopes=["a2p:preferences"],
            connection_id="conn_123",
            user_did="did:a2p:user:gaugid:alice",
            profiles=[{"id": "did:a2p:user:gaugid:alice", "name": "Personal"}],
        )

        manager.save_connection("conn_123", token_info)

        info = manager.get_connection_info("conn_123")
        assert info is not None
        assert info.token == "token_123"
        assert info.scopes == ["a2p:preferences"]
        assert info.user_did == "did:a2p:user:gaugid:alice"
        assert len(info.profiles) == 1


def test_connection_manager_get_connection_info_not_found() -> None:
    """Test getting connection info that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = str(Path(tmpdir) / "tokens.json")
        storage = TokenStorage(storage_path=storage_path)
        manager = ConnectionManager(storage=storage)

        info = manager.get_connection_info("nonexistent")
        assert info is None
