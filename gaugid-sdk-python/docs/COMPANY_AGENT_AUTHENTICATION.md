# Company Agent Authentication Guide

This guide explains how a company's AI agent authenticates and accesses user profiles in Gaugid.

## Overview

**Key Principle**: Users must grant access to their profiles. No agent can access user data without explicit user consent.

There are two authentication methods, both requiring user consent:

1. **OAuth Flow (Connection Tokens)** - Recommended for most company agents
2. **A2P-Signature (Protocol-Native)** - For protocol-compliant agents

## Authentication Flow 1: OAuth (Recommended)

### When to Use
- ✅ User-facing services (web apps, mobile apps)
- ✅ Services where users explicitly authorize your agent
- ✅ Most common use case for company agents

### How It Works

```
1. User visits your service
   ↓
2. User clicks "Connect with Gaugid" or similar
   ↓
3. User is redirected to Gaugid OAuth page
   ↓
4. User reviews requested scopes and authorizes
   ↓
5. User is redirected back with authorization code
   ↓
6. Your service exchanges code for connection token
   ↓
7. Your agent can now access user's profile with granted scopes
```

### Code Example

```python
from gaugid import GaugidClient
from gaugid.auth import OAuthFlow

# Step 1: Set up OAuth flow
flow = OAuthFlow(
    client_id="acme-travel-service",
    client_secret="your-secret",
    redirect_uri="https://acme.com/oauth/callback",
    api_url="https://api.alpha.gaugid.com"
)

# Step 2: Get authorization URL
scopes = ["a2p:preferences", "a2p:memories"]
auth_url, state = flow.get_authorization_url(scopes=scopes)

# Step 3: User visits auth_url and authorizes
# (In your web app, redirect user to auth_url)

# Step 4: User is redirected back with code
# (In your callback handler)
redirect_url = request.args.get('redirect_uri')
code = flow.parse_authorization_response(redirect_url, expected_state=state)
token_response = await flow.exchange_code(code=code, state=state)

# Step 5: Create client with connection token
client = GaugidClient.from_oauth_response(token_response)

# Step 6: Access user profile (no DID needed!)
profile = await client.get_profile(scopes=["a2p:preferences"])
```

### Benefits
- ✅ User-friendly OAuth flow
- ✅ No need to know user DIDs
- ✅ User can revoke access anytime
- ✅ Better privacy (DIDs not exposed)

## Authentication Flow 2: A2P-Signature (Protocol-Native)

### When to Use
- ✅ Protocol-compliant agents
- ✅ Agent-to-agent communication
- ✅ Cross-provider interoperability
- ✅ Decentralized authentication

### How It Works

```
1. Generate Ed25519 keypair for your agent
   ↓
2. Register agent with public key (one-time setup)
   ↓
3. User grants access via access request
   ↓
4. Sign each request with A2P-Signature header
   ↓
5. Access user profiles with granted scopes
```

### Code Example

```python
from gaugid import (
    GaugidClient,
    generate_ed25519_keypair,
    generate_a2p_signature_header,
    private_key_to_pem,
)
import base64

# Step 1: Generate keypair
private_key, public_key = generate_ed25519_keypair()
public_key_b64 = base64.b64encode(public_key).decode("utf-8")
private_key_pem = private_key_to_pem(private_key)

# Store private_key_pem securely! Never expose it.

# Step 2: Register agent (one-time setup)
# You need a registration token (from service account or OAuth)
agent_did = "did:a2p:agent:gaugid:acme-travel-assistant"
client = GaugidClient(
    connection_token="registration_token",  # For registration only
    api_url="https://api.alpha.gaugid.com",
    namespace="acme-corp"
)

result = await client.register_agent(
    agent_did=agent_did,
    name="Acme Travel Assistant",
    description="AI travel assistant for Acme Corp",
    public_key=public_key_b64
)

# Step 3: User grants access (via dashboard or access request API)
# (See Access Request Workflow below)

# Step 4: Use A2P-Signature for requests
# (SDK will handle this automatically when A2P-Signature support is added)
header = generate_a2p_signature_header(
    agent_did=agent_did,
    private_key=private_key,
    method="GET",
    path=f"/a2p/v1/profile/{user_did}"
)

# Make request with A2P-Signature header
headers = {"Authorization": header}
# ... make HTTP request
```

