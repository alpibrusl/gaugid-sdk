"""
GaugidClient - High-level client for Gaugid service integration.

This client wraps A2PClient with Gaugid-specific conveniences:
- Simplified initialization with connection tokens
- Profile selection helpers
- Gaugid-specific error handling
- Automatic retry logic
"""

from typing import Any, Optional, TYPE_CHECKING
import httpx
from a2p.client import A2PClient

from gaugid.storage import GaugidStorage
from gaugid.types import GaugidError
from gaugid.utils import generate_agent_did, validate_gaugid_did
from gaugid.logger import get_logger

if TYPE_CHECKING:
    from gaugid.types import OAuthTokenResponse

logger = get_logger("client")


class GaugidClient:
    """
    High-level client for interacting with Gaugid service.

    This client wraps A2PClient and provides a simplified interface
    for working with Gaugid profiles and memories.

    Example:
        ```python
        # Basic usage (manual DID)
        from gaugid import GaugidClient
        
        client = GaugidClient(connection_token="gaugid_conn_xxx")
        profile = await client.get_profile(
            user_did="did:a2p:user:gaugid:alice",
            scopes=["a2p:preferences", "a2p:interests"]
        )
        
        # User-friendly usage (from OAuth)
        from gaugid import GaugidClient
        from gaugid.auth import OAuthFlow
        
        flow = OAuthFlow(...)
        token_response = await flow.exchange_code(code, state)
        
        # Create client with user account info
        client = GaugidClient.from_oauth_response(token_response)
        
        # List and select profile
        profiles = await client.list_profiles()
        if profiles:
            client.select_profile(profiles[0]["did"])
        
        # Use selected profile (no DID needed!)
        profile = await client.get_current_profile(scopes=["a2p:preferences"])
        ```
    """

    def __init__(
        self,
        connection_token: str,
        api_url: Optional[str] = None,
        agent_did: Optional[str] = None,
        namespace: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Initialize Gaugid client.

        Args:
            connection_token: Gaugid connection token for authentication
            api_url: Base URL of the Gaugid API (optional, defaults to production)
            agent_did: Optional agent DID for identification (must include namespace)
            namespace: Namespace for agent DID generation (if agent_did not provided)
                       Can also be set via GAUGID_NAMESPACE environment variable
            timeout: HTTP request timeout in seconds
        """
        # Validate agent_did if provided
        if agent_did:
            is_valid, error = validate_gaugid_did(agent_did)
            if not is_valid:
                raise ValueError(f"Invalid agent DID: {error}")
        else:
            # Generate default agent DID; default namespace is "gaugid" when not provided
            import os
            _namespace = namespace or os.getenv("GAUGID_NAMESPACE") or "gaugid"
            agent_did = generate_agent_did(name="default", namespace=_namespace)

        # Create GaugidStorage with connection token
        storage = GaugidStorage(
            connection_token=connection_token,
            api_url=api_url,
            agent_did=agent_did,
            timeout=timeout,
        )

        # Create A2PClient with the storage
        self._client = A2PClient(agent_did=agent_did, storage=storage)

        self.storage = storage
        self.connection_token = connection_token
        
        # User account information (set from OAuth response)
        self._user_did: Optional[str] = None
        self._available_profiles: list[dict[str, Any]] = []
        self._selected_profile_did: Optional[str] = None

    async def get_profile(
        self,
        user_did: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        sub_profile: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get a user's profile with the specified scopes.

        Supports both DID mode and connection token mode:
        - DID mode: Provide user_did to get a specific profile
        - Connection token mode: Omit user_did to get profile from token context

        Args:
            user_did: User profile DID (optional for connection token mode)
                     Must include namespace if provided (e.g., "did:a2p:user:gaugid:alice")
            scopes: List of scopes to request (e.g., ["a2p:preferences", "a2p:interests"])
            sub_profile: Optional sub-profile identifier

        Returns:
            Filtered profile dictionary

        Raises:
            ValueError: If user_did is invalid or missing namespace (when provided)
            GaugidError: On errors
        """
        scopes = scopes or []
        
        # Connection token mode: no DID required
        if user_did is None:
            import httpx
            from urllib.parse import urlencode
            
            # Build query parameters
            params = {}
            if scopes:
                params["scopes"] = ",".join(scopes)
            
            url = f"{self.storage.api_url}/a2p/v1/profile"
            if params:
                url += f"?{urlencode(params)}"
            
            headers = {
                "Authorization": f"Bearer {self.connection_token}",
            }
            
            try:
                async with httpx.AsyncClient(timeout=self.storage.timeout) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get("success"):
                        from gaugid.types import parse_gaugid_error
                        raise parse_gaugid_error(response)
                    
                    return data.get("data", {})
            except httpx.HTTPStatusError as e:
                from gaugid.types import parse_gaugid_error
                raise parse_gaugid_error(e.response) from e
            except httpx.RequestError as e:
                from gaugid.types import GaugidConnectionError
                raise GaugidConnectionError(
                    message=f"Failed to connect to Gaugid API: {e}",
                    original_error=e,
                ) from e
        
        # DID mode: validate and use base client
        is_valid, error = validate_gaugid_did(user_did)
        if not is_valid:
            raise ValueError(f"Invalid user DID: {error}")

        try:
            return await self._client.get_profile(
                user_did=user_did,
                scopes=scopes,
                sub_profile=sub_profile,
            )
        except Exception as e:
            if isinstance(e, GaugidError):
                raise
            raise GaugidError(f"Failed to get profile: {e}") from e

    async def request_access(
        self,
        scopes: list[str],
        user_did: Optional[str] = None,
        sub_profile: Optional[str] = None,
        purpose: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Request access to additional scopes.

        Supports both DID mode and connection token mode:
        - Connection token mode: Omit user_did (recommended)
        - DID mode: Provide user_did for direct access

        Args:
            scopes: List of scopes to request
            user_did: User profile DID (optional for connection token mode, must include namespace if provided)
            sub_profile: Optional sub-profile identifier
            purpose: Optional purpose object with:
                    - type: Purpose type (e.g., "memory_retrieval")
                    - description: Human-readable description
                    - legalBasis: Legal basis (e.g., "user_consent")

        Returns:
            Dictionary with receiptId, grantedScopes, deniedScopes, etc.

        Raises:
            ValueError: If user_did is invalid or missing namespace (when provided)
            GaugidError: On errors
        """
        # Connection token mode: no DID required
        if user_did is None:
            import httpx
            import json
            
            url = f"{self.storage.api_url}/a2p/v1/profile/access"
            
            payload = {
                "scopes": scopes,
            }
            if purpose:
                payload["purpose"] = purpose
            
            headers = {
                "Authorization": f"Bearer {self.connection_token}",
                "Content-Type": "application/json",
            }
            
            try:
                async with httpx.AsyncClient(timeout=self.storage.timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get("success"):
                        from gaugid.types import parse_gaugid_error
                        raise parse_gaugid_error(response)
                    
                    return data.get("data", {})
            except httpx.HTTPStatusError as e:
                from gaugid.types import parse_gaugid_error
                raise parse_gaugid_error(e.response) from e
            except httpx.RequestError as e:
                from gaugid.types import GaugidConnectionError
                raise GaugidConnectionError(
                    message=f"Failed to connect to Gaugid API: {e}",
                    original_error=e,
                ) from e
        
        # DID mode: validate and use base client
        is_valid, error = validate_gaugid_did(user_did)
        if not is_valid:
            raise ValueError(f"Invalid user DID: {error}")

        # Convert purpose dict to string for base client if needed
        purpose_str = None
        if purpose:
            if isinstance(purpose, dict):
                purpose_str = purpose.get("description") or str(purpose)
            else:
                purpose_str = str(purpose)

        try:
            return await self._client.request_access(
                user_did=user_did,
                scopes=scopes,
                sub_profile=sub_profile,
                purpose=purpose_str,
            )
        except Exception as e:
            if isinstance(e, GaugidError):
                raise
            raise GaugidError(f"Failed to request access: {e}") from e

    async def propose_memory(
        self,
        content: str,
        user_did: Optional[str] = None,
        category: Optional[str] = None,
        memory_type: Optional[str] = None,
        confidence: float = 0.7,
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Propose a new memory to a user's profile.

        Supports both DID mode and connection token mode:
        - Connection token mode: Omit user_did (recommended)
        - DID mode: Provide user_did for direct access

        Args:
            content: Memory content
            user_did: User profile DID (optional for connection token mode, must include namespace if provided)
            category: Memory category (optional, e.g., "a2p:travel_preferences")
            memory_type: Memory type - "episodic", "semantic", or "procedural" (optional)
            confidence: Confidence level (0.0-1.0)
            context: Additional context (optional)

        Returns:
            Dictionary with proposal_id and status

        Raises:
            ValueError: If user_did is invalid or missing namespace (when provided)
            GaugidError: On errors
        """
        # Connection token mode: no DID required
        if user_did is None:
            import httpx
            import json
            
            url = f"{self.storage.api_url}/a2p/v1/profile/memories/propose"
            
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
                async with httpx.AsyncClient(timeout=self.storage.timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    if not data.get("success"):
                        from gaugid.types import parse_gaugid_error
                        raise parse_gaugid_error(response)
                    
                    return data.get("data", {})
            except httpx.HTTPStatusError as e:
                from gaugid.types import parse_gaugid_error
                raise parse_gaugid_error(e.response) from e
            except httpx.RequestError as e:
                from gaugid.types import GaugidConnectionError
                raise GaugidConnectionError(
                    message=f"Failed to connect to Gaugid API: {e}",
                    original_error=e,
                ) from e
        
        # DID mode: validate and use storage
        is_valid, error = validate_gaugid_did(user_did)
        if not is_valid:
            raise ValueError(f"Invalid user DID: {error}")

        try:
            return await self.storage.propose_memory(
                user_did=user_did,
                content=content,
                category=category,
                memory_type=memory_type,
                confidence=confidence,
                context=context,
            )
        except Exception as e:
            if isinstance(e, GaugidError):
                raise
            raise GaugidError(f"Failed to propose memory: {e}") from e

    async def check_permission(
        self,
        user_did: str,
        permission: str,
        scope: Optional[str] = None,
    ) -> bool:
        """
        Check if agent has a specific permission for a user.

        Args:
            user_did: User profile DID (must include namespace)
            permission: Permission level to check
            scope: Optional scope to check

        Returns:
            True if permission is granted, False otherwise

        Raises:
            ValueError: If user_did is invalid or missing namespace
            GaugidError: On errors
        """
        # Validate user DID format
        is_valid, error = validate_gaugid_did(user_did)
        if not is_valid:
            raise ValueError(f"Invalid user DID: {error}")

        try:
            # Import PermissionLevel from a2p
            from a2p.types import PermissionLevel

            # Convert string to PermissionLevel if needed
            if isinstance(permission, str):
                perm_level = PermissionLevel[permission.upper()]
            else:
                perm_level = permission

            return await self._client.check_permission(
                user_did=user_did,
                permission=perm_level,
                scope=scope,
            )
        except Exception as e:
            if isinstance(e, GaugidError):
                raise
            raise GaugidError(f"Failed to check permission: {e}") from e

    @classmethod
    def from_oauth_response(
        cls,
        oauth_response: "OAuthTokenResponse",
        api_url: Optional[str] = None,
        agent_did: Optional[str] = None,
        namespace: Optional[str] = None,
        timeout: float = 30.0,
    ) -> "GaugidClient":
        """
        Create a GaugidClient from an OAuth token response.
        
        This automatically sets up the client with the user's DID and available profiles
        from the OAuth response, making it easier to work with user accounts.
        
        Args:
            oauth_response: OAuth token response from OAuthFlow.exchange_code()
            api_url: Base URL of the Gaugid API (optional)
            agent_did: Optional agent DID for identification
            namespace: Namespace for agent DID generation (if agent_did not provided)
            timeout: HTTP request timeout in seconds
            
        Returns:
            GaugidClient instance configured with user account information
            
        Example:
            ```python
            from gaugid import GaugidClient
            from gaugid.auth import OAuthFlow
            
            flow = OAuthFlow(...)
            token_response = await flow.exchange_code(code, state)
            
            # Create client with user account info
            client = GaugidClient.from_oauth_response(token_response)
            
            # List available profiles
            profiles = await client.list_profiles()
            
            # Select a profile (or use default)
            if profiles:
                await client.select_profile(profiles[0]["did"])
            
            # Use the selected profile
            profile = await client.get_current_profile(scopes=["a2p:preferences"])
            ```
        """
        from gaugid.types import OAuthTokenResponse
        
        client = cls(
            connection_token=oauth_response.access_token,
            api_url=api_url,
            agent_did=agent_did,
            namespace=namespace,
            timeout=timeout,
        )
        
        # Set user account information from OAuth response
        client._user_did = oauth_response.user_did
        client._available_profiles = oauth_response.profiles or []
        
        # Auto-select if only one profile (accept "did" or "id" for profile identifier)
        if len(client._available_profiles) == 1:
            profile_did = client._available_profiles[0].get("did") or client._available_profiles[0].get("id")
            if profile_did:
                client._selected_profile_did = profile_did
        
        return client
    
    async def list_profiles(self) -> list[dict[str, Any]]:
        """
        List available profiles for the authenticated user.
        
        Returns:
            List of profile dictionaries with 'did' and other metadata
            
        Example:
            ```python
            profiles = await client.list_profiles()
            for profile in profiles:
                logger.info(f"Profile: {profile['did']} - {profile.get('name', 'Unnamed')}")
            ```
        """
        # If we have profiles from OAuth, return them
        if self._available_profiles:
            return self._available_profiles
        
        # Otherwise, if we have user_did, return it as the only profile
        if self._user_did:
            return [{"did": self._user_did, "type": "user"}]
        
        # No profiles available
        return []
    
    def select_profile(self, profile_did: str) -> None:
        """
        Select a profile to use for subsequent operations.
        
        Args:
            profile_did: The DID of the profile to select
            
        Raises:
            ValueError: If profile_did is not in available profiles
            
        Example:
            ```python
            profiles = await client.list_profiles()
            client.select_profile(profiles[0]["did"])
            ```
        """
        # Validate DID format
        is_valid, error = validate_gaugid_did(profile_did)
        if not is_valid:
            raise ValueError(f"Invalid profile DID: {error}")
        
        # Check if profile is available (accept "did" or "id" in profile dicts)
        available_dids = [
            p.get("did") or p.get("id") for p in self._available_profiles
            if p.get("did") or p.get("id")
        ]
        if self._user_did:
            available_dids.append(self._user_did)
        
        if profile_did not in available_dids:
            raise ValueError(
                f"Profile {profile_did} is not available. "
                f"Available profiles: {available_dids}"
            )
        
        self._selected_profile_did = profile_did
    
    def get_current_profile_did(self) -> Optional[str]:
        """
        Get the currently selected profile DID.
        
        Returns:
            Selected profile DID, or None if no profile selected
            
        Example:
            ```python
            current_did = client.get_current_profile_did()
            if current_did:
                logger.info(f"Using profile: {current_did}")
            ```
        """
        return self._selected_profile_did or self._user_did
    
    async def get_current_profile(
        self,
        scopes: list[str],
        sub_profile: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get the currently selected profile.
        
        This is a convenience method that uses the selected profile DID
        (or user_did if no profile is selected).
        If no profile is selected and using connection token mode, uses token context.
        
        Args:
            scopes: List of scopes to request
            sub_profile: Optional sub-profile identifier
            
        Returns:
            Filtered profile dictionary
            
        Raises:
            ValueError: If no profile is selected or available (in DID mode)
            
        Example:
            ```python
            # After OAuth login and profile selection
            profile = await client.get_current_profile(
                scopes=["a2p:preferences", "a2p:interests"]
            )
            
            # Or in connection token mode (no profile selection needed)
            profile = await client.get_current_profile(
                scopes=["a2p:preferences", "a2p:interests"]
            )
            ```
        """
        profile_did = self.get_current_profile_did()
        
        # If no profile selected, use connection token mode (no DID)
        if not profile_did:
            return await self.get_profile(
                scopes=scopes,
                sub_profile=sub_profile,
            )
        
        return await self.get_profile(
            user_did=profile_did,
            scopes=scopes,
            sub_profile=sub_profile,
        )
    
    async def propose_memory_to_current(
        self,
        content: str,
        category: Optional[str] = None,
        memory_type: Optional[str] = None,
        confidence: float = 0.7,
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Propose a memory to the currently selected profile.
        
        This is a convenience method that uses the selected profile DID.
        If no profile is selected and using connection token mode, uses token context.
        
        Args:
            content: Memory content
            category: Memory category (optional)
            memory_type: Memory type - "episodic", "semantic", or "procedural" (optional)
            confidence: Confidence level (0.0-1.0)
            context: Additional context (optional)
            
        Returns:
            Dictionary with proposal_id and status
            
        Raises:
            ValueError: If no profile is selected or available (in DID mode)
        """
        profile_did = self.get_current_profile_did()
        
        # If no profile selected, use connection token mode (no DID)
        if not profile_did:
            return await self.propose_memory(
                content=content,
                category=category,
                memory_type=memory_type,
                confidence=confidence,
                context=context,
            )
        
        return await self.propose_memory(
            content=content,
            user_did=profile_did,
            category=category,
            memory_type=memory_type,
            confidence=confidence,
            context=context,
        )
    
    async def resolve_did(self, did: str) -> dict[str, Any]:
        """
        Resolve a DID to its DID document (protocol-compliant).

        This method calls the a2p protocol DID resolution endpoint.

        Args:
            did: DID to resolve (e.g., "did:a2p:agent:gaugid:my-agent")

        Returns:
            DID document dictionary with verification methods

        Raises:
            GaugidAPIError: On API errors
            GaugidConnectionError: On connection errors

        Example:
            ```python
            did_doc = await client.resolve_did("did:a2p:agent:gaugid:my-agent")
            logger.info(f"Agent DID: {did_doc['id']}")
            logger.debug(f"Public key: {did_doc['verificationMethod'][0]['publicKeyMultibase']}")
            ```
        """
        import httpx

        # Validate DID format
        is_valid, error = validate_gaugid_did(did)
        if not is_valid:
            raise ValueError(f"Invalid DID: {error}")

        # DID resolution is a public endpoint (no auth required)
        api_url = self.storage.api_url
        url = f"{api_url}/a2p/v1/did/{did}"

        try:
            async with httpx.AsyncClient(timeout=self.storage.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if not data.get("success"):
                    raise GaugidAPIError(
                        message=data.get("error", {}).get("message", "DID resolution failed"),
                        status_code=response.status_code,
                        code=data.get("error", {}).get("code"),
                    )

                return data.get("data", {})
        except httpx.HTTPStatusError as e:
            from gaugid.types import parse_gaugid_error
            raise parse_gaugid_error(e.response) from e
        except httpx.RequestError as e:
            from gaugid.types import GaugidConnectionError
            raise GaugidConnectionError(
                message=f"Failed to resolve DID: {e}",
                original_error=e,
            ) from e

    async def register_agent(
        self,
        agent_did: str,
        name: str,
        description: Optional[str] = None,
        owner_email: Optional[str] = None,
        public_key: Optional[str] = None,
        generate_keys: bool = False,
    ) -> dict[str, Any]:
        """
        Register an agent with Gaugid (protocol-compliant).

        This method calls the a2p protocol agent registration endpoint.
        Supports both A2P-Signature and Bearer token authentication.

        Args:
            agent_did: Agent DID (must include namespace, e.g., "did:a2p:agent:gaugid:my-agent")
            name: Agent name
            description: Optional agent description
            owner_email: Optional owner email
            public_key: Optional base64-encoded Ed25519 public key
            generate_keys: If True, server generates keypair (returns private key)

        Returns:
            Dictionary with agent info, DID document, and optionally private key

        Raises:
            ValueError: If agent_did is invalid
            GaugidAPIError: On API errors
            GaugidConnectionError: On connection errors

        Example:
            ```python
            # Register with existing public key
            result = await client.register_agent(
                agent_did="did:a2p:agent:gaugid:my-assistant",
                name="My Assistant",
                description="A helpful AI assistant",
                public_key="base64_encoded_public_key"
            )
            logger.info(f"Agent registered: {result['agent']['did']}")

            # Register with server-generated keys
            result = await client.register_agent(
                agent_did="did:a2p:agent:gaugid:my-assistant",
                name="My Assistant",
                generate_keys=True
            )
            private_key = result.get("privateKey")
            # Store private_key securely!
            ```
        """
        import httpx
        import json

        # Validate agent DID format
        is_valid, error = validate_gaugid_did(agent_did)
        if not is_valid:
            raise ValueError(f"Invalid agent DID: {error}")

        # Build request payload
        payload: dict[str, Any] = {
            "did": agent_did,
            "name": name,
            "keyType": "Ed25519",
            "generateKeys": generate_keys,
        }

        if description:
            payload["description"] = description
        if owner_email:
            payload["ownerEmail"] = owner_email
        if public_key:
            payload["publicKey"] = public_key

        # Use protocol-compliant endpoint
        api_url = self.storage.api_url
        url = f"{api_url}/a2p/v1/agents/register"

        # Use connection token for authentication (Bearer token)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.storage.connection_token}",
        }

        try:
            async with httpx.AsyncClient(timeout=self.storage.timeout) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    content=json.dumps(payload),
                )
                response.raise_for_status()
                data = response.json()

                if not data.get("success"):
                    raise GaugidAPIError(
                        message=data.get("error", {}).get("message", "Agent registration failed"),
                        status_code=response.status_code,
                        code=data.get("error", {}).get("code"),
                    )

                return data.get("data", {})
        except httpx.HTTPStatusError as e:
            from gaugid.types import parse_gaugid_error
            raise parse_gaugid_error(e.response) from e
        except httpx.RequestError as e:
            from gaugid.types import GaugidConnectionError
            raise GaugidConnectionError(
                message=f"Failed to register agent: {e}",
                original_error=e,
            ) from e

    async def close(self) -> None:
        """Close the client and cleanup resources."""
        await self.storage.close()

    def __enter__(self) -> "GaugidClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        # Note: This is sync, but close() is async
        # In practice, use async context manager
        pass

    async def __aenter__(self) -> "GaugidClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
