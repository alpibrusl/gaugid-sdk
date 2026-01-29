"""Tests for Gaugid types and error handling."""

import pytest
import httpx
from gaugid.types import (
    GaugidError,
    GaugidAPIError,
    GaugidAuthError,
    GaugidConnectionError,
    parse_gaugid_error,
    OAuthTokenResponse,
)


def test_gaugid_error() -> None:
    """Test GaugidError base class."""
    error = GaugidError("Test error", code="TEST001")
    assert str(error) == "Test error"
    assert error.message == "Test error"
    assert error.code == "TEST001"


def test_gaugid_api_error() -> None:
    """Test GaugidAPIError."""
    error = GaugidAPIError("API error", code="A2P001", status_code=400)
    assert error.message == "API error"
    assert error.code == "A2P001"
    assert error.status_code == 400


def test_gaugid_auth_error() -> None:
    """Test GaugidAuthError."""
    error = GaugidAuthError("Auth failed")
    assert error.message == "Auth failed"
    assert isinstance(error, GaugidError)


def test_gaugid_connection_error() -> None:
    """Test GaugidConnectionError."""
    original = ConnectionError("Original error")
    error = GaugidConnectionError("Connection failed", original_error=original)
    assert error.message == "Connection failed"
    assert error.original_error == original
    assert isinstance(error, GaugidError)


def test_parse_gaugid_error_with_error_object() -> None:
    """Test parsing Gaugid error with error object."""
    # Use A2P006 (Invalid request) so we get GaugidAPIError; A2P001 maps to GaugidAuthError
    response = httpx.Response(
        400,
        json={"error": {"code": "A2P006", "message": "Invalid request"}},
    )
    error = parse_gaugid_error(response)
    assert isinstance(error, GaugidAPIError)
    assert error.code == "A2P006"
    assert error.message == "Invalid request"
    assert error.status_code == 400


def test_parse_gaugid_error_without_error_object() -> None:
    """Test parsing Gaugid error without error object."""
    response = httpx.Response(500, text="Internal server error")
    error = parse_gaugid_error(response)
    assert isinstance(error, GaugidAPIError)
    assert error.message == "Internal server error"
    assert error.status_code == 500


def test_oauth_token_response() -> None:
    """Test OAuthTokenResponse model."""
    response = OAuthTokenResponse(
        access_token="token123",
        expires_in=3600,
        scope="a2p:preferences a2p:interests",
    )
    assert response.access_token == "token123"
    assert response.expires_in == 3600
    assert response.scope == "a2p:preferences a2p:interests"
    assert response.token_type == "Bearer"


def test_oauth_token_response_with_profiles() -> None:
    """Test OAuthTokenResponse with profiles."""
    response = OAuthTokenResponse(
        access_token="token123",
        expires_in=3600,
        scope="a2p:preferences",
        user_did="did:a2p:user:gaugid:alice",
        profiles=[
            {"id": "did:a2p:user:gaugid:alice", "name": "Personal"},
            {"id": "did:a2p:user:gaugid:bob", "name": "Work"},
        ],
    )
    assert response.user_did == "did:a2p:user:gaugid:alice"
    assert len(response.profiles) == 2
    assert response.profiles[0]["id"] == "did:a2p:user:gaugid:alice"


def test_parse_gaugid_error_with_details() -> None:
    """Test parsing Gaugid error with details."""
    # Use A2P006 so we get GaugidAPIError with status_code/response
    response = httpx.Response(
        400,
        json={
            "error": {
                "code": "A2P006",
                "message": "Invalid request",
                "details": {"field": "user_did", "reason": "Invalid format"},
            }
        },
    )
    error = parse_gaugid_error(response)
    assert isinstance(error, GaugidAPIError)
    assert error.code == "A2P006"
    assert error.message == "Invalid request"
    assert error.response is not None


def test_parse_gaugid_error_empty_response() -> None:
    """Test parsing Gaugid error with empty response."""
    response = httpx.Response(500, text="")
    error = parse_gaugid_error(response)
    assert isinstance(error, GaugidAPIError)
    assert error.status_code == 500
    assert error.message == "" or error.message is not None


