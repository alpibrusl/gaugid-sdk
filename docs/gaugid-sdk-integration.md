# Gaugid SDK Integration Guide

**Date**: 2025-01-15  
**Version**: 1.0  
**Status**: Current System Features

## Overview

This document provides a comprehensive overview of the current Gaugid (a2p-cloud) system features for the SDK development team. It covers available endpoints, authentication methods, scopes, and token management capabilities.

## ✅ Yes, We Can Provide Tokens for Applications

**Connection Tokens** are fully implemented and available for applications. They provide a secure, OAuth-style authentication method that doesn't require applications to know user/profile DIDs.

### Token Format

```
gaugid_conn_<base64-encoded-random-bytes>
```

Example: `gaugid_conn_AbCdEf1234567890...`

### Token Lifetime

- **Validity**: 90 days from issuance
- **Expiration**: Automatic after 90 days
- **Refresh**: Currently requires re-authorization (refresh tokens not yet implemented)

### Token Context

Each connection token encapsulates:
- `userDid`: User's DID
- `profileDid`: Profile DID (if specific profile selected)
- `serviceDid`: Service DID
- `grantedScopes`: Scopes granted to the connection

## Authentication Methods

The system supports **two authentication methods**:

### 1. Connection Tokens (OAuth) - Recommended for Services

**Advantages:**
- ✅ No need to know profile DIDs
- ✅ Better privacy (DIDs not exposed)
- ✅ Simpler tool signatures
- ✅ Automatic profile resolution
- ✅ 90-day validity

**Use Case**: OAuth services, MCP servers, managed integrations

