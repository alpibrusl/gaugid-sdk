"""Tests for OAuthFlow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from gaugid.auth import OAuthFlow
from gaugid.types import (
    GaugidAPIError,
    GaugidAuthError,
    GaugidConnectionError,
    OAuthTokenResponse,
)


def test_oauth_flow_init() -> None:
    """Test OAuthFlow initialization."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )
    assert flow.client_id == "test_client"
    assert flow.client_secret == "test_secret"
    assert flow.redirect_uri == "https://example.com/callback"
    assert flow.api_url == "https://api.gaugid.com"
    assert flow.timeout == 30.0


def test_oauth_flow_init_custom_api_url() -> None:
    """Test OAuthFlow initialization with custom API URL."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
        api_url="https://custom.api.com",
    )
    assert flow.api_url == "https://custom.api.com"


def test_oauth_flow_init_custom_timeout() -> None:
    """Test OAuthFlow initialization with custom timeout."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
        timeout=60.0,
    )
    assert flow.timeout == 60.0


def test_get_authorization_url() -> None:
    """Test generating authorization URL."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    auth_url, state = flow.get_authorization_url(
        scopes=["a2p:preferences", "a2p:interests"]
    )

    assert state is not None
    assert len(state) > 0
    assert "client_id=test_client" in auth_url
    assert "redirect_uri=https%3A%2F%2Fexample.com%2Fcallback" in auth_url
    assert "response_type=code" in auth_url
    assert "scope=a2p%3Apreferences%2Ca2p%3Ainterests" in auth_url
    assert f"state={state}" in auth_url
    assert auth_url.startswith("https://api.gaugid.com/connect/authorize")


def test_get_authorization_url_with_state() -> None:
    """Test generating authorization URL with custom state."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    custom_state = "custom_state_123"
    auth_url, state = flow.get_authorization_url(
        scopes=["a2p:preferences"],
        state=custom_state,
    )

    assert state == custom_state
    assert f"state={custom_state}" in auth_url


def test_parse_authorization_response() -> None:
    """Test parsing authorization response."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    redirect_url = "https://example.com/callback?code=auth_code_123&state=test_state"
    code = flow.parse_authorization_response(redirect_url, "test_state")

    assert code == "auth_code_123"


def test_parse_authorization_response_invalid_state() -> None:
    """Test parsing authorization response with invalid state."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    redirect_url = "https://example.com/callback?code=auth_code_123&state=wrong_state"

    with pytest.raises(GaugidAuthError, match="State mismatch"):
        flow.parse_authorization_response(redirect_url, "expected_state")


def test_parse_authorization_response_no_code() -> None:
    """Test parsing authorization response without code."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    redirect_url = "https://example.com/callback?error=access_denied&state=test_state"

    with pytest.raises(GaugidAuthError, match="OAuth error|access_denied|Authorization denied"):
        flow.parse_authorization_response(redirect_url, "test_state")


@pytest.mark.asyncio
async def test_exchange_code() -> None:
    """Test exchanging authorization code for token."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    mock_response = {
        "access_token": "token_123",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "a2p:preferences a2p:interests",
        "connection_id": "conn_123",
        "user_did": "did:a2p:user:gaugid:alice",
        "profiles": [{"id": "did:a2p:user:gaugid:alice", "name": "Personal"}],
    }

    with patch.object(flow._client, "post", new_callable=AsyncMock) as mock_post:
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_http_response

        result = await flow.exchange_code("auth_code_123", "test_state")

        assert isinstance(result, OAuthTokenResponse)
        assert result.access_token == "token_123"
        assert result.expires_in == 3600
        assert result.scope == "a2p:preferences a2p:interests"
        assert result.user_did == "did:a2p:user:gaugid:alice"
        assert len(result.profiles) == 1

        # Verify request (auth uses json= for token exchange)
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "json" in call_args.kwargs
        assert call_args.kwargs["json"]["code"] == "auth_code_123"
        assert call_args.kwargs["json"]["grant_type"] == "authorization_code"


