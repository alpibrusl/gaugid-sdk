"""
Gaugid-specific utilities for DID generation and validation.

This module provides helper functions for working with a2p DIDs.
Namespace must be explicitly provided - no default is set.
"""

import os
from typing import Optional

from a2p.utils.id import (
    generate_agent_did as _generate_agent_did,
    generate_user_did as _generate_user_did,
    is_valid_a2p_did,
    parse_did,
    get_namespace,
)

# Namespace can be configured via environment variable, but defaults to None
# Users should explicitly provide namespace when generating DIDs
_NAMESPACE_ENV_VAR = "GAUGID_NAMESPACE"


def _get_default_namespace() -> Optional[str]:
    """Get default namespace from environment variable, or None if not set."""
    return os.getenv(_NAMESPACE_ENV_VAR)


def generate_user_did(
    namespace: Optional[str] = None, identifier: Optional[str] = None
) -> str:
    """
    Generate a user DID with namespace.

    Args:
        namespace: Provider namespace (required, or set GAUGID_NAMESPACE env var)
        identifier: Unique identifier (auto-generated if not provided)

    Returns:
        User DID in format: did:a2p:user:<namespace>:<identifier>

    Raises:
        ValueError: If namespace is not provided and not set in environment

    Example:
        >>> generate_user_did(namespace="gaugid")
        'did:a2p:user:gaugid:AbC123XyZ789'
        >>> generate_user_did(namespace="company-a", identifier="alice")
        'did:a2p:user:company-a:alice'
    """
    if namespace is None:
        namespace = _get_default_namespace()
    if namespace is None:
        raise ValueError(
            "Namespace is required. Provide it as argument or set GAUGID_NAMESPACE environment variable."
        )
    return _generate_user_did(namespace=namespace, identifier=identifier)


def generate_agent_did(
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    identifier: Optional[str] = None,
) -> str:
    """
    Generate an agent DID with namespace.

    Args:
        name: Agent name (will be sanitized if provided)
        namespace: Provider namespace (required, or set GAUGID_NAMESPACE env var)
        identifier: Unique identifier (auto-generated if not provided)

    Returns:
        Agent DID in format: did:a2p:agent:<namespace>:<identifier>

    Raises:
        ValueError: If namespace is not provided and not set in environment

    Example:
        >>> generate_agent_did("my-assistant", namespace="gaugid")
        'did:a2p:agent:gaugid:my-assistant'
        >>> generate_agent_did("my-assistant", namespace="local")
        'did:a2p:agent:local:my-assistant'
    """
    if namespace is None:
        namespace = _get_default_namespace()
    if namespace is None:
        raise ValueError(
            "Namespace is required. Provide it as argument or set GAUGID_NAMESPACE environment variable."
        )
    return _generate_agent_did(namespace=namespace, name=name, identifier=identifier)


def validate_gaugid_did(did: str) -> tuple[bool, Optional[str]]:
    """
    Validate a DID and ensure it has a namespace.

    Args:
        did: DID string to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if DID is valid, False otherwise
        - error_message: Error message if invalid, None if valid

    Example:
        >>> validate_gaugid_did("did:a2p:user:gaugid:alice")
        (True, None)
        >>> validate_gaugid_did("did:a2p:user:alice")
        (False, 'Namespace is required in DID: did:a2p:user:alice')
    """
    if not is_valid_a2p_did(did):
        return (
            False,
            f"Invalid DID format: {did}. "
            f"Required format: did:a2p:<type>:<namespace>:<identifier>",
        )

    parsed = parse_did(did)
    if not parsed or not parsed.get("namespace"):
        return (
            False,
            f"Namespace is required in DID: {did}. "
            f"Format must be: did:a2p:<type>:<namespace>:<identifier>",
        )

    return (True, None)


__all__ = [
    "generate_user_did",
    "generate_agent_did",
    "validate_gaugid_did",
    "parse_did",
    "get_namespace",
]