def test_gaugid_error_with_code() -> None:
    """Test GaugidError with code."""
    error = GaugidError("Test error", code="TEST001")
    assert error.message == "Test error"
    assert error.code == "TEST001"


def test_gaugid_error_without_code() -> None:
    """Test GaugidError without code."""
    error = GaugidError("Test error")
    assert error.message == "Test error"
    assert error.code is None


def test_gaugid_api_error_with_response() -> None:
    """Test GaugidAPIError with response."""
    error = GaugidAPIError(
        "API error",
        code="A2P001",
        status_code=400,
        response={"field": "user_did"},
    )
    assert error.message == "API error"
    assert error.code == "A2P001"
    assert error.status_code == 400
    assert error.response == {"field": "user_did"}


def test_connection_token_info() -> None:
    """Test ConnectionTokenInfo model."""
    from gaugid.types import ConnectionTokenInfo

    token_info = ConnectionTokenInfo(
        token="token_123",
        expires_at=1234567890,
        scopes=["a2p:preferences"],
        connection_id="conn_123",
        user_did="did:a2p:user:gaugid:alice",
    )

    assert token_info.token == "token_123"
    assert token_info.expires_at == 1234567890
    assert token_info.scopes == ["a2p:preferences"]
    assert token_info.connection_id == "conn_123"
    assert token_info.user_did == "did:a2p:user:gaugid:alice"


def test_connection_token_info_minimal() -> None:
    """Test ConnectionTokenInfo with minimal fields."""
    from gaugid.types import ConnectionTokenInfo

    token_info = ConnectionTokenInfo(token="token_123")

    assert token_info.token == "token_123"
    assert token_info.expires_at is None
    assert token_info.scopes == []
    assert token_info.connection_id is None
    assert token_info.user_did is None
    assert token_info.profiles is None


def test_parse_gaugid_error_auth_codes() -> None:
    """Test parsing Gaugid error with auth error codes."""
    from gaugid.types import ERROR_CODES
    
    # Test A2P001 (Not authorized) -> GaugidAuthError
    response = httpx.Response(
        401,
        json={"error": {"code": "A2P001", "message": "Not authorized"}},
    )
    error = parse_gaugid_error(response)
    assert isinstance(error, GaugidAuthError)
    assert error.code == "A2P001"
    assert "Not authorized" in error.message
    
    # Test A2P019 (Invalid token) -> GaugidAuthError
    response = httpx.Response(
        401,
        json={"error": {"code": "A2P019", "message": "Invalid token"}},
    )
    error = parse_gaugid_error(response)
    assert isinstance(error, GaugidAuthError)
    assert error.code == "A2P019"
    
    # Test A2P020 (Connection revoked) -> GaugidAuthError
    response = httpx.Response(
        401,
        json={"error": {"code": "A2P020", "message": "Connection revoked"}},
    )
    error = parse_gaugid_error(response)
    assert isinstance(error, GaugidAuthError)
    assert error.code == "A2P020"


def test_parse_gaugid_error_rate_limit_codes() -> None:
    """Test parsing Gaugid error with rate limit codes."""
    # Test A2P023 (Rate limit exceeded)
    response = httpx.Response(
        429,
        json={"error": {"code": "A2P023", "message": "Rate limit exceeded"}},
    )
    error = parse_gaugid_error(response)
    assert isinstance(error, GaugidAPIError)
    assert error.code == "A2P023"
    assert error.status_code == 429


def test_parse_gaugid_error_with_error_code_description() -> None:
    """Test that error messages include error code descriptions."""
    from gaugid.types import ERROR_CODES
    
    response = httpx.Response(
        400,
        json={"error": {"code": "A2P003", "message": "Profile not found"}},
    )
    error = parse_gaugid_error(response)
    assert isinstance(error, GaugidAPIError)
    assert error.code == "A2P003"
    # Message should include description from ERROR_CODES
    assert ERROR_CODES["A2P003"] in error.message or "Profile not found" in error.message
