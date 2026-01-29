"""Tests for GaugidStorage."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from gaugid.storage import GaugidStorage
from gaugid.types import GaugidAPIError, GaugidConnectionError


@pytest.mark.asyncio
async def test_gaugid_storage_init() -> None:
    """Test GaugidStorage initialization."""
    storage = GaugidStorage(connection_token="test_token")
    assert storage.connection_token == "test_token"
    assert storage.api_url == GaugidStorage.DEFAULT_API_URL
    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_custom_api_url() -> None:
    """Test GaugidStorage with custom API URL."""
    storage = GaugidStorage(
        connection_token="test_token",
        api_url="https://custom.api.com",
    )
    assert storage.api_url == "https://custom.api.com"
    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_get_profile() -> None:
    """Test getting profile."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    from a2p.storage.cloud import CloudStorage
    mock_profile = {"id": user_did, "profileType": "human", "identity": {"did": user_did}}

    with patch.object(CloudStorage, "get", new_callable=AsyncMock) as mock_parent_get:
        mock_parent_get.return_value = mock_profile

        result = await storage.get(user_did, scopes=["a2p:preferences"])

        assert result == mock_profile
        mock_parent_get.assert_called_once_with(user_did, ["a2p:preferences"])

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_get_profile_404() -> None:
    """Test getting profile that doesn't exist."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:nonexistent"

    with patch.object(storage, "_client") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        from a2p.storage.cloud import CloudStorage
        with patch.object(CloudStorage, "get", new_callable=AsyncMock) as mock_parent_get:
            mock_parent_get.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )

            result = await storage.get(user_did)

            assert result is None

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_get_profile_api_error() -> None:
    """Test getting profile with API error."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    with patch.object(storage, "_client") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "error": {"code": "A2P006", "message": "Internal error"}
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Error", request=MagicMock(), response=mock_response
        )

        from a2p.storage.cloud import CloudStorage
        with patch.object(CloudStorage, "get", new_callable=AsyncMock) as mock_parent_get:
            mock_parent_get.side_effect = httpx.HTTPStatusError(
                "Internal Error", request=MagicMock(), response=mock_response
            )

            with pytest.raises(GaugidAPIError):
                await storage.get(user_did)

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_set() -> None:
    """Test setting/updating profile."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    from a2p.types import Profile, ProfileType
    mock_profile = Profile(
        id=user_did,
        profileType=ProfileType.HUMAN,
        identity={"did": user_did},
    )

    from a2p.storage.cloud import CloudStorage
    with patch.object(CloudStorage, "set", new_callable=AsyncMock) as mock_parent_set:
        await storage.set(user_did, mock_profile)

        mock_parent_set.assert_called_once_with(user_did, mock_profile)

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_set_error() -> None:
    """Test setting profile with error."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    from a2p.types import Profile, ProfileType
    mock_profile = Profile(id=user_did, profileType=ProfileType.HUMAN, identity={"did": user_did})

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error": {"code": "A2P006", "message": "Invalid profile"}
    }
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=MagicMock(), response=mock_response
    )

    from a2p.storage.cloud import CloudStorage
    with patch.object(CloudStorage, "set", new_callable=AsyncMock) as mock_parent_set:
        mock_parent_set.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        with pytest.raises(GaugidAPIError):
            await storage.set(user_did, mock_profile)

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_delete() -> None:
    """Test deleting profile."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    from a2p.storage.cloud import CloudStorage
    with patch.object(CloudStorage, "delete", new_callable=AsyncMock) as mock_parent_delete:
        await storage.delete(user_did)

        mock_parent_delete.assert_called_once_with(user_did)

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_delete_error() -> None:
    """Test deleting profile with error."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {
        "error": {"code": "A2P002", "message": "Profile not found"}
    }
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=mock_response
    )

    from a2p.storage.cloud import CloudStorage
    with patch.object(CloudStorage, "delete", new_callable=AsyncMock) as mock_parent_delete:
        mock_parent_delete.side_effect = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with pytest.raises(GaugidAPIError):
            await storage.delete(user_did)

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_propose_memory() -> None:
    """Test proposing memory."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    mock_response = {
        "proposal_id": "prop_123",
        "status": "pending",
    }

    from a2p.storage.cloud import CloudStorage
    with patch.object(
        CloudStorage, "propose_memory", new_callable=AsyncMock
    ) as mock_parent_propose:
        mock_parent_propose.return_value = mock_response

        result = await storage.propose_memory(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.8,
        )

        assert result == mock_response
        mock_parent_propose.assert_called_once_with(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.8,
            context=None,
        )

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_connection_error() -> None:
    """Test connection error handling."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    from a2p.storage.cloud import CloudStorage
    with patch.object(CloudStorage, "get", new_callable=AsyncMock) as mock_parent_get:
        mock_parent_get.side_effect = httpx.RequestError("Connection failed")

        with pytest.raises(GaugidConnectionError):
            await storage.get(user_did)

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_get_with_scopes() -> None:
    """Test getting profile with scopes."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    mock_profile = {
        "id": user_did,
        "preferences": {"theme": "dark"},
    }

    from a2p.storage.cloud import CloudStorage
    with patch.object(CloudStorage, "get", new_callable=AsyncMock) as mock_parent_get:
        mock_parent_get.return_value = mock_profile

        result = await storage.get(user_did, scopes=["a2p:preferences"])

        assert result == mock_profile
        mock_parent_get.assert_called_once_with(user_did, ["a2p:preferences"])

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_propose_memory_with_context() -> None:
    """Test proposing memory with context."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    mock_response = {"proposal_id": "prop_123", "status": "pending"}

    from a2p.storage.cloud import CloudStorage
    with patch.object(
        CloudStorage, "propose_memory", new_callable=AsyncMock
    ) as mock_parent_propose:
        mock_parent_propose.return_value = mock_response

        result = await storage.propose_memory(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.8,
            context="Observed during UI interaction",
        )

        assert result == mock_response
        mock_parent_propose.assert_called_once_with(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.8,
            context="Observed during UI interaction",
        )

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_propose_memory_error() -> None:
    """Test proposing memory with error."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        "error": {"code": "A2P006", "message": "Invalid memory"}
    }
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Bad Request", request=MagicMock(), response=mock_response
    )

    from a2p.storage.cloud import CloudStorage
    with patch.object(
        CloudStorage, "propose_memory", new_callable=AsyncMock
    ) as mock_parent_propose:
        mock_parent_propose.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        with pytest.raises(GaugidAPIError):
            await storage.propose_memory(
                user_did=user_did,
                content="Invalid memory",
            )

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_set_connection_error() -> None:
    """Test setting profile with connection error."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    from a2p.types import Profile, ProfileType
    mock_profile = Profile(id=user_did, profileType=ProfileType.HUMAN, identity={"did": user_did})

    from a2p.storage.cloud import CloudStorage
    with patch.object(CloudStorage, "set", new_callable=AsyncMock) as mock_parent_set:
        mock_parent_set.side_effect = httpx.RequestError("Connection failed")

        with pytest.raises(GaugidConnectionError):
            await storage.set(user_did, mock_profile)

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_delete_connection_error() -> None:
    """Test deleting profile with connection error."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"

    from a2p.storage.cloud import CloudStorage
    with patch.object(CloudStorage, "delete", new_callable=AsyncMock) as mock_parent_delete:
        mock_parent_delete.side_effect = httpx.RequestError("Connection failed")

        with pytest.raises(GaugidConnectionError):
            await storage.delete(user_did)

    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_propose_memory_with_memory_type() -> None:
    """Test proposing memory with memory_type parameter."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"
    
    mock_response = {
        "success": True,
        "data": {
            "proposal_id": "prop_123",
            "status": "pending",
        }
    }
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        
        result = await storage.propose_memory(
            user_did=user_did,
            content="User prefers window seats",
            category="a2p:travel_preferences",
            memory_type="episodic",
            confidence=0.9,
        )
        
        assert result == mock_response["data"]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        # post(url, ...) or post(..., json=...) - url can be first positional arg
        url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
        assert call_args.kwargs.get("json", {}).get("memory_type") == "episodic"
        assert f"/profile/{user_did}/memories/propose" in url
    
    await storage.close()


@pytest.mark.asyncio
async def test_gaugid_storage_propose_memory_without_memory_type() -> None:
    """Test proposing memory without memory_type (uses base class)."""
    storage = GaugidStorage(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:test"
    
    mock_response = {
        "proposal_id": "prop_123",
        "status": "pending",
    }
    
    from a2p.storage.cloud import CloudStorage
    with patch.object(
        CloudStorage, "propose_memory", new_callable=AsyncMock
    ) as mock_parent_propose:
        mock_parent_propose.return_value = mock_response
        
        result = await storage.propose_memory(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.8,
        )
        
        assert result == mock_response
        mock_parent_propose.assert_called_once_with(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.8,
            context=None,
        )
    
    await storage.close()
