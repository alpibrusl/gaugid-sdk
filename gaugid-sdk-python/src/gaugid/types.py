"""
Gaugid-specific types and error classes.
"""

from typing import Any, Optional
import httpx
from pydantic import BaseModel, Field

# Error codes from Gaugid API
ERROR_CODES = {
    "A2P000": "Internal server error",
    "A2P001": "Not authorized",
    "A2P002": "Invalid public key format",
    "A2P003": "Profile not found",
    "A2P006": "Invalid request",
    "A2P009": "User already exists",
    "A2P013": "Authenticated DID must match",
    "A2P014": "Service not found",
    "A2P015": "Invalid redirect_uri",
    "A2P016": "Invalid scopes",
    "A2P017": "Invalid authorization code",
    "A2P018": "Authorization code expired",
    "A2P019": "Invalid or expired connection token",
    "A2P020": "Connection has been revoked",
    "A2P021": "Connection token required",
    "A2P022": "Service DID mismatch",
    "A2P023": "Rate limit exceeded",
    "A2P024": "Export limit exceeded",
    "A2P025": "Import limit exceeded",
    "A2P026": "Data import completed with errors",
}


class GaugidError(Exception):
    """Base exception for all Gaugid SDK errors."""

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class GaugidAPIError(GaugidError):
    """Error raised when the Gaugid API returns an error response."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        response: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code)
        self.status_code = status_code
        self.response = response or {}


class GaugidAuthError(GaugidError):
    """Error raised when authentication fails."""

    pass


class GaugidConnectionError(GaugidError):
    """Error raised when connection to Gaugid API fails."""

    def __init__(
        self, message: str, code: Optional[str] = None, original_error: Optional[Exception] = None
    ) -> None:
        super().__init__(message, code)
        self.original_error = original_error


class ConnectionTokenInfo(BaseModel):
    """Information about a connection token."""

    token: str = Field(..., description="The connection token")
    expires_at: Optional[int] = Field(None, description="Token expiration timestamp (Unix)")
    scopes: list[str] = Field(default_factory=list, description="Granted scopes")
    connection_id: Optional[str] = Field(None, description="Connection ID")
    user_did: Optional[str] = Field(None, description="User DID")
    profiles: Optional[list[dict[str, Any]]] = Field(None, description="Connected profiles")


class OAuthTokenResponse(BaseModel):
    """Response from OAuth token exchange."""

    access_token: str = Field(..., description="Connection token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    scope: str = Field(..., description="Granted scopes (space-separated)")
    connection_id: Optional[str] = Field(None, description="Connection ID")
    user_did: Optional[str] = Field(None, description="User DID")
    profiles: Optional[list[dict[str, Any]]] = Field(None, description="Connected profiles")


def parse_gaugid_error(response: httpx.Response) -> GaugidAPIError:
    """
    Parse a Gaugid API error response into a GaugidAPIError.

    Maps error codes to appropriate exception types and provides
    helpful error messages based on the error code.

    Args:
        response: HTTP response from Gaugid API

    Returns:
        GaugidAPIError with parsed error information
    """
    error_data = {}
    try:
        error_data = response.json()
    except Exception:
        pass

    error_obj = error_data.get("error", {})
    if isinstance(error_obj, dict):
        code = error_obj.get("code")
        message = error_obj.get("message", response.text or "Unknown error")
    else:
        code = None
        message = str(error_obj) if error_obj else response.text or "Unknown error"

    # Enhance message with error code description if available
    if code and code in ERROR_CODES:
        description = ERROR_CODES[code]
        if description not in message:
            message = f"{message} ({description})"

    # Map specific error codes to more specific exceptions
    if code == "A2P001" or code == "A2P019" or code == "A2P020" or code == "A2P021":
        # Authentication/authorization errors
        return GaugidAuthError(
            message=message,
            code=code,
        )
    elif code == "A2P023" or code == "A2P024" or code == "A2P025":
        # Rate limiting errors
        return GaugidAPIError(
            message=message,
            code=code,
            status_code=response.status_code,
            response=error_data,
        )

    return GaugidAPIError(
        message=message,
        code=code,
        status_code=response.status_code,
        response=error_data,
    )
