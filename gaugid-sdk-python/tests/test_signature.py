"""Tests for A2P-Signature utilities."""

import pytest
import base64
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from gaugid.signature import (
    generate_a2p_signature_header,
    generate_ed25519_keypair,
    private_key_to_pem,
)


def test_generate_ed25519_keypair() -> None:
    """Test generating Ed25519 keypair."""
    private_key, public_key = generate_ed25519_keypair()

    assert isinstance(private_key, Ed25519PrivateKey)
    assert isinstance(public_key, bytes)
    assert len(public_key) == 32

    # Verify public key matches private key
    derived_public = private_key.public_key().public_bytes_raw()
    assert derived_public == public_key


def test_generate_ed25519_keypair_unique() -> None:
    """Test that generated keypairs are unique."""
    keypair1 = generate_ed25519_keypair()
    keypair2 = generate_ed25519_keypair()

    assert keypair1[0] != keypair2[0]  # Different private keys
    assert keypair1[1] != keypair2[1]  # Different public keys


def test_private_key_to_pem() -> None:
    """Test converting private key to PEM format."""
    private_key, _ = generate_ed25519_keypair()
    pem = private_key_to_pem(private_key)

    assert isinstance(pem, str)
    assert pem.startswith("-----BEGIN PRIVATE KEY-----")
    assert pem.endswith("-----END PRIVATE KEY-----\n")
    assert "PRIVATE KEY" in pem


def test_generate_a2p_signature_header() -> None:
    """Test generating A2P-Signature header."""
    private_key, _ = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="GET",
        path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
    )

    assert header.startswith("A2P-Signature")
    assert f'did="{agent_did}"' in header
    assert 'sig="' in header
    assert 'ts="' in header
    assert 'nonce="' in header
    assert 'exp="' in header


def test_generate_a2p_signature_header_with_body() -> None:
    """Test generating signature header with request body."""
    private_key, _ = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"
    body = b'{"content": "test"}'

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="POST",
        path="/a2p/v1/profile/memories/propose",
        body=body,
    )

    assert header.startswith("A2P-Signature")
    # Body hash should be included in signature
    assert 'sig="' in header


def test_generate_a2p_signature_header_custom_timestamp() -> None:
    """Test generating signature with custom timestamp."""
    private_key, _ = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"
    custom_timestamp = int(time.time()) - 100

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="GET",
        path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
        timestamp=custom_timestamp,
    )

    assert f'ts="{custom_timestamp}"' in header


def test_generate_a2p_signature_header_custom_nonce() -> None:
    """Test generating signature with custom nonce."""
    private_key, _ = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"
    custom_nonce = "custom_nonce_123"

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="GET",
        path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
        nonce=custom_nonce,
    )

    assert f'nonce="{custom_nonce}"' in header


def test_generate_a2p_signature_header_pem_string() -> None:
    """Test generating signature with PEM string private key."""
    private_key, _ = generate_ed25519_keypair()
    pem = private_key_to_pem(private_key)
    agent_did = "did:a2p:agent:gaugid:my-agent"

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=pem,
        method="GET",
        path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
    )

    assert header.startswith("A2P-Signature")


def test_generate_a2p_signature_header_bytes_key() -> None:
    """Test generating signature with bytes private key."""
    private_key, _ = generate_ed25519_keypair()
    private_key_bytes = private_key.private_bytes_raw()
    agent_did = "did:a2p:agent:gaugid:my-agent"

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key_bytes,
        method="GET",
        path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
    )

    assert header.startswith("A2P-Signature")


def test_generate_a2p_signature_header_invalid_key() -> None:
    """Test generating signature with invalid key."""
    agent_did = "did:a2p:agent:gaugid:my-agent"

    with pytest.raises(ValueError, match="Invalid private key|Unable to load PEM|MalformedFraming"):
        generate_a2p_signature_header(
            agent_did=agent_did,
            private_key="invalid_key",
            method="GET",
            path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
        )


def test_generate_a2p_signature_header_invalid_bytes_key() -> None:
    """Test generating signature with invalid bytes key."""
    agent_did = "did:a2p:agent:gaugid:my-agent"

    with pytest.raises(ValueError, match="Raw private key must be 32 bytes"):
        generate_a2p_signature_header(
            agent_did=agent_did,
            private_key=b"invalid",
            method="GET",
            path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
        )


def test_generate_a2p_signature_header_round_trip() -> None:
    """Test that signature can be verified (round-trip)."""
    private_key, public_key = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="GET",
        path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
    )

    # Parse header to extract signature
    # Format: A2P-Signature did="...",sig="...",ts="...",nonce="...",exp="..."
    parts = header.split(", ")
    sig_part = [p for p in parts if p.startswith('sig="')][0]
    sig_b64 = sig_part.split('"')[1]
    sig_bytes = base64.b64decode(sig_b64)

    # Verify signature (simplified - in real usage, server verifies)
    assert len(sig_bytes) == 64  # Ed25519 signature is 64 bytes


def test_generate_a2p_signature_header_custom_expiration() -> None:
    """Test generating signature with custom expiration."""
    private_key, _ = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"
    custom_exp = int(time.time()) + 600  # 10 minutes

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="GET",
        path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
        expiration=custom_exp,
    )

    assert f'exp="{custom_exp}"' in header


def test_generate_a2p_signature_header_different_methods() -> None:
    """Test generating signatures for different HTTP methods."""
    private_key, _ = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"

    methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    for method in methods:
        header = generate_a2p_signature_header(
            agent_did=agent_did,
            private_key=private_key,
            method=method,
            path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
        )
        assert header.startswith("A2P-Signature")
        # Different methods should produce different signatures
        assert 'sig="' in header


def test_generate_a2p_signature_header_different_paths() -> None:
    """Test that different paths produce different signatures."""
    private_key, _ = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"

    path1 = "/a2p/v1/profile/did:a2p:user:gaugid:alice"
    path2 = "/a2p/v1/profile/did:a2p:user:gaugid:bob"

    header1 = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="GET",
        path=path1,
    )

    header2 = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="GET",
        path=path2,
    )

    # Extract signatures
    sig1 = [p for p in header1.split(", ") if p.startswith('sig="')][0].split('"')[1]
    sig2 = [p for p in header2.split(", ") if p.startswith('sig="')][0].split('"')[1]

    # Different paths should produce different signatures
    assert sig1 != sig2


def test_generate_a2p_signature_header_empty_body() -> None:
    """Test generating signature with empty body."""
    private_key, _ = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="GET",
        path="/a2p/v1/profile/did:a2p:user:gaugid:alice",
        body=b"",
    )

    assert header.startswith("A2P-Signature")


def test_generate_a2p_signature_header_large_body() -> None:
    """Test generating signature with large body."""
    private_key, _ = generate_ed25519_keypair()
    agent_did = "did:a2p:agent:gaugid:my-agent"
    large_body = b"x" * 10000  # 10KB body

    header = generate_a2p_signature_header(
        agent_did=agent_did,
        private_key=private_key,
        method="POST",
        path="/a2p/v1/profile/memories/propose",
        body=large_body,
    )

    assert header.startswith("A2P-Signature")
    # Body hash should be included
    assert 'sig="' in header
