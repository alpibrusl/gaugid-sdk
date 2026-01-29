"""
A2P-Signature authentication utilities for protocol-compliant authentication.

This module provides functions for generating A2P-Signature headers as required
by the a2p protocol specification.
"""

import base64
import secrets
import time
from typing import Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def generate_a2p_signature_header(
    agent_did: str,
    private_key: str | bytes | Ed25519PrivateKey,
    method: str,
    path: str,
    body: Optional[bytes] = None,
    timestamp: Optional[int] = None,
    nonce: Optional[str] = None,
    expiration: Optional[int] = None,
) -> str:
    """
    Generate an A2P-Signature authorization header for protocol-compliant authentication.

    Args:
        agent_did: Agent DID (e.g., "did:a2p:agent:gaugid:my-agent")
        private_key: Ed25519 private key (PEM string, bytes, or Ed25519PrivateKey object)
        method: HTTP method (e.g., "GET", "POST")
        path: Request path (e.g., "/a2p/v1/profile/did:a2p:user:gaugid:alice")
        body: Optional request body bytes
        timestamp: Optional Unix timestamp (defaults to current time)
        nonce: Optional random nonce (auto-generated if not provided)
        expiration: Optional expiration timestamp in seconds (defaults to 300 seconds)

    Returns:
        Authorization header value: 'A2P-Signature did="...",sig="...",ts="...",nonce="..."'

    Example:
        >>> private_key = Ed25519PrivateKey.generate()
        >>> header = generate_a2p_signature_header(
        ...     agent_did="did:a2p:agent:gaugid:my-agent",
        ...     private_key=private_key,
        ...     method="GET",
        ...     path="/a2p/v1/profile/did:a2p:user:gaugid:alice"
        ... )
        >>> # Use in request: headers["Authorization"] = header
    """
    # Parse private key if needed
    if isinstance(private_key, str):
        # Assume PEM format
        private_key_bytes = private_key.encode("utf-8")
        key = serialization.load_pem_private_key(private_key_bytes, password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise ValueError("Private key must be Ed25519")
    elif isinstance(private_key, bytes):
        # Try PEM first, then raw
        try:
            key = serialization.load_pem_private_key(private_key, password=None)
            if not isinstance(key, Ed25519PrivateKey):
                raise ValueError("Private key must be Ed25519")
        except Exception:
            # Try raw 32-byte key
            if len(private_key) != 32:
                raise ValueError("Raw private key must be 32 bytes")
            key = Ed25519PrivateKey.from_private_bytes(private_key)
    elif isinstance(private_key, Ed25519PrivateKey):
        key = private_key
    else:
        raise ValueError("Invalid private key type")

    # Generate timestamp and nonce if not provided
    if timestamp is None:
        timestamp = int(time.time())
    if nonce is None:
        nonce = secrets.token_urlsafe(32)
    if expiration is None:
        expiration = timestamp + 300  # 5 minutes default

    # Build signature string (canonical request format)
    # Format: method\npath\nbody_hash\ntimestamp\nnonce\nexpiration
    body_hash = ""
    if body:
        import hashlib
        body_hash = base64.b64encode(hashlib.sha256(body).digest()).decode("utf-8")

    signature_string = f"{method}\n{path}\n{body_hash}\n{timestamp}\n{nonce}\n{expiration}"

    # Sign the canonical string
    signature_bytes = key.sign(signature_string.encode("utf-8"))
    signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

    # Build authorization header
    header_parts = [
        f'did="{agent_did}"',
        f'sig="{signature_b64}"',
        f'ts="{timestamp}"',
        f'nonce="{nonce}"',
        f'exp="{expiration}"',
    ]

    return f"A2P-Signature {', '.join(header_parts)}"


def generate_ed25519_keypair() -> tuple[Ed25519PrivateKey, bytes]:
    """
    Generate a new Ed25519 keypair for agent authentication.

    Returns:
        Tuple of (private_key, public_key_bytes)
        - private_key: Ed25519PrivateKey object
        - public_key_bytes: Raw 32-byte public key

    Example:
        >>> private_key, public_key = generate_ed25519_keypair()
        >>> # Store private_key securely
        >>> # Register public_key with agent DID
        >>> import base64
        >>> public_key_b64 = base64.b64encode(public_key).decode("utf-8")
    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    public_key_bytes = public_key.public_bytes_raw()
    return private_key, public_key_bytes


def private_key_to_pem(private_key: Ed25519PrivateKey) -> str:
    """
    Convert Ed25519PrivateKey to PEM format for storage.

    Args:
        private_key: Ed25519PrivateKey object

    Returns:
        PEM-formatted private key string

    Example:
        >>> private_key, _ = generate_ed25519_keypair()
        >>> pem = private_key_to_pem(private_key)
        >>> # Store pem string securely
    """
    pem_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem_bytes.decode("utf-8")


__all__ = [
    "generate_a2p_signature_header",
    "generate_ed25519_keypair",
    "private_key_to_pem",
]
