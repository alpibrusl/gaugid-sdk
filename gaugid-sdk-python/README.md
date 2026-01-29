# Gaugid SDK for Python

[![License: EUPL-1.2](https://img.shields.io/badge/License-EUPL--1.2-blue.svg)](https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Python SDK for integrating with the [Gaugid](https://gaugid.com) (a2p-cloud) service. This SDK extends the base [a2p protocol SDK](https://github.com/a2p-protocol/a2p) with Gaugid-specific features like OAuth flows, connection tokens, and service-specific utilities.

## Features

- 🚀 **Easy Integration**: Simple, high-level API for interacting with Gaugid
- 🔐 **OAuth Support**: Built-in OAuth 2.0 authorization code flow for user-facing apps
- 🔑 **Connection Tokens**: Secure token management for service-to-user connections
- 📦 **100% Protocol Compliant**: Fully compliant with a2p protocol v0.1.0
- 🔒 **A2P-Signature Ready**: Support for protocol-native authentication (Ed25519 signatures)
- 🆔 **DID Resolution**: Resolve DIDs to DID documents (W3C-compliant)
- 🤖 **Agent Registration**: Register agents with public keys for protocol compliance
- 💾 **Memory Types**: Support for episodic, semantic, and procedural memories
- 🛡️ **Error Handling**: Comprehensive error handling with helpful messages
- ⚡ **Async First**: Fully async/await support

## Installation

This project uses the official **a2p-sdk** Python package from [PyPI](https://pypi.org/project/a2p-sdk/). Normal installation will pull `a2p-sdk>=0.1.1` automatically.

### Basic Installation

```bash
pip install gaugid
```

### Optional Dependencies

Install with Google ADK integration:

```bash
pip install gaugid[adk]
```

This includes:
- `google-adk>=1.22.0` - Google Agent Development Kit
- `python-genai>=1.57.0` - Google Generative AI SDK (maintained package)

Install with LangGraph integration:

```bash
pip install gaugid[langgraph]
```

This includes:
- `langgraph>=1.0.6` - LangGraph for state machines
- `langchain-core>=1.26.0` - LangChain core dependencies

Install with Anthropic integration:

```bash
pip install gaugid[anthropic]
```

This includes:
- `anthropic>=0.75.0` - Anthropic Claude SDK

Install with OpenAI Agents integration:

```bash
pip install gaugid[openai]
```

This includes:
- `openai-agents>=1.0.0` - OpenAI Agents SDK

Install with LlamaIndex integration:

```bash
pip install gaugid[llama-index]
```

This includes:
- `llama-index-core>=0.14.12` - LlamaIndex core

Install with Agno integration:

```bash
pip install gaugid[agno]
```

This includes:
- `agno>=2.3.26` - Agno multi-agent framework

Install with all optional dependencies:

```bash
pip install gaugid[all]
```

## Quick Start

### Choose Your Authentication Method

**Building a user-facing app (UI, profile management)?** → Use **Connection Tokens (OAuth)**
```python
# User authorizes via OAuth, you get a connection token
client = GaugidClient(connection_token="gaugid_conn_xxx")
profile = await client.get_profile(scopes=["a2p:preferences"])  # No DID needed!
```

**Building an AI agent (protocol-compliant)?** → Use **A2P-Signature (Protocol)**
```python
# Agent registers with public key, signs requests
# (Full A2P-Signature support coming soon)
client = GaugidClient(agent_did="did:a2p:agent:gaugid:my-agent", ...)
```

### Basic Usage

The SDK supports **two modes** for accessing profiles:

#### Connection Token Mode (Recommended)

When using a connection token, you don't need to specify the user DID - it's resolved from the token context:

```python
import asyncio
from gaugid import GaugidClient

async def main():
    # Initialize client with connection token
    client = GaugidClient(connection_token="gaugid_conn_xxx")
    
    # Get profile (no DID needed - resolved from token)
    profile = await client.get_profile(
        scopes=["a2p:preferences", "a2p:interests"]
    )
    
    # Propose a new memory (no DID needed)
    result = await client.propose_memory(
        content="User prefers morning meetings",
        category="a2p:preferences",
        memory_type="episodic",  # episodic, semantic, or procedural
        confidence=0.8
    )
    
    await client.close()

asyncio.run(main())
```

#### DID Mode (Direct Access)

You can also specify the user DID directly:

```python
import asyncio
from gaugid import GaugidClient

async def main():
    client = GaugidClient(connection_token="gaugid_conn_xxx")
    
    # Get profile with explicit DID
    profile = await client.get_profile(
        user_did="did:a2p:user:gaugid:alice",
        scopes=["a2p:preferences", "a2p:interests"]
    )
    
    # Propose memory with explicit DID
    result = await client.propose_memory(
        content="User prefers morning meetings",
        user_did="did:a2p:user:gaugid:alice",
        category="a2p:preferences",
        memory_type="episodic",
        confidence=0.8
    )
    
    await client.close()

asyncio.run(main())
```

### OAuth Flow

```python
from gaugid.auth import OAuthFlow

# Initialize OAuth flow
flow = OAuthFlow(
    client_id="my-service",
    client_secret="my-secret",
    redirect_uri="https://myapp.com/callback"
)

# Step 1: Get authorization URL
auth_url, state = flow.get_authorization_url(
    scopes=["a2p:preferences", "a2p:interests"]
)

# Step 2: User authorizes and redirects back with code
# Step 3: Exchange code for token
token_response = await flow.exchange_code(code="auth_code_xxx", state=state)

# Use the connection token
client = GaugidClient(connection_token=token_response.access_token)
```

### Authentication Methods: When to Use Which?

Gaugid supports **two authentication methods** for different use cases:

#### 1. Connection Tokens (OAuth) - For User-Facing Applications

**Use for:**
- 🖥️ **User interfaces** (web apps, mobile apps, dashboards)
- 👤 **Profile management** (creating/editing profiles via API)
- 🔗 **Service-to-user connections** (OAuth-based integrations)
- 📱 **User-authorized services** (user grants access to a service)

**How it works:**
```python
# User authorizes via OAuth flow
from gaugid.auth import OAuthFlow

flow = OAuthFlow(client_id="my-service", client_secret="secret", redirect_uri="...")
auth_url, state = flow.get_authorization_url(scopes=["a2p:preferences"])
# User visits auth_url, authorizes, redirects back with code
token_response = await flow.exchange_code(code="...", state=state)

# Use connection token
client = GaugidClient(connection_token=token_response.access_token)
profile = await client.get_profile(scopes=["a2p:preferences"])  # No DID needed!
```

**Benefits:**
- ✅ User-friendly OAuth flow
- ✅ No need to know user DIDs
- ✅ Easy to revoke (user can revoke access)
- ✅ Better privacy (DIDs not exposed in URLs)

#### 2. A2P-Signature (Protocol-Native) - For AI Agents

**Use for:**
- 🤖 **AI agents** (protocol-compliant agents)
- 🔄 **Agent-to-agent communication**
- 🌐 **Cross-provider interoperability** (works with any a2p implementation)
- 🔐 **Decentralized authentication** (no centralized token management)

**How it works:**
```python
from gaugid import generate_ed25519_keypair, generate_a2p_signature_header
import base64

# Generate keypair for your agent
private_key, public_key = generate_ed25519_keypair()

# Register agent (one-time setup, can use connection token for registration)
client = GaugidClient(connection_token="gaugid_conn_xxx")  # For registration only
await client.register_agent(
    agent_did="did:a2p:agent:gaugid:my-agent",
    name="My Agent",
    public_key=base64.b64encode(public_key).decode("utf-8")
)

# Use A2P-Signature for all protocol requests
# (SDK would handle this automatically when A2P-Signature support is added)
```

**Benefits:**
- ✅ Fully decentralized (no token management)
- ✅ Protocol-native (100% a2p compliant)
- ✅ Works across providers (not tied to Gaugid)
- ✅ No token expiration
- ✅ Agent-to-agent communication

**Note:** The SDK currently uses connection tokens for all requests. Full A2P-Signature support for protocol endpoints is planned for future releases.

### DID Resolution

```python
# Resolve any DID to its DID document
did_doc = await client.resolve_did("did:a2p:agent:gaugid:my-agent")
print(f"Public key: {did_doc['verificationMethod'][0]['publicKeyMultibase']}")
```

### Agent Registration

```python
# Register a new agent
result = await client.register_agent(
    agent_did="did:a2p:agent:gaugid:my-agent",
    name="My Agent",
    description="A helpful AI assistant",
    public_key="base64_encoded_public_key"
)
```

## Documentation

### GaugidClient

The main client for interacting with Gaugid profiles.

```python
from gaugid import GaugidClient

client = GaugidClient(
    connection_token="gaugid_conn_xxx",
    api_url="https://api.gaugid.com",  # Optional
    agent_did="did:a2p:agent:local:my-agent",  # Optional (use "local" for examples)
    timeout=30.0  # Optional
)
```

**Methods:**

- `get_profile(user_did=None, scopes, sub_profile=None)` - Get user profile
  - Connection token mode: Omit `user_did` to use token context
  - DID mode: Provide `user_did` for direct access
- `request_access(scopes, user_did=None, sub_profile=None, purpose=None)` - Request access
  - Connection token mode: Omit `user_did` to use token context
  - `purpose` can be a dict with `type`, `description`, and `legalBasis`
- `propose_memory(content, user_did=None, category=None, memory_type=None, confidence=0.7, context=None)` - Propose memory
  - Connection token mode: Omit `user_did` to use token context
  - `memory_type`: "episodic", "semantic", or "procedural"
- `check_permission(user_did, permission, scope=None)` - Check permission
- `get_current_profile(scopes, sub_profile=None)` - Get currently selected profile (connection token mode if no profile selected)
- `propose_memory_to_current(content, category=None, memory_type=None, ...)` - Propose to current profile
- `close()` - Close the client

### OAuthFlow

Helper for implementing OAuth 2.0 authorization code flow.

```python
from gaugid.auth import OAuthFlow

flow = OAuthFlow(
    client_id="my-service",
    client_secret="my-secret",
    redirect_uri="https://myapp.com/callback",
    api_url="https://api.gaugid.com"  # Optional
)
```

**Methods:**

- `get_authorization_url(scopes, state=None)` - Generate authorization URL
- `parse_authorization_response(redirect_url, expected_state)` - Parse redirect URL
- `exchange_code(code, state=None)` - Exchange code for token
- `revoke_token(token)` - Revoke a connection token

### ConnectionManager

Manage multiple connection tokens.

```python
from gaugid.connection import ConnectionManager

manager = ConnectionManager()

# Save connection
manager.save_connection("my-connection", token_info)

# Get token
token = manager.get_connection_token("my-connection")

# List connections
connections = manager.list_connections()
```

## Framework Integrations

### LangGraph

Use Gaugid as a `BaseStore` for LangGraph agents:

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint import MemorySaver
from gaugid.integrations.langgraph import GaugidStore

# Create store
store = GaugidStore(
    connection_token="gaugid_conn_xxx",
    namespace_prefix=("langgraph", "my-app")
)

# Use with LangGraph
graph = StateGraph(...)
app = graph.compile(checkpointer=store)
```

**Installation**: `pip install gaugid[langgraph]`

**LangMem Integration**: `GaugidStore` works seamlessly with [LangMem](https://langchain-ai.github.io/langmem/) for automatic memory management:

```python
from langgraph.prebuilt import create_react_agent
from langmem import create_manage_memory_tool, create_search_memory_tool
from gaugid.integrations.langgraph import GaugidStore

store = GaugidStore(connection_token="gaugid_conn_xxx")
agent = create_react_agent(
    "anthropic:claude-3-5-sonnet-latest",
    tools=[
        create_manage_memory_tool(namespace=("memories",)),
        create_search_memory_tool(namespace=("memories",)),
    ],
    store=store,  # LangMem uses BaseStore - GaugidStore works!
)
```

**Documentation**: Based on [LangGraph Store Base](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint/langgraph/store/base/__init__.py)

### Google ADK (Agent Development Kit)

Use Gaugid as a `MemoryService` for Google ADK agents:

```python
from google.adk import Agent, Runner
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from gaugid.integrations.adk import GaugidMemoryService

# Create memory service
memory_service = GaugidMemoryService(
    connection_token="gaugid_conn_xxx",
    app_name="my-adk-app"
)

# Create agent with memory
agent = Agent(
    model="gemini-2.0-flash-exp",
    tools=[PreloadMemoryTool()],  # Auto-loads memories
)

# Use with runner
runner = Runner(agent=agent, memory_service=memory_service)
```

**Installation**: `pip install gaugid[adk]`

**Note**: Requires `google-adk>=1.22.0` and `python-genai>=1.57.0` (the maintained Google AI package)

**Documentation**: See [examples/frameworks/README_GAUGID_MEMORY.md](../../examples/frameworks/README_GAUGID_MEMORY.md)

Based on: [Google ADK Memory Documentation](https://google.github.io/adk-docs/sessions/memory/)

### Anthropic Claude Memory Tool

Use Gaugid as the backend for Anthropic's memory tool, allowing Claude to store and retrieve information across conversations:

```python
from anthropic import Anthropic
from gaugid.integrations.anthropic import GaugidMemoryTool

# Create memory tool with Gaugid backend
memory_tool = GaugidMemoryTool(
    connection_token="gaugid_conn_xxx",
    namespace_prefix="claude"
)

# Use with Anthropic client
client = Anthropic()
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    messages=[{"role": "user", "content": "Remember that I prefer dark mode."}],
    tools=[memory_tool],
    betas=["context-management-2025-06-27"]
)
```

**Installation**: `pip install gaugid[anthropic]`

**Documentation**: Based on [Anthropic Memory Tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)

### OpenAI Agents SDK

Use Gaugid as a `Session` backend for OpenAI Agents SDK, allowing agents to maintain conversation history across sessions:

```python
from openai import OpenAI
from openai.agents import Agent
from gaugid.integrations.openai import GaugidSession

# Create session with Gaugid backend
session = GaugidSession(
    session_id="user-123",
    connection_token="gaugid_conn_xxx"
)

# Use with OpenAI agent
agent = Agent(
    model="gpt-4o",
    session=session,
)
```

**Installation**: `pip install gaugid[openai]`

**Documentation**: Based on [OpenAI Agents SDK Memory](https://openai.github.io/openai-agents-python/ref/memory/)

### LlamaIndex

Use Gaugid as a `BaseMemoryBlock` for LlamaIndex, allowing agents to store and retrieve long-term memories:

```python
from llama_index.core.memory import Memory
from gaugid.integrations.llama_index import GaugidMemoryBlock

# Create memory block with Gaugid backend
memory_block = GaugidMemoryBlock(
    name="user_preferences",
    connection_token="gaugid_conn_xxx",
    memory_type="semantic"
)

# Use with LlamaIndex Memory
memory = Memory(
    memory_blocks=[memory_block],
    session_id="user-123"
)
```

**Installation**: `pip install gaugid[llama-index]`

**Documentation**: Based on [LlamaIndex Memory](https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/memory/memory.py)

### Agno

Use Gaugid as a database backend for Agno's MemoryManager, allowing agents to store and retrieve user memories:

```python
from agno.memory.manager import MemoryManager
from agno.models.openai import OpenAIChat
from gaugid.integrations.agno import GaugidDb

# Create database with Gaugid backend
db = GaugidDb(
    connection_token="gaugid_conn_xxx",
    user_id="user-123"
)

# Use with Agno MemoryManager
memory_manager = MemoryManager(
    model=OpenAIChat(id="gpt-4o"),
    db=db
)
```

**Installation**: `pip install gaugid[agno]`

**Documentation**: Based on [Agno Memory Manager](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/memory/manager.py)

## Examples

See the [examples](./examples/) directory for more detailed examples:

### User-Facing Applications (Connection Tokens)
- [User-Facing App](./examples/user_facing_app.py) - Building UIs and profile management tools
- [OAuth Flow](./examples/oauth_flow.py) - OAuth integration
- [User-Friendly Login](./examples/user_friendly_login.py) - OAuth with profile selection
- [Connection Tokens](./examples/connection_tokens.py) - Token management

### AI Agents (Protocol-Compliant)
- [Protocol-Compliant Auth](./examples/protocol_compliant_auth.py) - A2P-Signature for agents
- [Agent Registration](./examples/protocol_compliant_auth.py) - Register agents with public keys

### General Usage
- [Basic Usage](./examples/basic_usage.py) - Basic client usage (connection token mode & DID mode)
- [Memory Types](./examples/memory_types.py) - Using episodic, semantic, and procedural memories

## Error Handling

The SDK provides specific error types:

```python
from gaugid import (
    GaugidError,
    GaugidAPIError,
    GaugidAuthError,
    GaugidConnectionError
)

try:
    profile = await client.get_profile(user_did, scopes)
except GaugidAPIError as e:
    print(f"API error: {e.message} (code: {e.code})")
except GaugidConnectionError as e:
    print(f"Connection error: {e.message}")
```

## Logging

The SDK uses Python's standard `logging` module for all output. By default, only warnings and errors are logged.

### Enable Debug Logging

```python
import logging
from gaugid.logger import setup_logging

# Enable debug logging
setup_logging(level=logging.DEBUG)

# Or use INFO level for more verbose output
setup_logging(level=logging.INFO)
```

### Use Loggers in Your Code

```python
from gaugid.logger import get_logger

logger = get_logger("my_module")
logger.info("This is an info message")
logger.debug("This is a debug message")
logger.warning("This is a warning")
logger.error("This is an error")
```

### Custom Logging Configuration

```python
from gaugid.logger import setup_logging
import logging

# Custom format and level
setup_logging(
    level=logging.DEBUG,
    format_string="%(levelname)s - %(name)s - %(message)s"
)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/alpibrusl/gaugid-sdk.git
cd gaugid-sdk/gaugid-sdk-python

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Or use Makefile
make install-dev
```

### Local Development with a2p SDK

If you have the a2p SDK code in `../../a2p`, you can use it for local development:

```bash
# Using the setup script (recommended)
bash setup-local-dev.sh

# Or using Makefile
make install-dev-local
```

This will automatically detect and install the local a2p SDK from:
- `../../a2p/packages/sdk/python` (primary path - pyproject.toml is directly in python/)
- `../../a2p/packages/sdk-python` (alternative path)
- `../../a2p` (if a2p SDK is at root)

### Testing

```bash
# Run tests
pytest

# Run with coverage (enforces 80% minimum)
pytest --cov=gaugid --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Or use Makefile
make test-cov
make coverage-report  # Opens coverage report in browser
```

### Code Quality

The project uses:
- [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- [Black](https://github.com/psf/black) for code formatting
- [mypy](https://mypy.readthedocs.io/) for type checking
- [pytest](https://pytest.org/) for testing
- [Bandit](https://bandit.readthedocs.io/) for security scanning
- [pre-commit](https://pre-commit.com/) for automated checks

**Pre-commit hooks** are configured to run these tools automatically:
- Formatting (Black, Ruff format)
- Linting (Ruff)
- Type checking (mypy)
- Security scanning (Bandit)
- Test coverage (80% minimum, runs on pre-push)

### Coverage Requirements

- **Minimum**: 80% code coverage (enforced in CI and pre-commit)
- **Target**: 90% code coverage
- Coverage reports are generated in `htmlcov/` directory
- Coverage is checked on every commit and PR

### Makefile Commands

For convenience, use the Makefile:

```bash
make help          # Show all available commands
make install-dev   # Install with dev dependencies
make test          # Run tests
make test-cov      # Run tests with coverage
make lint          # Run linters
make format        # Format code
make type-check    # Run type checker
make security      # Run security scan
make pre-commit    # Run all pre-commit hooks
make ci            # Run all CI checks locally
make clean         # Clean build artifacts
```

## License

This project is licensed under the [European Union Public Licence v. 1.2](LICENSE) (EUPL-1.2).

## Related Projects

- [a2p Protocol SDK](https://github.com/a2p-protocol/a2p) - Base protocol SDK
- **Gaugid Service** - Gaugid API service (proprietary)

## Support

- **Documentation**: [https://docs.gaugid.com](https://docs.gaugid.com)
- **Issues**: [GitHub Issues](https://github.com/alpibrusl/gaugid-sdk/issues)
- **Homepage**: [https://gaugid.com](https://gaugid.com)

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

---

Copyright (c) 2024 Gaugid SDK Contributors

Licensed under the EUPL