@pytest.mark.asyncio
async def test_exchange_code_api_error() -> None:
    """Test exchanging code with API error."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    with patch.object(flow._client, "post", new_callable=AsyncMock) as mock_post:
        mock_http_response = MagicMock()
        mock_http_response.status_code = 400
        mock_http_response.json.return_value = {
            "error": {"code": "A2P001", "message": "Invalid code"}
        }
        mock_http_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_http_response
        )
        mock_post.return_value = mock_http_response

        with pytest.raises(GaugidAuthError):
            await flow.exchange_code("invalid_code", "test_state")


@pytest.mark.asyncio
async def test_exchange_code_connection_error() -> None:
    """Test exchanging code with connection error."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    with patch.object(flow._client, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.RequestError("Connection failed")

        with pytest.raises(GaugidConnectionError):
            await flow.exchange_code("auth_code_123", "test_state")


@pytest.mark.asyncio
async def test_refresh_token() -> None:
    """Test refreshing access token."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    mock_response = {
        "access_token": "new_token_456",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "a2p:preferences",
    }

    with patch.object(flow._client, "post", new_callable=AsyncMock) as mock_post:
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_http_response

        result = await flow.refresh_token("refresh_token_123")

        assert isinstance(result, OAuthTokenResponse)
        assert result.access_token == "new_token_456"

        # Verify request (auth uses json= for refresh)
        call_args = mock_post.call_args
        assert call_args.kwargs["json"]["refresh_token"] == "refresh_token_123"
        assert call_args.kwargs["json"]["grant_type"] == "refresh_token"


@pytest.mark.asyncio
async def test_revoke_token() -> None:
    """Test revoking a token."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    with patch.object(flow._client, "post", new_callable=AsyncMock) as mock_post:
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_http_response

        await flow.revoke_token("token_123")

        # Verify request (auth uses json= for revoke)
        call_args = mock_post.call_args
        assert call_args.kwargs["json"]["token"] == "token_123"


@pytest.mark.asyncio
async def test_close() -> None:
    """Test closing OAuth flow."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    with patch.object(flow._client, "aclose", new_callable=AsyncMock) as mock_close:
        await flow.close()
        mock_close.assert_called_once()


@pytest.mark.asyncio
async def test_oauth_flow_context_manager() -> None:
    """Test OAuthFlow as async context manager."""
    async with OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    ) as flow:
        assert flow is not None
        assert flow.client_id == "test_client"


@pytest.mark.asyncio
async def test_refresh_token_api_error() -> None:
    """Test refreshing token with API error."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    with patch.object(flow._client, "post", new_callable=AsyncMock) as mock_post:
        mock_http_response = MagicMock()
        mock_http_response.status_code = 400
        mock_http_response.json.return_value = {
            "error": {"code": "A2P001", "message": "Invalid refresh token"}
        }
        mock_http_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_http_response
        )
        mock_post.return_value = mock_http_response

        with pytest.raises(GaugidAuthError):
            await flow.refresh_token("invalid_refresh_token")


@pytest.mark.asyncio
async def test_revoke_token_error() -> None:
    """Test revoking token with error."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    with patch.object(flow._client, "post", new_callable=AsyncMock) as mock_post:
        mock_http_response = MagicMock()
        mock_http_response.status_code = 400
        mock_http_response.text = "Bad request"
        mock_http_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_http_response
        )
        mock_post.return_value = mock_http_response

        with pytest.raises(GaugidAPIError, match="Token revocation"):
            await flow.revoke_token("token_123")


def test_get_authorization_url_empty_scopes() -> None:
    """Test generating authorization URL with empty scopes."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    auth_url, state = flow.get_authorization_url(scopes=[])

    assert "scope=" in auth_url or "scope=%2C" in auth_url  # Empty or encoded comma


def test_parse_authorization_response_error_parameter() -> None:
    """Test parsing authorization response with error parameter."""
    flow = OAuthFlow(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback",
    )

    redirect_url = "https://example.com/callback?error=server_error&error_description=Something%20went%20wrong&state=test_state"

    with pytest.raises(GaugidAuthError, match="OAuth error|server_error|Something|Authorization denied"):
        flow.parse_authorization_response(redirect_url, "test_state")
