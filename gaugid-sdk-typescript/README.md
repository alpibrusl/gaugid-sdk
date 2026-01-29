# Gaugid SDK - TypeScript

TypeScript SDK for integrating with Gaugid (a2p-cloud) service. This SDK extends the base a2p protocol SDK with Gaugid-specific features like OAuth flows, connection tokens, and service-specific utilities.

## Installation

```bash
npm install @gaugid/sdk
```

### Framework Integrations

Install with framework-specific dependencies:

```bash
# LangGraph integration
npm install @gaugid/sdk @langchain/langgraph

# Google ADK integration
npm install @gaugid/sdk @google-cloud/adk

# Anthropic Claude integration
npm install @gaugid/sdk @anthropic-ai/sdk

# OpenAI Agents integration
npm install @gaugid/sdk @openai/agents

# LlamaIndex integration
npm install @gaugid/sdk llama-index-core

# Agno integration
npm install @gaugid/sdk agno
```

## Quick Start

### Basic Usage

```typescript
import { GaugidClient } from "@gaugid/sdk";

// Create a client with connection token
const client = new GaugidClient({
  connectionToken: "gaugid_conn_xxx",
});

// Get user profile
const profile = await client.getProfile({
  userDid: "did:a2p:user:gaugid:alice",
  scopes: ["a2p:preferences", "a2p:interests"],
});

// Propose a memory
await client.proposeMemory({
  content: "User prefers vegetarian options",
  category: "a2p:preferences",
});
```

### OAuth Flow

```typescript
import { OAuthFlow, GaugidClient } from "@gaugid/sdk";

// Initialize OAuth flow
const flow = new OAuthFlow({
  clientId: "my-service",
  clientSecret: "secret",
  redirectUri: "https://myapp.com/callback",
});

// Step 1: Get authorization URL
const { authUrl, state } = flow.getAuthorizationUrl({
  scopes: ["a2p:preferences", "a2p:interests"],
});

// Step 2: Redirect user to authUrl
// Step 3: After redirect, exchange code for token
const tokenResponse = await flow.exchangeCode(code, state);

// Step 4: Create client from OAuth response
const client = GaugidClient.fromOAuthResponse(tokenResponse);

// List and select profile
const profiles = await client.listProfiles();
if (profiles.length > 0) {
  client.selectProfile(profiles[0].did as string);
}

// Use selected profile
const profile = await client.getCurrentProfile({
  scopes: ["a2p:preferences"],
});
```

## Framework Integrations

### LangGraph

```typescript
import { StateGraph } from "@langchain/langgraph";
import { GaugidStore } from "@gaugid/sdk/integrations/langgraph";

const store = new GaugidStore({
  connectionToken: "gaugid_conn_xxx",
  namespacePrefix: ["langgraph", "my-app"],
});

const graph = new StateGraph(...);
const app = graph.compile({ checkpointer: store });
```

### Google ADK

```typescript
import { Agent } from "@google-cloud/adk";
import { GaugidMemoryService } from "@gaugid/sdk/integrations/adk";

const memoryService = new GaugidMemoryService({
  connectionToken: "gaugid_conn_xxx",
});

const agent = new Agent({
  memoryService,
  // ... other config
});
```

### Anthropic Claude

```typescript
import { Anthropic } from "@anthropic-ai/sdk";
import { GaugidMemoryTool } from "@gaugid/sdk/integrations/anthropic";

const memoryTool = new GaugidMemoryTool({
  connectionToken: "gaugid_conn_xxx",
});

// Use with Claude
```

### OpenAI Agents

```typescript
import { Agent } from "@openai/agents";
import { GaugidSession } from "@gaugid/sdk/integrations/openai";

const session = new GaugidSession({
  connectionToken: "gaugid_conn_xxx",
  sessionId: "user-123",
});

const agent = new Agent({
  session,
  // ... other config
});
```

### LlamaIndex

```typescript
import { VectorStoreIndex } from "llama-index";
import { GaugidMemoryBlock } from "@gaugid/sdk/integrations/llama_index";

const memoryBlock = new GaugidMemoryBlock({
  connectionToken: "gaugid_conn_xxx",
  blockId: "user-memories",
});

// Use with LlamaIndex
```

### Agno

```typescript
import { MemoryManager } from "agno";
import { GaugidDb } from "@gaugid/sdk/integrations/agno";

const db = new GaugidDb({
  connectionToken: "gaugid_conn_xxx",
});

const memoryManager = new MemoryManager({ db });
```

## API Reference

### GaugidClient

Main client for interacting with Gaugid service.

#### Methods

- `getProfile(options?)` - Get user profile
- `requestAccess(options)` - Request access to additional scopes
- `proposeMemory(options)` - Propose a new memory
- `listProfiles()` - List available profiles
- `selectProfile(profileDid)` - Select a profile
- `getCurrentProfile(options)` - Get currently selected profile
- `proposeMemoryToCurrent(options)` - Propose memory to current profile
- `resolveDid(did)` - Resolve a DID to its document
- `registerAgent(options)` - Register an agent
- `close()` - Close the client

### OAuthFlow

OAuth 2.0 authorization code flow helper.

#### Methods

- `getAuthorizationUrl(options)` - Generate authorization URL
- `parseAuthorizationResponse(redirectUrl, expectedState)` - Parse authorization code
- `exchangeCode(code, state?)` - Exchange code for token
- `revokeToken(token)` - Revoke a connection token

### ConnectionManager

Manager for multiple Gaugid connections.

#### Methods

- `saveConnection(connectionId, tokenInfo)` - Save a connection
- `getConnectionToken(connectionId)` - Get connection token
- `deleteConnection(connectionId)` - Delete a connection
- `listConnections()` - List all connections
- `getConnectionInfo(connectionId)` - Get connection info

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Test
npm test

# Lint
npm run lint

# Format
npm run format
```

## License

EUPL-1.2

## Links

- **Homepage**: https://gaugid.com
- **Documentation**: https://docs.gaugid.com
- **Repository**: https://github.com/alpibrusl/gaugid-sdk
- **Issues**: https://github.com/alpibrusl/gaugid-sdk/issues
