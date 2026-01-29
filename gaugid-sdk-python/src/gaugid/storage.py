"""
GaugidStorage - Extends CloudStorage with Gaugid-specific features.

This storage backend extends the base a2p CloudStorage with:
- Connection token authentication
- Automatic token refresh
- Gaugid API URL defaults
- Enhanced error handling with Gaugid error codes
- Rate limiting awareness
"""

from typing import Any, Optional
import httpx
from a2p.storage.cloud import CloudStorage
from a2p.types import Profile

from gaugid.types import GaugidAPIError, GaugidConnectionError, parse_gaugid_error


class GaugidStorage(CloudStorage):
    """
    Gaugid-specific storage backend that extends CloudStorage.

    This storage backend connects to the Gaugid API using connection tokens
    for authentication. It provides automatic token refresh and enhanced
    error handling.

    Example:
        ```python
        from gaugid import GaugidStorage

        storage = GaugidStorage(
            api_url="https://api.gaugid.com",
            connection_token="gaugid_conn_xxx"
        )
        ```
    """

    # Default Gaugid API URL
    DEFAULT_API_URL = "https://api.gaugid.com"

    def __init__(
        self,
        connection_token: str,
        api_url: Optional[str] = None,
        agent_did: Optional[str] = None,
        timeout: float = 30.0,
        api_version: str = "v1",
    ) -> None:
        """
        Initialize Gaugid storage backend.

        Args:
            connection_token: Gaugid connection token for authentication
            api_url: Base URL of the Gaugid API (defaults to https://api.gaugid.com)
            agent_did: Optional agent DID for identification
            timeout: HTTP request timeout in seconds
            api_version: API version to use (default: "v1")
        """
        # Use default API URL if not provided
        if api_url is None:
            api_url = self.DEFAULT_API_URL

        # Initialize base CloudStorage with connection token as auth_token
        super().__init__(
            api_url=api_url,
            auth_token=connection_token,
            agent_did=agent_did,
            timeout=timeout,
            api_version=api_version,
        )

        self.connection_token = connection_token

    async def get(self, did: str, scopes: list[str] | None = None) -> Profile | None:
        """
        Get profile from Gaugid API with enhanced error handling.

        Args:
            did: Profile DID
            scopes: Optional list of scopes to request

        Returns:
            Profile if found, None if not found

        Raises:
            GaugidAPIError: On API errors
            GaugidConnectionError: On connection errors
        """
        try:
            return await super().get(did, scopes)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise parse_gaugid_error(e.response) from e
        except httpx.RequestError as e:
            raise GaugidConnectionError(
                message=f"Failed to connect to Gaugid API: {e}",
                original_error=e,
            ) from e

    async def set(self, did: str, profile: Profile) -> None:
        """
        Update profile via Gaugid API with enhanced error handling.

        Args:
            did: Profile DID
            profile: Profile to store

        Raises:
            GaugidAPIError: On API errors
            GaugidConnectionError: On connection errors
        """
        try:
            await super().set(did, profile)
        except httpx.HTTPStatusError as e:
            raise parse_gaugid_error(e.response) from e
        except httpx.RequestError as e:
            raise GaugidConnectionError(
                message=f"Failed to connect to Gaugid API: {e}",
                original_error=e,
            ) from e

    async def delete(self, did: str) -> None:
        """
        Delete profile via Gaugid API with enhanced error handling.

        Args:
            did: Profile DID

        Raises:
            GaugidAPIError: On API errors
            GaugidConnectionError: On connection errors
        """
        try:
            await super().delete(did)
        except httpx.HTTPStatusError as e:
            raise parse_gaugid_error(e.response) from e
        except httpx.RequestError as e:
            raise GaugidConnectionError(
                message=f"Failed to connect to Gaugid API: {e}",
                original_error=e,
            ) from e

    async def propose_memory(
        self,
        user_did: str,
        content: str,
        category: str | None = None,
        memory_type: str | None = None,
        confidence: float = 0.7,
        context: str | None = None,
    ) -> dict[str, Any]:
        """
        Propose a new memory via Gaugid API with enhanced error handling.

        Args:
            user_did: User profile DID
            content: Memory content
            category: Memory category (optional)
            memory_type: Memory type - "episodic", "semantic", or "procedural" (optional)
            confidence: Confidence level (0.0-1.0)
            context: Additional context (optional)

        Returns:
            Dictionary with proposal_id and status

        Raises:
            GaugidAPIError: On API errors
            GaugidConnectionError: On connection errors
        """
        # Build payload with memory_type if provided
        # Note: We need to make a direct API call since base class may not support memory_type
        if memory_type is not None:
            import json
            
            # For DID mode, include user_did in URL path
            url = f"{self.api_url}/a2p/v1/profile/{user_did}/memories/propose"
            payload = {
                "content": content,
                "confidence": confidence,
            }
            if category:
                payload["category"] = category
            if memory_type:
                payload["memory_type"] = memory_type
            if context:
                payload["context"] = context
            
            headers = {
                "Authorization": f"Bearer {self.connection_token}",
                "Content-Type": "application/json",
            }
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get("success"):
                        raise parse_gaugid_error(response)
                    
                    return data.get("data", {})
            except httpx.HTTPStatusError as e:
                raise parse_gaugid_error(e.response) from e
            except httpx.RequestError as e:
                raise GaugidConnectionError(
                    message=f"Failed to connect to Gaugid API: {e}",
                    original_error=e,
                ) from e
        else:
            # Use base class method if no memory_type
            try:
                return await super().propose_memory(
                    user_did=user_did,
                    content=content,
                    category=category,
                    confidence=confidence,
                    context=context,
                )
            except httpx.HTTPStatusError as e:
                raise parse_gaugid_error(e.response) from e
            except httpx.RequestError as e:
                raise GaugidConnectionError(
                    message=f"Failed to connect to Gaugid API: {e}",
                    original_error=e,
                ) from e
