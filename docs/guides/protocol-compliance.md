# Protocol Compliance

Gaugid is **100% compliant** with the a2p protocol specification v0.1.0. This document outlines the protocol features supported by Gaugid and how to use them.

## Compliance Status

✅ **100% Protocol Compliant**

All required a2p protocol endpoints and features are fully implemented:

- ✅ A2P-Signature authentication (Ed25519)
- ✅ DID resolution (W3C-compliant)
- ✅ Agent registration
- ✅ Profile operations
- ✅ Memory operations (episodic, semantic, procedural)
- ✅ Access requests
- ✅ Proposal workflow
- ✅ Namespace-based DIDs

## Authentication Methods

Gaugid supports **both** authentication methods:

### 1. Connection Tokens (Convenience)

**Best for**: Service connections, OAuth-based flows

```python
from gaugid import GaugidClient

client = GaugidClient(connection_token="gaugid_conn_xxx")
```

**Benefits**:
- ✅ User-friendly OAuth flow
- ✅ Easy to revoke
- ✅ Better UX for service connections

### 2. A2P-Signature (Protocol-Native)

**Best for**: Agent-to-agent communication, protocol interoperability

```python
from gaugid import generate_ed25519_keypair, generate_a2p_signature_header
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Generate keypair
private_key, public_key = generate_ed25519_keypair()

# Register agent with public key
client = GaugidClient(connection_token="gaugid_conn_xxx")
await client.register_agent(
    agent_did="did:a2p:agent:gaugid:my-agent",
    name="My Agent",
    public_key=base64.b64encode(public_key).decode("utf-8")
)

# Use A2P-Signature for requests
header = generate_a2p_signature_header(
    agent_did="did:a2p:agent:gaugid:my-agent",
    private_key=private_key,
    method="GET",
    path="/a2p/v1/profile/did:a2p:user:gaugid:alice"
)
```

**Benefits**:
- ✅ Decentralized (no token management)
- ✅ Protocol-native
- ✅ Works across providers
- ✅ No token expiration

## DID Resolution

Resolve any DID to its DID document:

```python
# Resolve agent DID
did_doc = await client.resolve_did("did:a2p:agent:gaugid:my-agent")
print(f"Public key: {did_doc['verificationMethod'][0]['publicKeyMultibase']}")

# Resolve user DID
did_doc = await client.resolve_did("did:a2p:user:gaugid:alice")
```

**Endpoint**: `GET /a2p/v1/did/:did`  
**Auth**: Public (no authentication required)  
**Returns**: W3C-compliant DID document

## Agent Registration

Register agents with public keys:

```python
# Register with existing public key
result = await client.register_agent(
    agent_did="did:a2p:agent:gaugid:my-agent",
    name="My Agent",
    description="A helpful AI assistant",
    public_key="base64_encoded_public_key"
)

# Or let server generate keys
result = await client.register_agent(
    agent_did="did:a2p:agent:gaugid:my-agent",
    name="My Agent",
    generate_keys=True
)
private_key = result.get("privateKey")  # Store securely!
```

**Endpoint**: `POST /a2p/v1/agents/register`  
**Auth**: A2P-Signature or Bearer token  
**Returns**: Agent info, DID document, optionally private key

## Protocol Endpoints

All a2p protocol endpoints are supported:

| Endpoint | Method | Auth | Status |
|----------|--------|------|--------|
| `/a2p/v1/profile/:did` | GET | A2P-Signature or Connection Token | ✅ |
| `/a2p/v1/profile/:did` | POST | A2P-Signature | ✅ |
| `/a2p/v1/profile/:did` | DELETE | A2P-Signature | ✅ |
| `/a2p/v1/profile/:did/memories/propose` | POST | A2P-Signature | ✅ |
| `/a2p/v1/did/:did` | GET | Public | ✅ |
| `/a2p/v1/agents/register` | POST | A2P-Signature or Bearer | ✅ |
| `/a2p/v1/profile/access` | POST | Connection Token | ✅ |

## Examples

See the examples directory for complete examples:

- `examples/protocol_compliant_auth.py` - A2P-Signature authentication
- `examples/did_resolution.py` - DID resolution
- `examples/basic_usage.py` - Basic usage with connection tokens

## Verification

To verify protocol compliance:

1. **Test A2P-Signature**: Use `generate_a2p_signature_header()` to sign requests
2. **Test DID Resolution**: Resolve any registered DID
3. **Test Agent Registration**: Register an agent with public key
4. **Test Profile Operations**: Use all profile endpoints

All tests should pass with standard a2p protocol clients.

## References

- [a2p Protocol Specification](https://a2p-protocol.org)
- Gaugid API documentation (see [Gaugid](https://gaugid.com) for compliance and API details)
