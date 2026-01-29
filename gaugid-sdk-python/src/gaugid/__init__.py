"""
Gaugid SDK - Python client library for Gaugid (a2p-cloud) service integration.

This SDK extends the base a2p protocol SDK with Gaugid-specific features like
OAuth flows, connection tokens, and service-specific utilities.

Licensed under the European Union Public Licence v. 1.2 (EUPL-1.2).
See LICENSE in the distribution for the full text.
"""

from gaugid.client import GaugidClient
from gaugid.storage import GaugidStorage
from gaugid.types import (
    GaugidError,
    GaugidAPIError,
    GaugidAuthError,
    GaugidConnectionError,
)
from gaugid.utils import (
    generate_user_did,
    generate_agent_did,
    validate_gaugid_did,
)
from gaugid.signature import (
    generate_a2p_signature_header,
    generate_ed25519_keypair,
    private_key_to_pem,
)
from gaugid.logger import get_logger, setup_logging

# Import submodules for easy access
from gaugid import auth, connection  # noqa: F401

__version__ = "0.1.0"
__all__ = [
    "GaugidClient",
    "GaugidStorage",
    "GaugidError",
    "GaugidAPIError",
    "GaugidAuthError",
    "GaugidConnectionError",
    "generate_user_did",
    "generate_agent_did",
    "validate_gaugid_did",
    "generate_a2p_signature_header",
    "generate_ed25519_keypair",
    "private_key_to_pem",
    "get_logger",
    "setup_logging",
    "auth",
    "connection",
]

# Optional integrations (require extra dependencies)
try:
    from gaugid.integrations import GaugidMemoryService, GaugidStore
    if "GaugidMemoryService" not in __all__:
        __all__.append("GaugidMemoryService")
    if "GaugidStore" not in __all__:
        __all__.append("GaugidStore")
except ImportError:
    # Integrations not available (gaugid[adk] or gaugid[langgraph] not installed)
    pass
