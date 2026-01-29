# Gaugid SDK Documentation

Welcome to the **Gaugid SDK** documentation! This SDK provides a convenient, high-level interface for integrating with the [Gaugid](https://gaugid.com) (a2p-cloud) service.

## What is Gaugid?

Gaugid is a cloud service that implements the [a2p protocol](https://a2p-protocol.org), enabling AI agents to access user profiles with proper consent and privacy controls. **Gaugid is 100% compliant with the a2p protocol specification**, supporting all required endpoints including A2P-Signature authentication, DID resolution, and agent registration.

The Gaugid SDK extends the base a2p protocol SDK with service-specific features like OAuth flows and connection tokens, while maintaining full protocol compliance.

## Key Features

- 🚀 **Easy Integration**: Simple, high-level API for interacting with Gaugid
- 🔐 **OAuth Support**: Built-in OAuth 2.0 authorization code flow
- 🔑 **Connection Tokens**: Secure connection token management
- 📦 **100% Protocol Compliant**: Fully compliant with a2p protocol v0.1.0
- 🔒 **A2P-Signature Support**: Protocol-native authentication (Ed25519 signatures)
- 🆔 **DID Resolution**: Resolve DIDs to DID documents (W3C-compliant)
- 🤖 **Agent Registration**: Register agents with public keys
- 🛡️ **Error Handling**: Comprehensive error handling with helpful messages
- ⚡ **Async First**: Fully async/await support
- 🔌 **Framework Support**: Works with LangChain, LangGraph, OpenAI, Anthropic, and more

## Quick Start

```python
import asyncio
from gaugid import GaugidClient

async def main():
    # Initialize client with connection token
    client = GaugidClient(connection_token="gaugid_conn_xxx")
    
    # Get a user's profile
    profile = await client.get_profile(
        user_did="did:a2p:user:gaugid:alice",
        scopes=["a2p:preferences", "a2p:interests"]
    )
    
    # Propose a new memory
    result = await client.propose_memory(
        user_did="did:a2p:user:gaugid:alice",
        content="User prefers morning meetings",
        category="a2p:preferences",
        confidence=0.8
    )
    
    await client.close()

asyncio.run(main())
```

## Installation

```bash
pip install gaugid
```

## Documentation Structure

### Getting Started
- [Installation](getting-started/installation.md) - Install and configure the SDK
- [Quick Start](getting-started/quickstart.md) - Your first integration
- [Authentication](getting-started/authentication.md) - OAuth and connection tokens
- [First Example](getting-started/first-example.md) - Build your first app

### Tutorials
- [Framework Integration](tutorials/overview.md) - Integrate with popular AI frameworks
  - [LangChain](tutorials/frameworks/langchain.md) - Build personalized chains
  - [LangGraph](tutorials/frameworks/langgraph.md) - State machine agents
  - [OpenAI Assistants](tutorials/frameworks/openai-assistants.md) - GPT-4 integration
  - [Anthropic Claude](tutorials/frameworks/anthropic.md) - Claude integration
  - [Google Gemini](tutorials/frameworks/gemini.md) - Gemini integration
  - [Google ADK](tutorials/frameworks/google-adk.md) - Agent Development Kit
  - [CrewAI](tutorials/frameworks/crewai.md) - Multi-agent crews
  - [Agno](tutorials/frameworks/agno.md) - Enterprise multi-agent

### API Reference
- [Client](api-reference/client.md) - GaugidClient API
- [Storage](api-reference/storage.md) - GaugidStorage API
- [Auth](api-reference/auth.md) - OAuth flow helpers
- [Connection](api-reference/connection.md) - Token management
- [Types](api-reference/types.md) - Error types and models

### Guides
- [Best Practices](guides/best-practices.md) - Recommended patterns
- [Security](guides/security.md) - Security considerations
- [Performance](guides/performance.md) - Optimization tips
- [Troubleshooting](guides/troubleshooting.md) - Common issues
- [Migration Guide](guides/migration.md) - Migrating from a2p SDK

### Protocol Proposals
- [Memory Types Extension](proposals/memory-types-protocol-extension.md) - ✅ Approved and Implemented
- [Implementation Status](proposals/IMPLEMENTATION_STATUS.md) - Current implementation status
- [Proposals Overview](proposals/README.md) - All protocol extension proposals

## Framework Support

The Gaugid SDK works seamlessly with popular AI agent frameworks. Each framework tutorial shows the **same use case** (a personalized chatbot) implemented differently:

=== "LangChain"
    ```python
    from langchain_openai import ChatOpenAI
    from gaugid import GaugidClient
    
    # Load user context
    client = GaugidClient(connection_token="...")
    profile = await client.get_profile(user_did, scopes=["a2p:preferences"])
    
    # Use in LangChain
    llm = ChatOpenAI()
    chain = create_personalized_chain(llm, profile)
    ```
    [View Tutorial →](tutorials/frameworks/langchain.md)

=== "LangGraph"
    ```python
    from langgraph.graph import StateGraph
    from gaugid import GaugidClient
    
    # Load user context into state
    client = GaugidClient(connection_token="...")
    user_context = await load_user_context(user_did)
    
    # Use in LangGraph state
    graph = create_chatbot_graph(llm, user_context)
    ```
    [View Tutorial →](tutorials/frameworks/langgraph.md)

=== "OpenAI Assistants"
    ```python
    from openai import OpenAI
    from gaugid import GaugidClient
    
    # Load user context
    client = GaugidClient(connection_token="...")
    profile = await client.get_profile(user_did, scopes=["a2p:preferences"])
    
    # Create personalized assistant
    assistant = client.beta.assistants.create(
        instructions=f"User context: {profile}",
        model="gpt-4"
    )
    ```
    [View Tutorial →](tutorials/frameworks/openai-assistants.md)

## Use Cases

### Personalized AI Assistants
Build AI assistants that remember user preferences, context, and history across sessions.

### Multi-Agent Systems
Enable multiple agents to share user context while respecting privacy and consent policies.

### Memory Management
Propose and manage user memories with confidence scores and user approval workflows.

### OAuth Integration
Implement secure OAuth flows for service-to-user connections.

## Related Projects

- [a2p Protocol SDK](https://github.com/a2p-protocol/a2p) - Base protocol SDK
- **Gaugid Service** - Gaugid API service (proprietary)
- [a2p Protocol](https://a2p-protocol.org) - Protocol specification

## License

This project is licensed under the [European Union Public Licence v. 1.2](https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12) (EUPL-1.2).

## Support

- **Documentation**: [https://docs.gaugid.com](https://docs.gaugid.com)
- **Issues**: [GitHub Issues](https://github.com/alpibrusl/gaugid-sdk/issues)
- **Homepage**: [https://gaugid.com](https://gaugid.com)

---

**Ready to get started?** Check out the [Installation Guide](getting-started/installation.md) or jump to [Quick Start](getting-started/quickstart.md)!
