# GaugidMemoryService for Google ADK

This document explains how to use `GaugidMemoryService` as a `MemoryService` implementation for Google ADK, allowing ADK agents to use Gaugid profiles as their long-term memory store.

## Overview

`GaugidMemoryService` implements the Google ADK `BaseMemoryService` interface, enabling seamless integration between Google ADK agents and Gaugid profiles. This allows agents to:

- **Store session information** in Gaugid profiles as memories
- **Search Gaugid memories** for relevant context
- **Use built-in ADK memory tools** (PreloadMemoryTool, LoadMemoryTool)
- **Access all three memory types** (episodic, semantic, procedural)

Based on: [Google ADK Memory Documentation](https://google.github.io/adk-docs/sessions/memory/)

## Installation

```bash
pip install google-adk>=0.1.0
pip install gaugid>=0.1.0
```

## Quick Start

```python
from google.adk import Agent, Runner
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from gaugid_memory_service import GaugidMemoryService

# Create Gaugid memory service
memory_service = GaugidMemoryService(
    connection_token="gaugid_conn_xxx",
    app_name="my-adk-app"
)

# Create agent with memory tool
agent = Agent(
    model="gemini-2.0-flash-exp",
    name="memory_agent",
    instruction="You are a helpful assistant with long-term memory.",
    tools=[PreloadMemoryTool()],  # Automatically loads memories
)

# Create runner with memory service
runner = Runner(
    agent=agent,
    memory_service=memory_service,
)
```

## How It Works

### 1. Memory Storage (`add_session_to_memory`)

When a session is saved to memory, `GaugidMemoryService` extracts information and stores it in three ways:

- **Episodic Memory**: The actual conversation events ("what happened when")
- **Semantic Memory**: Extracted topics and knowledge ("what the user knows")
- **Procedural Memory**: Behavioral patterns from session state ("how the user does things")

```python
# Automatically called via callback or manually
await memory_service.add_session_to_memory(session)
```

### 2. Memory Retrieval (`search_memory`)

When an agent needs context, it searches Gaugid memories:

```python
# Called automatically by PreloadMemoryTool or LoadMemoryTool
results = await memory_service.search_memory(
    query="user preferences for Python",
    limit=10
)
```

The service:
- Searches across all memory types (episodic, semantic, procedural)
- Ranks results by relevance
- Returns results in ADK's `SearchMemoryResponse` format

### 3. Using Memory Tools

ADK provides built-in tools for memory access:

- **PreloadMemoryTool**: Automatically loads relevant memories at the start of each turn
- **LoadMemoryTool**: Allows the agent to search memory when needed

```python
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.tools.load_memory_tool import LoadMemoryTool

agent = Agent(
    model="gemini-2.0-flash-exp",
    tools=[
        PreloadMemoryTool(),  # Auto-load at turn start
        LoadMemoryTool(),      # Search on demand
    ]
)
```

## Complete Example

See `google_adk_with_gaugid_memory.py` for a complete working example.

## Integration with ADK Server

You can also use `GaugidMemoryService` with the ADK server:

```bash
# Start ADK server with custom memory service
# (This requires modifying the server code to use GaugidMemoryService)
adk api_server path/to/agents --memory_service_uri="gaugid://connection_token"
```

## Memory Types Mapping

| ADK Concept | Gaugid Memory Type | Description |
|-------------|-------------------|-------------|
| Conversation events | `episodic` | Specific events and interactions |
| Extracted knowledge | `semantic` | General knowledge and facts |
| Behavioral patterns | `procedural` | How the user does things |

## Benefits

1. **Persistent Memory**: Memories survive agent restarts (unlike InMemoryMemoryService)
2. **User Profiles**: Integrates with existing Gaugid user profiles
3. **Memory Types**: Supports episodic, semantic, and procedural memories
4. **Search**: Intelligent search across all memory types
5. **Privacy**: Uses connection tokens (user-controlled access)

## Comparison with Other Memory Services

| Feature | InMemoryMemoryService | VertexAiMemoryBankService | GaugidMemoryService |
|---------|----------------------|---------------------------|---------------------|
| Persistence | ❌ No | ✅ Yes (Vertex AI) | ✅ Yes (Gaugid) |
| Memory Types | Full conversation | Extracted memories | Episodic, Semantic, Procedural |
| User Profiles | ❌ No | ❌ No | ✅ Yes |
| Privacy Control | ❌ No | ❌ No | ✅ Yes (user-controlled) |
| Search | Keyword | Semantic | Keyword + Memory Type |

## Advanced Usage

### Custom Memory Extraction

You can customize how memories are extracted by subclassing:

```python
class CustomGaugidMemoryService(GaugidMemoryService):
    async def add_session_to_memory(self, session, app_name=None, user_id=None):
        # Custom extraction logic
        # ... your code ...
        
        # Call parent to store
        await super().add_session_to_memory(session, app_name, user_id)
```

### Multiple Memory Services

You can use multiple memory services in a single agent:

```python
# Framework-configured service (GaugidMemoryService)
framework_memory = GaugidMemoryService(connection_token="...")

# Manual service for document lookup
document_memory = VertexAiMemoryBankService(...)

# Use both in your agent code
```

## References

- [Google ADK Memory Documentation](https://google.github.io/adk-docs/sessions/memory/)
- [Gaugid SDK Documentation](../../../gaugid-sdk-python/README.md)
- [Memory Types Extension](../../../docs/proposals/memory-types-protocol-extension.md)
