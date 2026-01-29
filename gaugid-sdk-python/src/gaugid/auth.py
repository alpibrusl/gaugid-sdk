"""
OAuth flow helpers for Gaugid service connections.

This module provides utilities for implementing the OAuth 2.0 authorization
code flow for connecting services to Gaugid.
"""

import secrets
from typing import Any, Optional
from urllib.parse import urlencode, urlparse, parse_qs
import httpx

from gaugid.types import GaugidAPIError, GaugidAuthError, GaugidConnectionError, OAuthTokenResponse


class OAuthFlow:
    """
    OAuth 2.0 authorization code flow helper for Gaugid.

    This class simplifies the OAuth flow for service connections:
    1. Generate authorization URL
    2. User authorizes and redirects back with code
    3. Exchange code for connection token

    Example:
        ```python
        from gaugid.auth import OAuthFlow

        flow = OAuthFlow(
            client_id="my-service",
            client_secret="secret",
            redirect_uri="https://myapp.com/callback",
            api_url="https://api.gaugid.com"
        )

        # Step 1: Get authorization URL
        auth_url, state = flow.get_authorization_url(
            scopes=["a2p:preferences", "a2p:interests"]
        )

        # Step 2: User authorizes, redirects back with code
        # Step 3: Exchange code for token
        token_response = await flow.exchange_code(code="auth_code_xxx", state=state)
        ```
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        api_url: str = "https://api.gaugid.com",
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize OAuth flow.

        Args:
            client_id: OAuth client ID (service ID)
            client_secret: OAuth client secret
            redirect_uri: Redirect URI registered with Gaugid
            api_url: Base URL of the Gaugid API
            timeout: HTTP request timeout in seconds
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    def get_authorization_url(
        self,
        scopes: list[str],
        state: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Generate authorization URL for OAuth flow.

        Args:
            scopes: List of scopes to request (e.g., ["a2p:preferences", "a2p:interests"])
            state: Optional state parameter (auto-generated if not provided)

        Returns:
            Tuple of (authorization_url, state)
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": ",".join(scopes),
            "state": state,
        }

        # Support both /connect/authorize and /api/connect/authorize for compatibility
        # Try /connect/authorize first (as per documentation), fallback to /api/connect/authorize
        auth_url = f"{self.api_url}/connect/authorize?{urlencode(params)}"
        return auth_url, state

    def parse_authorization_response(self, redirect_url: str, expected_state: str) -> str:
        """
        Parse authorization code from redirect URL.

        Args:
            redirect_url: The redirect URL with code and state parameters
            expected_state: The state value that was sent in the authorization request

        Returns:
            Authorization code

        Raises:
            GaugidAuthError: If state doesn't match or code is missing
        """
        parsed = urlparse(redirect_url)
        params = parse_qs(parsed.query)

        # Check for errors
        if "error" in params:
            error = params["error"][0]
            error_description = params.get("error_description", [""])[0]
            raise GaugidAuthError(f"OAuth error: {error} - {error_description}")

        # Verify state
        state = params.get("state", [None])[0]
        if state != expected_state:
            raise GaugidAuthError("State mismatch in OAuth callback")

        # Get code
        code = params.get("code", [None])[0]
        if not code:
            raise GaugidAuthError("Authorization code not found in redirect URL")

        return code

    async def exchange_code(
        self,
        code: str,
        state: Optional[str] = None,
    ) -> OAuthTokenResponse:
        """
        Exchange authorization code for connection token.

        Args:
            code: Authorization code from OAuth callback
            state: Optional state parameter (for verification)

        Returns:
            OAuthTokenResponse with connection token and metadata

        Raises:
            GaugidAuthError: On authentication errors
            GaugidAPIError: On API errors
            GaugidConnectionError: On connection errors
        """
        # Support both /connect/token and /api/connect/token for compatibility
        token_url = f"{self.api_url}/connect/token"

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }

        try:
            response = await self._client.post(token_url, json=payload)
            response.raise_for_status()
            data = response.json()

            return OAuthTokenResponse(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise GaugidAuthError("Invalid client credentials") from e
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    error_obj = error_data.get("error", {})
                    if isinstance(error_obj, dict):
                        message = error_obj.get("message", "Token exchange failed")
                    else:
                        message = str(error_obj) if error_obj else "Token exchange failed"
                except Exception:
                    message = "Token exchange failed"
                raise GaugidAuthError(message) from e
            raise GaugidAPIError(
                message=f"Token exchange failed: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise GaugidConnectionError(
                message=f"Failed to connect to Gaugid API: {e}",
                original_error=e,
            ) from e

    async def refresh_token(self, refresh_token: str) -> OAuthTokenResponse:
        """
        Refresh a connection token using a refresh token.

        Args:
            refresh_token: Refresh token from a previous token response

        Returns:
            OAuthTokenResponse with new connection token and metadata

        Raises:
            GaugidAuthError: On authentication errors
            GaugidAPIError: On API errors
            GaugidConnectionError: On connection errors
        """
        token_url = f"{self.api_url}/connect/token"

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = await self._client.post(token_url, json=payload)
            response.raise_for_status()
            data = response.json()
            return OAuthTokenResponse(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise GaugidAuthError("Invalid client credentials") from e
            if e.response.status_code == 400:
                try:
                    error_data = e.response.json()
                    error_obj = error_data.get("error", {})
                    if isinstance(error_obj, dict):
                        message = error_obj.get("message", "Token refresh failed")
                    else:
                        message = str(error_obj) if error_obj else "Token refresh failed"
                except Exception:
                    message = "Token refresh failed"
                raise GaugidAuthError(message) from e
            raise GaugidAPIError(
                message=f"Token refresh failed: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise GaugidConnectionError(
                message=f"Failed to connect to Gaugid API: {e}",
                original_error=e,
            ) from e

    async def revoke_token(self, token: str) -> None:
        """
        Revoke a connection token.

        Args:
            token: Connection token to revoke

        Raises:
            GaugidAuthError: On authentication errors
            GaugidAPIError: On API errors
            GaugidConnectionError: On connection errors
        """
        # Support both /connect/revoke and /api/connect/revoke for compatibility
        revoke_url = f"{self.api_url}/connect/revoke"

        payload = {
            "token": token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = await self._client.post(revoke_url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise GaugidAuthError("Invalid client credentials") from e
            raise GaugidAPIError(
                message=f"Token revocation failed: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            raise GaugidConnectionError(
                message=f"Failed to connect to Gaugid API: {e}",
                original_error=e,
            ) from e

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self._client.aclose()

    async def __aenter__(self) -> "OAuthFlow":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
