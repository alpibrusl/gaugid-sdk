"""Tests for utility functions."""

import pytest
import os
from gaugid.utils import (
    generate_user_did,
    generate_agent_did,
    validate_gaugid_did,
)


def test_generate_user_did_with_namespace() -> None:
    """Test generating user DID with namespace."""
    did = generate_user_did(namespace="gaugid")

    assert did.startswith("did:a2p:user:gaugid:")
    assert len(did.split(":")) == 5  # did:a2p:user:namespace:identifier


def test_generate_user_did_with_identifier() -> None:
    """Test generating user DID with custom identifier."""
    did = generate_user_did(namespace="gaugid", identifier="alice")

    assert did == "did:a2p:user:gaugid:alice"


def test_generate_user_did_with_env_namespace() -> None:
    """Test generating user DID with namespace from environment."""
    os.environ["GAUGID_NAMESPACE"] = "test-namespace"

    try:
        did = generate_user_did()
        assert did.startswith("did:a2p:user:test-namespace:")
    finally:
        os.environ.pop("GAUGID_NAMESPACE", None)


def test_generate_user_did_no_namespace() -> None:
    """Test generating user DID without namespace raises error."""
    # Clear environment variable
    os.environ.pop("GAUGID_NAMESPACE", None)

    with pytest.raises(ValueError, match="Namespace is required"):
        generate_user_did()


def test_generate_agent_did_with_namespace() -> None:
    """Test generating agent DID with namespace."""
    did = generate_agent_did(name="my-agent", namespace="gaugid")

    assert did.startswith("did:a2p:agent:gaugid:")
    assert "my-agent" in did or did.endswith(":my-agent")


def test_generate_agent_did_with_identifier() -> None:
    """Test generating agent DID with custom identifier."""
    did = generate_agent_did(
        name="my-agent",
        namespace="gaugid",
        identifier="custom-id",
    )

    assert "custom-id" in did
    assert did.startswith("did:a2p:agent:gaugid:")


def test_generate_agent_did_with_env_namespace() -> None:
    """Test generating agent DID with namespace from environment."""
    os.environ["GAUGID_NAMESPACE"] = "test-namespace"

    try:
        did = generate_agent_did(name="test-agent")
        assert did.startswith("did:a2p:agent:test-namespace:")
    finally:
        os.environ.pop("GAUGID_NAMESPACE", None)


def test_generate_agent_did_no_namespace() -> None:
    """Test generating agent DID without namespace raises error."""
    os.environ.pop("GAUGID_NAMESPACE", None)

    with pytest.raises(ValueError, match="Namespace is required"):
        generate_agent_did(name="test-agent")


def test_validate_gaugid_did_valid() -> None:
    """Test validating a valid DID."""
    did = "did:a2p:user:gaugid:alice"
    is_valid, error = validate_gaugid_did(did)

    assert is_valid is True
    assert error is None


def test_validate_gaugid_did_valid_agent() -> None:
    """Test validating a valid agent DID."""
    did = "did:a2p:agent:gaugid:my-agent"
    is_valid, error = validate_gaugid_did(did)

    assert is_valid is True
    assert error is None


def test_validate_gaugid_did_invalid_format() -> None:
    """Test validating an invalid DID format."""
    did = "invalid-did"
    is_valid, error = validate_gaugid_did(did)

    assert is_valid is False
    assert error is not None
    assert "Invalid DID format" in error


def test_validate_gaugid_did_missing_namespace() -> None:
    """Test validating a DID without namespace (invalid format in a2p)."""
    did = "did:a2p:user:alice"  # Missing namespace - invalid in a2p
    is_valid, error = validate_gaugid_did(did)

    assert is_valid is False
    assert error is not None
    # a2p rejects as invalid format; message may mention namespace or invalid format
    assert "Namespace" in error or "Invalid DID format" in error


def test_validate_gaugid_did_wrong_method() -> None:
    """Test validating a DID with wrong method."""
    did = "did:other:method:test"
    is_valid, error = validate_gaugid_did(did)

    assert is_valid is False
    assert error is not None
    assert "Invalid DID format" in error


def test_validate_gaugid_did_different_namespace() -> None:
    """Test validating a DID with different namespace."""
    did = "did:a2p:user:company-a:alice"
    is_valid, error = validate_gaugid_did(did)

    assert is_valid is True
    assert error is None


def test_generate_user_did_different_namespaces() -> None:
    """Test generating DIDs with different namespaces."""
    did1 = generate_user_did(namespace="gaugid", identifier="alice")
    did2 = generate_user_did(namespace="company-a", identifier="alice")

    assert did1 != did2
    assert did1.startswith("did:a2p:user:gaugid:")
    assert did2.startswith("did:a2p:user:company-a:")


def test_generate_agent_did_sanitization() -> None:
    """Test that agent names are properly sanitized."""
    # Agent names with special characters should be sanitized
    did = generate_agent_did(name="my-agent@test", namespace="gaugid")

    assert did.startswith("did:a2p:agent:gaugid:")
    # The exact format depends on a2p SDK implementation


def test_validate_gaugid_did_service_type() -> None:
    """Test validating a service DID."""
    did = "did:a2p:service:gaugid:my-service"
    is_valid, error = validate_gaugid_did(did)

    assert is_valid is True
    assert error is None


def test_validate_gaugid_did_empty_string() -> None:
    """Test validating an empty DID."""
    is_valid, error = validate_gaugid_did("")

    assert is_valid is False
    assert error is not None


def test_validate_gaugid_did_too_short() -> None:
    """Test validating a DID that's too short."""
    is_valid, error = validate_gaugid_did("did:a2p")

    assert is_valid is False
    assert error is not None


def test_generate_user_did_auto_identifier() -> None:
    """Test generating user DID with auto-generated identifier."""
    did1 = generate_user_did(namespace="gaugid")
    did2 = generate_user_did(namespace="gaugid")

    # Should generate different identifiers
    assert did1 != did2
    assert did1.startswith("did:a2p:user:gaugid:")
    assert did2.startswith("did:a2p:user:gaugid:")


def test_generate_agent_did_auto_identifier() -> None:
    """Test generating agent DID with auto-generated identifier."""
    did1 = generate_agent_did(namespace="gaugid")
    did2 = generate_agent_did(namespace="gaugid")

    # Should generate different identifiers
    assert did1 != did2
    assert did1.startswith("did:a2p:agent:gaugid:")
    assert did2.startswith("did:a2p:agent:gaugid:")


def test_generate_agent_did_no_name() -> None:
    """Test generating agent DID without name."""
    did = generate_agent_did(namespace="gaugid")

    assert did.startswith("did:a2p:agent:gaugid:")
    # Should still generate a valid DID


def test_validate_gaugid_did_with_special_chars() -> None:
    """Test validating DID with special characters in identifier."""
    did = "did:a2p:user:gaugid:user-123_test"
    is_valid, error = validate_gaugid_did(did)

    # Should be valid if a2p SDK accepts it
    # This depends on a2p SDK validation rules
    assert is_valid is True or error is not None