### Benefits
- ✅ Protocol-native (100% a2p compliant)
- ✅ Decentralized (no token management)
- ✅ Works across providers
- ✅ No token expiration

## Access Request Workflow

**Important**: Even with A2P-Signature, users must grant access before your agent can access their profiles.

### How Users Grant Access

1. **Via OAuth Flow** (automatic)
   - When user authorizes via OAuth, access is automatically granted

2. **Via Access Request API**
   - Agent requests access with specific scopes
   - User receives notification (dashboard/email)
   - User approves/denies the request
   - Agent can then access profile

3. **Via Gaugid Dashboard**
   - User manually grants access to your agent DID

### Code Example: Request Access

```python
# Request access to user profile
result = await client.request_access(
    user_did="did:a2p:user:gaugid:alice",
    scopes=["a2p:preferences", "a2p:memories"],
    purpose={
        "type": "travel_assistance",
        "description": "Access user preferences to provide personalized travel recommendations",
        "legalBasis": "user_consent"
    }
)

receipt_id = result.get("receiptId")
granted_scopes = result.get("grantedScopes", [])

# Wait for user approval (poll or wait for webhook)
# Once approved, access user profile
if granted_scopes:
    profile = await client.get_profile(
        user_did="did:a2p:user:gaugid:alice",
        scopes=granted_scopes
    )
```

## Multi-User Agent Pattern

If your agent serves multiple users, you have two options:

### Pattern 1: Connection Token per User (Recommended)

Each user authorizes via OAuth, you store one connection token per user.

```python
# User 1
client1 = GaugidClient(connection_token=user1_token)
profile1 = await client1.get_profile(scopes=[...])

# User 2
client2 = GaugidClient(connection_token=user2_token)
profile2 = await client2.get_profile(scopes=[...])
```

**Benefits:**
- Better user experience
- Easier token management
- User can revoke access easily

### Pattern 2: DID-Based with A2P-Signature

Single agent with one keypair, each user grants access to your agent DID.

```python
# Same agent, different users
agent_did = "did:a2p:agent:gaugid:my-agent"
private_key = load_agent_private_key()

# User 1
header1 = generate_a2p_signature_header(
    agent_did, private_key, "GET",
    f"/a2p/v1/profile/{user1_did}"
)

# User 2
header2 = generate_a2p_signature_header(
    agent_did, private_key, "GET",
    f"/a2p/v1/profile/{user2_did}"
)
```

**Benefits:**
- Protocol compliance
- Agent-to-agent communication
- Cross-provider interoperability

## Security Best Practices

1. **Store Private Keys Securely**
   - Never commit private keys to version control
   - Use environment variables or secure key management
   - Rotate keys periodically

2. **Use Least Privilege**
   - Request only the scopes you need
   - Don't request more permissions than necessary

3. **Handle Token Expiration**
   - Connection tokens expire after 90 days
   - Implement token refresh or re-authorization flow

4. **Validate User Consent**
   - Always check that access is granted before accessing profiles
   - Handle access denial gracefully

## Summary

| Method | Use Case | User Consent | Complexity |
|--------|----------|--------------|------------|
| OAuth (Connection Token) | User-facing services | Via OAuth flow | ⭐ Easy |
| A2P-Signature | Protocol-compliant agents | Via access request | ⭐⭐ Medium |

**Recommendation**: Start with OAuth flow for most company agents. Use A2P-Signature only if you need protocol compliance or agent-to-agent communication.

## Complete Example

See `examples/company_agent_authentication.py` for a complete working example with all authentication flows.
