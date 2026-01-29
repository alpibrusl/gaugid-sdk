"""Tests for GaugidClient."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from gaugid.client import GaugidClient
from gaugid.types import (
    GaugidError,
    GaugidAPIError,
    GaugidAuthError,
    GaugidConnectionError,
    OAuthTokenResponse,
)
from gaugid.utils import generate_agent_did, validate_gaugid_did


@pytest.mark.asyncio
async def test_client_init_with_connection_token() -> None:
    """Test GaugidClient initialization with connection token."""
    client = GaugidClient(connection_token="test_token")
    assert client.connection_token == "test_token"
    assert client.storage is not None
    assert client._client is not None
    await client.close()


@pytest.mark.asyncio
async def test_client_init_with_agent_did() -> None:
    """Test GaugidClient initialization with explicit agent DID."""
    agent_did = generate_agent_did(name="test-agent", namespace="gaugid")
    client = GaugidClient(
        connection_token="test_token",
        agent_did=agent_did,
    )
    assert client._client.agent_did == agent_did
    await client.close()


@pytest.mark.asyncio
async def test_client_init_with_namespace() -> None:
    """Test GaugidClient initialization with namespace."""
    client = GaugidClient(
        connection_token="test_token",
        namespace="gaugid",
    )
    # Should generate agent DID with namespace
    assert client._client.agent_did is not None
    assert "gaugid" in client._client.agent_did
    await client.close()


@pytest.mark.asyncio
async def test_client_init_invalid_agent_did() -> None:
    """Test GaugidClient initialization with invalid agent DID."""
    with pytest.raises(ValueError, match="Invalid agent DID"):
        GaugidClient(
            connection_token="test_token",
            agent_did="invalid-did",
        )


@pytest.mark.asyncio
async def test_client_get_profile() -> None:
    """Test getting a user profile."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"

    mock_profile = {
        "id": user_did,
        "profileType": "user",
        "identity": {"did": user_did},
        "preferences": {"theme": "dark"},
    }

    with patch.object(client._client, "get_profile", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_profile

        result = await client.get_profile(
            user_did=user_did,
            scopes=["a2p:preferences"],
        )

        assert result == mock_profile
        mock_get.assert_called_once_with(
            user_did=user_did,
            scopes=["a2p:preferences"],
            sub_profile=None,
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_get_profile_invalid_did() -> None:
    """Test getting profile with invalid DID."""
    client = GaugidClient(connection_token="test_token")

    with pytest.raises(ValueError, match="Invalid user DID"):
        await client.get_profile(
            user_did="invalid-did",
            scopes=["a2p:preferences"],
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_get_profile_error() -> None:
    """Test error handling in get_profile."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"

    with patch.object(client._client, "get_profile", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = GaugidAPIError("API error", code="A2P001", status_code=404)

        with pytest.raises(GaugidAPIError):
            await client.get_profile(
                user_did=user_did,
                scopes=["a2p:preferences"],
            )

    await client.close()


@pytest.mark.asyncio
async def test_client_request_access() -> None:
    """Test requesting access to a user profile."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"

    mock_response = {
        "profile": {"id": user_did},
        "consent": {"status": "granted"},
        "filtered_scopes": ["a2p:preferences"],
    }

    with patch.object(client._client, "request_access", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        result = await client.request_access(
            user_did=user_did,
            scopes=["a2p:preferences"],
            purpose="Personalization",
        )

        assert result == mock_response
        mock_request.assert_called_once_with(
            user_did=user_did,
            scopes=["a2p:preferences"],
            sub_profile=None,
            purpose="Personalization",
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_propose_memory() -> None:
    """Test proposing a memory."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"

    mock_response = {
        "proposal_id": "prop_123",
        "status": "pending",
    }

    with patch.object(client.storage, "propose_memory", new_callable=AsyncMock) as mock_propose:
        mock_propose.return_value = mock_response

        result = await client.propose_memory(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.8,
        )

        assert result == mock_response
        mock_propose.assert_called_once_with(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.8,
            context=None,
            memory_type=None,
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_check_permission() -> None:
    """Test checking permissions."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"

    with patch.object(client._client, "check_permission", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True

        result = await client.check_permission(
            user_did=user_did,
            permission="read_scoped",
            scope="a2p:preferences",
        )

        assert result is True
        # Note: PermissionLevel conversion is tested in integration

    await client.close()


@pytest.mark.asyncio
async def test_client_from_oauth_response() -> None:
    """Test creating client from OAuth response."""
    token_response = OAuthTokenResponse(
        access_token="token_123",
        expires_in=3600,
        scope="a2p:preferences a2p:interests",
        user_did="did:a2p:user:gaugid:alice",
        profiles=[
            {"id": "did:a2p:user:gaugid:alice", "name": "Personal"},
            {"id": "did:a2p:user:gaugid:bob", "name": "Work"},
        ],
    )

    client = GaugidClient.from_oauth_response(token_response)
    assert client.connection_token == "token_123"
    assert client._user_did == "did:a2p:user:gaugid:alice"
    assert len(client._available_profiles) == 2
    # Should auto-select first profile if only one
    # (Actually, it selects if len == 1, but we have 2, so no auto-select)
    await client.close()


@pytest.mark.asyncio
async def test_client_from_oauth_response_single_profile() -> None:
    """Test creating client from OAuth response with single profile."""
    token_response = OAuthTokenResponse(
        access_token="token_123",
        expires_in=3600,
        scope="a2p:preferences",
        user_did="did:a2p:user:gaugid:alice",
        profiles=[
            {"id": "did:a2p:user:gaugid:alice", "name": "Personal"},
        ],
    )

    client = GaugidClient.from_oauth_response(token_response)
    assert client._selected_profile_did == "did:a2p:user:gaugid:alice"
    await client.close()


@pytest.mark.asyncio
async def test_client_list_profiles() -> None:
    """Test listing available profiles."""
    client = GaugidClient(connection_token="test_token")
    client._available_profiles = [
        {"id": "did:a2p:user:gaugid:alice", "name": "Personal"},
        {"id": "did:a2p:user:gaugid:bob", "name": "Work"},
    ]

    profiles = await client.list_profiles()
    assert len(profiles) == 2
    assert profiles[0].get("id") == "did:a2p:user:gaugid:alice" or profiles[0].get("did") == "did:a2p:user:gaugid:alice"

    await client.close()


@pytest.mark.asyncio
async def test_client_select_profile() -> None:
    """Test selecting a profile."""
    client = GaugidClient(connection_token="test_token")
    client._available_profiles = [
        {"id": "did:a2p:user:gaugid:alice", "name": "Personal"},
        {"id": "did:a2p:user:gaugid:bob", "name": "Work"},
    ]

    client.select_profile("did:a2p:user:gaugid:bob")
    assert client._selected_profile_did == "did:a2p:user:gaugid:bob"

    await client.close()


@pytest.mark.asyncio
async def test_client_select_profile_invalid() -> None:
    """Test selecting an invalid profile."""
    client = GaugidClient(connection_token="test_token")
    client._available_profiles = [
        {"id": "did:a2p:user:gaugid:alice", "name": "Personal"},
    ]

    with pytest.raises(ValueError, match="Invalid profile DID"):
        client.select_profile("invalid-did")

    await client.close()


@pytest.mark.asyncio
async def test_client_select_profile_not_found() -> None:
    """Test selecting a profile not in available profiles."""
    client = GaugidClient(connection_token="test_token")
    client._available_profiles = [
        {"id": "did:a2p:user:gaugid:alice", "name": "Personal"},
    ]

    with pytest.raises(ValueError, match="not available|not found among connected profiles"):
        client.select_profile("did:a2p:user:gaugid:unknown")

    await client.close()


@pytest.mark.asyncio
async def test_client_get_current_profile_did() -> None:
    """Test getting current profile DID."""
    client = GaugidClient(connection_token="test_token")
    client._user_did = "did:a2p:user:gaugid:alice"

    did = client.get_current_profile_did()
    assert did == "did:a2p:user:gaugid:alice"

    # Test with selected profile
    client._selected_profile_did = "did:a2p:user:gaugid:bob"
    did = client.get_current_profile_did()
    assert did == "did:a2p:user:gaugid:bob"

    await client.close()


@pytest.mark.asyncio
async def test_client_get_current_profile() -> None:
    """Test getting current profile."""
    client = GaugidClient(connection_token="test_token")
    client._selected_profile_did = "did:a2p:user:gaugid:alice"

    mock_profile = {
        "id": "did:a2p:user:gaugid:alice",
        "preferences": {"theme": "dark"},
    }

    with patch.object(client, "get_profile", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_profile

        result = await client.get_current_profile(scopes=["a2p:preferences"])

        assert result == mock_profile
        mock_get.assert_called_once_with(
            user_did="did:a2p:user:gaugid:alice",
            scopes=["a2p:preferences"],
            sub_profile=None,
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_get_current_profile_no_selection() -> None:
    """Test getting current profile without selection (no DID, connection token mode)."""
    client = GaugidClient(connection_token="test_token")
    client._user_did = None
    client._selected_profile_did = None

    # When no profile DID, get_current_profile uses connection token mode and calls get_profile(scopes=...).
    # Mock get_profile to avoid real HTTP and simulate "no profile" response.
    with patch.object(client, "get_profile", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = ValueError("No profile selected")

        with pytest.raises(ValueError, match="No profile selected"):
            await client.get_current_profile(scopes=["a2p:preferences"])

    await client.close()


@pytest.mark.asyncio
async def test_client_propose_memory_to_current() -> None:
    """Test proposing memory to current profile."""
    client = GaugidClient(connection_token="test_token")
    client._selected_profile_did = "did:a2p:user:gaugid:alice"

    mock_response = {"proposal_id": "prop_123", "status": "pending"}

    with patch.object(client, "propose_memory", new_callable=AsyncMock) as mock_propose:
        mock_propose.return_value = mock_response

        result = await client.propose_memory_to_current(
            content="User prefers dark mode",
            category="a2p:preferences",
        )

        assert result == mock_response
        mock_propose.assert_called_once_with(
            user_did="did:a2p:user:gaugid:alice",
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.7,
            context=None,
            memory_type=None,
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_resolve_did() -> None:
    """Test resolving a DID."""
    client = GaugidClient(connection_token="test_token")
    agent_did = "did:a2p:agent:gaugid:my-agent"

    mock_did_doc = {
        "@context": ["https://www.w3.org/ns/did/v1"],
        "id": agent_did,
        "verificationMethod": [
            {
                "id": f"{agent_did}#key-1",
                "type": "Ed25519VerificationKey2020",
                "publicKeyMultibase": "z...",
            }
        ],
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": mock_did_doc}
        mock_response.raise_for_status = MagicMock()

        mock_client.get = AsyncMock(return_value=mock_response)

        result = await client.resolve_did(agent_did)

        assert result == mock_did_doc
        mock_client.get.assert_called_once()

    await client.close()


@pytest.mark.asyncio
async def test_client_resolve_did_invalid() -> None:
    """Test resolving an invalid DID."""
    client = GaugidClient(connection_token="test_token")

    with pytest.raises(ValueError, match="Invalid DID"):
        await client.resolve_did("invalid-did")

    await client.close()


@pytest.mark.asyncio
async def test_client_resolve_did_error() -> None:
    """Test DID resolution error handling."""
    client = GaugidClient(connection_token="test_token")
    agent_did = "did:a2p:agent:gaugid:my-agent"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "success": False,
            "error": {"code": "A2P003", "message": "DID not found"},
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )

        mock_client.get = AsyncMock(return_value=mock_response)

        with pytest.raises(GaugidAPIError):
            await client.resolve_did(agent_did)

    await client.close()


@pytest.mark.asyncio
async def test_client_register_agent() -> None:
    """Test registering an agent."""
    client = GaugidClient(connection_token="test_token")
    agent_did = "did:a2p:agent:gaugid:my-agent"

    mock_response = {
        "success": True,
        "data": {
            "agent": {
                "id": "agent_123",
                "did": agent_did,
                "name": "My Agent",
                "verified": True,
            }
        },
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        mock_client.post = AsyncMock(return_value=mock_http_response)

        result = await client.register_agent(
            agent_did=agent_did,
            name="My Agent",
            description="Test agent",
            public_key="base64_public_key",
        )

        assert result == mock_response["data"]
        mock_client.post.assert_called_once()

    await client.close()


@pytest.mark.asyncio
async def test_client_register_agent_invalid_did() -> None:
    """Test registering agent with invalid DID."""
    client = GaugidClient(connection_token="test_token")

    with pytest.raises(ValueError, match="Invalid agent DID"):
        await client.register_agent(
            agent_did="invalid-did",
            name="My Agent",
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_close() -> None:
    """Test closing the client."""
    client = GaugidClient(connection_token="test_token")

    with patch.object(client.storage, "close", new_callable=AsyncMock) as mock_close:
        await client.close()
        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_client_context_manager() -> None:
    """Test client as async context manager."""
    async with GaugidClient(connection_token="test_token") as client:
        assert client is not None
        assert client.connection_token == "test_token"


@pytest.mark.asyncio
async def test_client_get_profile_with_sub_profile() -> None:
    """Test getting profile with sub-profile."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"

    mock_profile = {"id": user_did, "profileType": "user"}

    with patch.object(client._client, "get_profile", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_profile

        result = await client.get_profile(
            user_did=user_did,
            scopes=["a2p:preferences"],
            sub_profile="work",
        )

        assert result == mock_profile
        mock_get.assert_called_once_with(
            user_did=user_did,
            scopes=["a2p:preferences"],
            sub_profile="work",
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_propose_memory_with_context() -> None:
    """Test proposing memory with context."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"

    mock_response = {"proposal_id": "prop_123", "status": "pending"}

    with patch.object(client.storage, "propose_memory", new_callable=AsyncMock) as mock_propose:
        mock_propose.return_value = mock_response

        result = await client.propose_memory(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.9,
            context="Observed during UI interaction",
        )

        assert result == mock_response
        mock_propose.assert_called_once_with(
            user_did=user_did,
            content="User prefers dark mode",
            category="a2p:preferences",
            confidence=0.9,
            context="Observed during UI interaction",
            memory_type=None,
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_propose_memory_default_confidence() -> None:
    """Test proposing memory with default confidence."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"

    mock_response = {"proposal_id": "prop_123", "status": "pending"}

    with patch.object(client.storage, "propose_memory", new_callable=AsyncMock) as mock_propose:
        mock_propose.return_value = mock_response

        await client.propose_memory(
            user_did=user_did,
            content="User prefers dark mode",
        )

        mock_propose.assert_called_once_with(
            user_did=user_did,
            content="User prefers dark mode",
            category=None,
            confidence=0.7,  # Default
            context=None,
            memory_type=None,
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_request_access_with_purpose() -> None:
    """Test requesting access with purpose."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"

    mock_response = {
        "profile": {"id": user_did},
        "consent": {"status": "granted"},
    }

    with patch.object(client._client, "request_access", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        result = await client.request_access(
            user_did=user_did,
            scopes=["a2p:preferences"],
            purpose="Personalization",
        )

        assert result == mock_response
        mock_request.assert_called_once_with(
            user_did=user_did,
            scopes=["a2p:preferences"],
            sub_profile=None,
            purpose="Personalization",
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_list_profiles_from_oauth() -> None:
    """Test listing profiles from OAuth response."""
    client = GaugidClient(connection_token="test_token")
    client._available_profiles = [
        {"id": "did:a2p:user:gaugid:alice", "name": "Personal"},
        {"id": "did:a2p:user:gaugid:bob", "name": "Work"},
    ]

    profiles = await client.list_profiles()
    assert len(profiles) == 2
    assert profiles[0]["id"] == "did:a2p:user:gaugid:alice"


@pytest.mark.asyncio
async def test_client_list_profiles_from_user_did() -> None:
    """Test listing profiles when only user_did is available."""
    client = GaugidClient(connection_token="test_token")
    client._user_did = "did:a2p:user:gaugid:alice"
    client._available_profiles = []

    profiles = await client.list_profiles()
    assert len(profiles) == 1
    assert profiles[0]["did"] == "did:a2p:user:gaugid:alice"
    assert profiles[0]["type"] == "user"


@pytest.mark.asyncio
async def test_client_list_profiles_empty() -> None:
    """Test listing profiles when none are available."""
    client = GaugidClient(connection_token="test_token")
    client._available_profiles = []
    client._user_did = None

    profiles = await client.list_profiles()
    assert profiles == []


@pytest.mark.asyncio
async def test_client_select_profile_with_user_did() -> None:
    """Test selecting profile when user_did is available."""
    client = GaugidClient(connection_token="test_token")
    client._user_did = "did:a2p:user:gaugid:alice"
    client._available_profiles = []

    client.select_profile("did:a2p:user:gaugid:alice")
    assert client._selected_profile_did == "did:a2p:user:gaugid:alice"

    await client.close()


@pytest.mark.asyncio
async def test_client_get_current_profile_with_user_did() -> None:
    """Test getting current profile when user_did is set."""
    client = GaugidClient(connection_token="test_token")
    client._user_did = "did:a2p:user:gaugid:alice"

    mock_profile = {"id": "did:a2p:user:gaugid:alice", "preferences": {}}

    with patch.object(client, "get_profile", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_profile

        result = await client.get_current_profile(scopes=["a2p:preferences"])

        assert result == mock_profile
        mock_get.assert_called_once_with(
            user_did="did:a2p:user:gaugid:alice",
            scopes=["a2p:preferences"],
            sub_profile=None,
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_propose_memory_to_current_with_user_did() -> None:
    """Test proposing memory to current when user_did is set."""
    client = GaugidClient(connection_token="test_token")
    client._user_did = "did:a2p:user:gaugid:alice"

    mock_response = {"proposal_id": "prop_123", "status": "pending"}

    with patch.object(client, "propose_memory", new_callable=AsyncMock) as mock_propose:
        mock_propose.return_value = mock_response

        result = await client.propose_memory_to_current(
            content="User prefers dark mode",
        )

        assert result == mock_response
        mock_propose.assert_called_once_with(
            user_did="did:a2p:user:gaugid:alice",
            content="User prefers dark mode",
            category=None,
            confidence=0.7,
            context=None,
            memory_type=None,
        )

    await client.close()


@pytest.mark.asyncio
async def test_client_resolve_did_connection_error() -> None:
    """Test DID resolution with connection error."""
    client = GaugidClient(connection_token="test_token")
    agent_did = "did:a2p:agent:gaugid:my-agent"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Connection failed"))

        with pytest.raises(GaugidConnectionError):
            await client.resolve_did(agent_did)

    await client.close()


@pytest.mark.asyncio
async def test_client_register_agent_with_generate_keys() -> None:
    """Test registering agent with server-generated keys."""
    client = GaugidClient(connection_token="test_token")
    agent_did = "did:a2p:agent:gaugid:my-agent"

    mock_response = {
        "success": True,
        "data": {
            "agent": {"id": "agent_123", "did": agent_did},
            "privateKey": "private_key_123",
        },
    }

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        mock_client.post = AsyncMock(return_value=mock_http_response)

        result = await client.register_agent(
            agent_did=agent_did,
            name="My Agent",
            generate_keys=True,
        )

        assert result == mock_response["data"]
        assert "privateKey" in result

    await client.close()


@pytest.mark.asyncio
async def test_client_register_agent_connection_error() -> None:
    """Test agent registration with connection error."""
    client = GaugidClient(connection_token="test_token")
    agent_did = "did:a2p:agent:gaugid:my-agent"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))

        with pytest.raises(GaugidConnectionError):
            await client.register_agent(
                agent_did=agent_did,
                name="My Agent",
            )

    await client.close()


# New tests for connection token mode and memory_type support

@pytest.mark.asyncio
async def test_client_get_profile_connection_token_mode() -> None:
    """Test getting profile in connection token mode (no DID required)."""
    client = GaugidClient(connection_token="test_token")
    
    mock_response = {
        "success": True,
        "data": {
            "id": "uuid",
            "version": "1.0",
            "profileType": "personal",
            "identity": {"displayName": "Alice"},
        },
    }
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        
        result = await client.get_profile(scopes=["a2p:preferences"])
        
        assert result == mock_response["data"]
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "Bearer test_token" in str(call_args.kwargs.get("headers", {}))
    
    await client.close()


@pytest.mark.asyncio
async def test_client_get_profile_connection_token_mode_error() -> None:
    """Test error handling in connection token mode."""
    client = GaugidClient(connection_token="test_token")
    
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {
        "error": {"code": "A2P019", "message": "Invalid token"}
    }
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Unauthorized", request=MagicMock(), response=mock_response
    )
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(GaugidAuthError):
            await client.get_profile(scopes=["a2p:preferences"])
    
    await client.close()


@pytest.mark.asyncio
async def test_client_propose_memory_with_memory_type() -> None:
    """Test proposing memory with memory_type parameter."""
    client = GaugidClient(connection_token="test_token")
    user_did = "did:a2p:user:gaugid:alice"
    
    mock_response = {
        "proposal_id": "prop_123",
        "status": "pending",
    }
    
    with patch.object(client.storage, "propose_memory", new_callable=AsyncMock) as mock_propose:
        mock_propose.return_value = mock_response
        
        result = await client.propose_memory(
            content="User prefers window seats",
            user_did=user_did,
            category="a2p:travel_preferences",
            memory_type="episodic",
            confidence=0.9,
        )
        
        assert result == mock_response
        mock_propose.assert_called_once_with(
            user_did=user_did,
            content="User prefers window seats",
            category="a2p:travel_preferences",
            memory_type="episodic",
            confidence=0.9,
            context=None,
        )
    
    await client.close()


@pytest.mark.asyncio
async def test_client_propose_memory_connection_token_mode() -> None:
    """Test proposing memory in connection token mode (no DID)."""
    client = GaugidClient(connection_token="test_token")
    
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
        
        result = await client.propose_memory(
            content="User prefers window seats",
            category="a2p:travel_preferences",
            memory_type="episodic",
            confidence=0.9,
        )
        
        assert result == mock_response["data"]
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["json"]["memory_type"] == "episodic"
        assert call_kwargs["json"]["content"] == "User prefers window seats"
    
    await client.close()


@pytest.mark.asyncio
async def test_client_request_access_connection_token_mode() -> None:
    """Test requesting access in connection token mode with purpose object."""
    client = GaugidClient(connection_token="test_token")
    
    mock_response = {
        "success": True,
        "data": {
            "receiptId": "rcpt_uuid",
            "grantedScopes": ["a2p:episodic"],
            "deniedScopes": [],
        }
    }
    
    purpose = {
        "type": "memory_retrieval",
        "description": "Need to access user memories for context",
        "legalBasis": "user_consent",
    }
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        
        mock_client.post = AsyncMock(return_value=mock_response_obj)
        
        result = await client.request_access(
            scopes=["a2p:episodic"],
            purpose=purpose,
        )
        
        assert result == mock_response["data"]
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["json"]["purpose"] == purpose
        assert call_kwargs["json"]["scopes"] == ["a2p:episodic"]
    
    await client.close()


@pytest.mark.asyncio
async def test_client_propose_memory_to_current_with_memory_type() -> None:
    """Test proposing memory to current profile with memory_type."""
    client = GaugidClient(connection_token="test_token")
    client._selected_profile_did = "did:a2p:user:gaugid:alice"
    
    mock_response = {"proposal_id": "prop_123", "status": "pending"}
    
    with patch.object(client.storage, "propose_memory", new_callable=AsyncMock) as mock_propose:
        mock_propose.return_value = mock_response
        
        result = await client.propose_memory_to_current(
            content="User prefers dark mode",
            memory_type="semantic",
            category="a2p:preferences",
        )
        
        assert result == mock_response
        mock_propose.assert_called_once_with(
            user_did="did:a2p:user:gaugid:alice",
            content="User prefers dark mode",
            category="a2p:preferences",
            memory_type="semantic",
            confidence=0.7,
            context=None,
        )
    
    await client.close()


@pytest.mark.asyncio
async def test_client_get_current_profile_connection_token_mode() -> None:
    """Test getting current profile in connection token mode (no profile selected)."""
    client = GaugidClient(connection_token="test_token")
    # No profile selected - should use connection token mode
    
    mock_response = {
        "success": True,
        "data": {
            "id": "uuid",
            "profileType": "personal",
        }
    }
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status = MagicMock()
        
        mock_client.get = AsyncMock(return_value=mock_response_obj)
        
        result = await client.get_current_profile(scopes=["a2p:preferences"])
        
        assert result == mock_response["data"]
    
    await client.close()