**Obtaining Tokens:**
- Via OAuth flow (see [OAuth Flow](#oauth-flow))
- Via Dashboard (`/connect` page)

### 2. A2P-Signature (Protocol-Native)

**Advantages:**
- ✅ Fully decentralized
- ✅ Protocol-aligned
- ✅ No server-managed tokens
- ✅ Works across implementations

**Use Case**: Protocol-compliant agents, direct agent-to-user interactions

**Setup:**
1. Register agent with public key
2. Sign requests with Ed25519 signatures
3. Include signature in `Authorization: A2P-Signature` header

## OAuth Flow

Complete OAuth 2.0 authorization code flow is implemented.

### Step 1: Service Registration

```http
POST /api/services
Authorization: Bearer <firebase-token>
Content-Type: application/json

{
  "serviceId": "my-travel-service",
  "name": "Travel Assistant",
  "description": "AI-powered travel planning",
  "redirectUris": ["http://localhost:8080/callback", "https://my-service.com/callback"],
  "requestedScopes": ["a2p:identity", "a2p:preferences", "a2p:episodic"]
}
```

**Response:**
```json
{
  "service": {
    "serviceId": "my-travel-service",
    "clientId": "my-travel-service",
    "clientSecret": "gaugid_secret_...",
    "redirectUris": ["http://localhost:8080/callback"],
    "allowedScopes": ["a2p:identity", "a2p:preferences", "a2p:episodic"],
    "verified": false,
    "active": true
  },
  "message": "Service registered successfully. Save the client secret - it will not be shown again!"
}
```

### Step 2: Authorization Request

```http
GET /connect/authorize?client_id=my-travel-service&redirect_uri=http://localhost:8080/callback&scope=a2p:identity,a2p:preferences&response_type=code&state=csrf_token
Authorization: Bearer <user-firebase-token>
```

**Response:**
```json
{
  "service": {
    "id": "my-travel-service",
    "name": "Travel Assistant",
    "description": "AI-powered travel planning",
    "logoUrl": "https://...",
    "verified": false
  },
  "requestedScopes": ["a2p:identity", "a2p:preferences"],
  "profiles": [
    {
      "id": "uuid",
      "did": "did:a2p:profile:gaugid:...",
      "name": "Personal Profile",
      "type": "personal"
    }
  ],
  "authParams": {
    "clientId": "my-travel-service",
    "redirectUri": "http://localhost:8080/callback",
    "scope": "a2p:identity,a2p:preferences",
    "state": "csrf_token"
  }
}
```

### Step 3: User Approval

```http
POST /connect/authorize
Authorization: Bearer <user-firebase-token>
Content-Type: application/json

{
  "client_id": "my-travel-service",
  "redirect_uri": "http://localhost:8080/callback",
  "scope": "a2p:identity,a2p:preferences",
  "decision": "approve",
  "profile_ids": ["profile-uuid-1"]
}
```

**Response:**
```json
{
  "redirect": "http://localhost:8080/callback?code=gaugid_code_...&state=csrf_token"
}
```

### Step 4: Token Exchange

```http
POST /connect/token
Content-Type: application/json

{
  "grant_type": "authorization_code",
  "code": "gaugid_code_...",
  "client_id": "my-travel-service",
  "client_secret": "gaugid_secret_...",
  "redirect_uri": "http://localhost:8080/callback"
}
```

**Response:**
```json
{
  "access_token": "gaugid_conn_...",
  "token_type": "Bearer",
  "expires_in": 7776000,
  "scope": "a2p:identity a2p:preferences",
  "connection_id": "uuid",
  "user_did": "did:a2p:user:gaugid:...",
  "profiles": [
    {
      "did": "did:a2p:profile:gaugid:...",
      "name": "Personal Profile",
      "type": "personal"
    }
  ]
}
```

## Protocol Endpoints

All protocol endpoints are under `/a2p/v1`.

### Base URL

- **Production**: `https://api.alpha.gaugid.com` (or your deployment URL)
- **Development**: `http://localhost:3001`

### 1. Get Profile (Connection Token Mode)

**No DID required** - profile resolved from connection token context.

```http
GET /a2p/v1/profile?scopes=a2p:identity,a2p:preferences
Authorization: Bearer gaugid_conn_...
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "version": "1.0",
    "profileType": "personal",
    "identity": {
      "displayName": "Alice",
      "entityType": "individual"
    },
    "common": {
      "preferences": {...}
    },
    "memories": {
      "a2p:episodic": [...],
      "a2p:semantic": [...]
    }
  },
  "meta": {
    "requestId": "uuid",
    "timestamp": "2025-01-15T12:00:00Z",
    "agentDid": "did:a2p:service:my-travel-service",
    "authMode": "connection"
  }
}
```

### 2. Get Profile (Direct Mode with DID)

```http
GET /a2p/v1/profile/:did?scopes=a2p:identity,a2p:preferences
Authorization: A2P-Signature ... | Bearer <token>
```

### 3. Request Access

Request access to additional scopes.

**Connection Token Mode:**
```http
POST /a2p/v1/profile/access
Authorization: Bearer gaugid_conn_...
Content-Type: application/json

{
  "scopes": ["a2p:episodic"],
  "purpose": {
    "type": "memory_retrieval",
    "description": "Need to access user memories for context",
    "legalBasis": "user_consent"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "receiptId": "rcpt_uuid",
    "userDid": "did:a2p:user:gaugid:...",
    "agentDid": "did:a2p:service:my-travel-service",
    "grantedScopes": ["a2p:episodic"],
    "deniedScopes": [],
    "purpose": {...},
    "grantedAt": "2025-01-15T12:00:00Z",
    "expiresAt": "2025-01-16T12:00:00Z"
  }
}
```

### 4. Propose Memory

Propose a new memory to be added to the profile.

**Connection Token Mode:**
```http
POST /a2p/v1/profile/memories/propose
Authorization: Bearer gaugid_conn_...
Content-Type: application/json

{
  "content": "User prefers window seats on flights",
  "category": "a2p:travel_preferences",
  "memory_type": "episodic",
  "confidence": 0.9,
  "context": "Conversation on 2025-01-15"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "proposalId": "prop_uuid",
    "status": "pending"
  },
  "meta": {
    "requestId": "uuid",
    "timestamp": "2025-01-15T12:00:00Z",
    "authMode": "connection"
  }
}
```

**Memory Types:**
- `episodic`: Personal experiences and events
- `semantic`: Facts and knowledge
- `procedural`: Skills and how-to information

### 5. DID Resolution

Resolve a DID to its DID document (W3C-compliant).

```http
GET /a2p/v1/did/:did
Authorization: Bearer <token> | A2P-Signature ...
```

**Example:**
```http
GET /a2p/v1/did/did:a2p:agent:gaugid:my-agent
```

**Response:**
```json
{
  "success": true,
  "data": {
    "@context": [
      "https://www.w3.org/ns/did/v1",
      "https://w3id.org/security/suites/ed25519-2020/v1"
    ],
    "id": "did:a2p:agent:gaugid:my-agent",
    "verificationMethod": [
      {
        "id": "did:a2p:agent:gaugid:my-agent#key-1",
        "type": "Ed25519VerificationKey2020",
        "publicKeyMultibase": "z...",
        "controller": "did:a2p:agent:gaugid:my-agent"
      }
    ],
    "authentication": ["did:a2p:agent:gaugid:my-agent#key-1"],
    "assertionMethod": ["did:a2p:agent:gaugid:my-agent#key-1"]
  }
}
```

### 6. Agent Registration

Register an agent with public key for A2P-Signature authentication.

```http
POST /a2p/v1/agents/register
Authorization: A2P-Signature ... | Bearer <token>
Content-Type: application/json

{
  "did": "did:a2p:agent:gaugid:my-agent",
  "name": "My Agent",
  "description": "A helpful AI assistant",
  "publicKey": "base64_encoded_ed25519_public_key",
  "keyType": "Ed25519"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent": {
      "did": "did:a2p:agent:gaugid:my-agent",
      "name": "My Agent",
      "description": "A helpful AI assistant",
      "verified": true,
      "publicKey": "base64_encoded_ed25519_public_key",
      "keyType": "Ed25519"
    },
    "didDocument": {...}
  },
  "message": "Agent registered and verified (development mode)"
}
```

## Available Scopes

### Standard Scopes

| Scope | Description | Profile Section |
|-------|-------------|------------------|
| `a2p:identity` | Identity information | `identity` |
| `a2p:preferences` | User preferences | `common.preferences` |
| `a2p:interests` | User interests | `memories` (filtered by category) |
| `a2p:professional` | Professional information | `memories` (filtered by category) |
| `a2p:context` | Current context | `memories` (filtered by category) |
| `a2p:*` | All scopes | All sections |

### Memory Type Scopes

| Scope | Description | Memory Type |
|-------|-------------|-------------|
| `a2p:episodic` | Episodic memories | `episodic` |
| `a2p:semantic` | Semantic memories | `semantic` |
| `a2p:procedural` | Procedural memories | `procedural` |

### Combined Scopes

You can combine memory types with categories:

- `a2p:episodic.preferences` - Episodic memories in preferences category
- `a2p:semantic.interests` - Semantic memories in interests category
- `a2p:procedural.skills` - Procedural memories in skills category

## Service Management Endpoints

### List Services

```http
GET /api/services
Authorization: Bearer <firebase-token>
```

### Get Service

```http
GET /api/services/:serviceId
Authorization: Bearer <firebase-token>
```

### Update Service

```http
PUT /api/services/:serviceId
Authorization: Bearer <firebase-token>
Content-Type: application/json

{
  "name": "Updated Service Name",
  "description": "Updated description",
  "redirectUris": ["https://new-callback.com"],
  "requestedScopes": ["a2p:identity"]
}
```

### Regenerate Client Secret

```http
POST /api/services/:serviceId/regenerate-secret
Authorization: Bearer <firebase-token>
```

**Response:**
```json
{
  "clientSecret": "gaugid_secret_NEW...",
  "message": "Client secret regenerated. Save it - it will not be shown again!"
}
```

### Delete Service

```http
DELETE /api/services/:serviceId
Authorization: Bearer <firebase-token>
```

## Connection Management

### List Connections

```http
GET /api/connections
Authorization: Bearer <firebase-token>
```

### Revoke Connection

**Via Dashboard API:**
```http
DELETE /api/connections/:id
Authorization: Bearer <firebase-token>
```

**Via OAuth Revoke Endpoint:**
```http
POST /connect/revoke
Content-Type: application/json

{
  "token": "gaugid_conn_...",
  "client_id": "my-service",
  "client_secret": "gaugid_secret_..."
}
```

## Error Codes

The system uses standardized error codes:

| Code | Message | Description |
|------|---------|-------------|
| `A2P000` | Internal server error | Generic server error |
| `A2P001` | Not authorized | Authentication/authorization failed |
| `A2P002` | Invalid public key format | Public key validation failed |
| `A2P003` | Profile not found | Profile doesn't exist or unavailable |
| `A2P006` | Invalid request | Request validation failed |
| `A2P009` | User already exists | Duplicate user registration |
| `A2P013` | Authenticated DID must match | DID mismatch in registration |
| `A2P014` | Service not found | Invalid service ID |
| `A2P015` | Invalid redirect_uri | Redirect URI not in allowed list |
| `A2P016` | Invalid scopes | Scope not in allowed list |
| `A2P017` | Invalid authorization code | Code expired or invalid |
| `A2P018` | Authorization code expired | Code has expired |
| `A2P019` | Invalid or expired connection token | Token validation failed |
| `A2P020` | Connection has been revoked | Token was revoked |
| `A2P021` | Connection token required | Endpoint requires connection token |
| `A2P022` | Service DID mismatch | DID mismatch in connection |
| `A2P023` | Rate limit exceeded | Too many requests |
| `A2P024` | Export limit exceeded | Data export rate limit |
| `A2P025` | Import limit exceeded | Data import rate limit |
| `A2P026` | Data import completed with errors | Import had errors |

## Current System Status

### ✅ Implemented Features

1. **OAuth 2.0 Flow**
   - Service registration
   - Authorization code flow
   - Token exchange
   - Token revocation

2. **Connection Tokens**
   - Token generation
   - Token validation
   - Token expiration (90 days)
   - Token revocation

3. **Protocol Endpoints**
   - Profile access (with/without DID)
   - Memory proposals
   - Access requests
   - DID resolution
   - Agent registration

4. **Scopes System**
   - Standard scopes
   - Memory type scopes
   - Combined scopes
   - Scope filtering

5. **Authentication**
   - Connection tokens
   - A2P-Signature (Ed25519)
   - Firebase authentication (for users)

6. **Service Management**
   - Service registration
   - Service updates
   - Client secret management
   - Connection management

### 🚧 Not Yet Implemented

1. **Token Refresh**
   - Refresh tokens not implemented
   - Requires re-authorization after 90 days

2. **Advanced Features**
   - Token rotation
   - Multiple token management
   - Token scoping per request

## SDK Integration Recommendations

### For Connection Token Support

The SDK should:

1. **Support OAuth Flow**
   - Implement authorization URL generation
   - Handle authorization code exchange
   - Manage connection tokens

2. **Token Management**
   - Store tokens securely
   - Handle token expiration
   - Implement token refresh (when available)

3. **Profile Access**
   - Support connection token mode (no DID required)
   - Support direct mode (with DID)
   - Handle scope filtering

4. **Error Handling**
   - Map error codes to SDK exceptions
   - Handle token expiration gracefully
   - Provide helpful error messages

### Example SDK Usage

```python
from gaugid import GaugidClient
from gaugid.auth import OAuthFlow

# OAuth Flow
flow = OAuthFlow(
    client_id="my-service",
    client_secret="my-secret",
    redirect_uri="https://myapp.com/callback"
)

# Get authorization URL
auth_url, state = flow.get_authorization_url(
    scopes=["a2p:identity", "a2p:preferences"]
)

# After user approves, exchange code for token
token_response = await flow.exchange_code(code="auth_code", state=state)

# Use connection token
client = GaugidClient(connection_token=token_response.access_token)

# Get profile (no DID needed!)
profile = await client.get_profile(scopes=["a2p:identity", "a2p:preferences"])

# Propose memory
result = await client.propose_memory(
    content="User prefers window seats",
    category="a2p:travel_preferences",
    memory_type="episodic",
    confidence=0.9
)
```

## Testing

### Test Environment

- **API URL**: `https://api.alpha.gaugid.com` (or your deployment)
- **Dashboard**: `https://alpha.gaugid.com` (or your deployment)

### Test Service Registration

1. Register a test service via Dashboard or API
2. Note the `client_id` and `client_secret`
3. Use these for OAuth flow testing

### Test Connection Token Flow

1. Complete OAuth flow to get connection token
2. Use token to access profile endpoints
3. Test token expiration (90 days)
4. Test token revocation

## Security Considerations

1. **Token Storage**
   - Store tokens securely (environment variables, secret management)
   - Never commit tokens to version control
   - Use secure storage mechanisms

2. **Token Rotation**
   - Tokens expire after 90 days
   - Implement logic to detect expired tokens
   - Re-authorize when tokens expire

3. **Scope Limitation**
   - Only request scopes you actually need
   - Follow principle of least privilege
   - Review granted scopes

4. **Revocation**
   - Users can revoke tokens at any time
   - Handle 401 errors gracefully
   - Implement re-authorization flow

## Next Steps

1. **SDK Updates**
   - Ensure connection token support is complete
   - Add OAuth flow helpers
   - Implement token management utilities

2. **Documentation**
   - Update SDK documentation with connection token examples
   - Add OAuth flow tutorials
   - Document error handling

3. **Testing**
   - Test OAuth flow end-to-end
   - Test token expiration handling
   - Test error scenarios

## Questions?

For questions or clarifications:
- **API Documentation**: See `/docs/api-reference/` in the a2p-cloud repository
- **OAuth Guide**: See `/docs/guides/oauth-flow.md`
- **Connection Tokens**: See `/docs/guides/connection-tokens.md`

---

**Last Updated**: 2025-01-15  
**Maintained by**: a2p-cloud team
