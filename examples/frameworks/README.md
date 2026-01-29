# Gaugid SDK Framework Examples

Working examples for integrating Gaugid SDK with popular AI agent frameworks.

## Prerequisites

1. **Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install dependencies**:
```bash
cd ../docs
uv pip install -e .[all]  # Install all framework dependencies
```

3. **Set environment variables**:
```bash
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export GOOGLE_API_KEY="your-google-api-key"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"
```

## Examples

### Basic Framework Integrations

These examples show basic integration patterns (loading context, personalizing responses):

#### LangChain
```bash
python langchain_example.py
```

#### LangGraph
```bash
python langgraph_example.py
```

#### Anthropic Claude
```bash
python anthropic_example.py
```

#### OpenAI Assistants
```bash
python openai_assistants_example.py
```

#### Google Gemini
```bash
python gemini_example.py
```

### Advanced Memory Integrations

These examples demonstrate using Gaugid as a persistent memory backend for framework-specific memory systems:

### Google ADK (Agent Development Kit)
```bash
python google_adk_example.py
```

**Note**: Requires `google-adk>=1.22.0`, `python-genai>=1.57.0`, and `GOOGLE_API_KEY` environment variable.

### Google ADK with Gaugid Memory Service
```bash
python google_adk_with_gaugid_memory.py
```

**Note**: This example shows how to use `GaugidMemoryService` as a `MemoryService` implementation for Google ADK, allowing agents to store and retrieve long-term memories from Gaugid profiles. See [gaugid_memory_service.py](./gaugid_memory_service.py) for the implementation.

**Installation**: `pip install gaugid[adk]`

Based on: https://google.github.io/adk-docs/sessions/memory/

### LangGraph Store
```bash
python langgraph_store_example.py
```

**Note**: Demonstrates using `GaugidStore` as a `BaseStore` for LangGraph, allowing agents to use Gaugid profiles as persistent key-value stores.

**Installation**: `pip install gaugid[langgraph]`

### LangMem + Gaugid Store
```bash
python langmem_gaugid_example.py
```

**Note**: Shows how `GaugidStore` works seamlessly with LangMem for automatic memory management.

**Installation**: `pip install gaugid[langgraph] langmem`

### Anthropic Claude Memory Tool
```bash
python anthropic_memory_tool_example.py
```

**Note**: Demonstrates using `GaugidMemoryTool` as the backend for Anthropic's memory tool, allowing Claude to store and retrieve information across conversations.

**Installation**: `pip install gaugid[anthropic]`

Based on: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool

### OpenAI Agents SDK Session
```bash
python openai_agents_session_example.py
```

**Note**: Shows how to use `GaugidSession` as a `Session` backend for OpenAI Agents SDK, allowing agents to maintain conversation history across sessions.

**Installation**: `pip install gaugid[openai]`

Based on: https://openai.github.io/openai-agents-python/ref/memory/

### LlamaIndex Memory Block
```bash
python llama_index_gaugid_example.py
```

**Note**: Demonstrates using `GaugidMemoryBlock` as a `BaseMemoryBlock` for LlamaIndex, allowing agents to store and retrieve long-term memories.

**Installation**: `pip install gaugid[llama-index]`

Based on: https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/memory/memory.py

### Agno Memory Database
```bash
python agno_gaugid_example.py
```

**Note**: Shows how to use `GaugidDb` as a database backend for Agno's MemoryManager, allowing agents to store and retrieve user memories.

**Installation**: `pip install gaugid[agno]`

Based on: https://github.com/agno-agi/agno/blob/main/libs/agno/agno/memory/manager.py

### CrewAI
```bash
python crewai_example.py
```

**Note**: Requires `crewai>=1.8.0`, `crewai-tools>=1.8.0`, and `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`).
Optional: `SERPER_API_KEY` for search functionality.

## Running Examples

Each example demonstrates:
1. Loading user context from Gaugid profiles
2. Personalizing AI responses based on user preferences
3. Proposing memories learned during conversations

All examples use the latest model versions as of January 2026:
- GPT-5.2
- Claude 4.5
- Gemini 3 Flash/Pro

## Interactive Features

During conversations, you can:
- Type `quit` to exit
- Type `propose` to manually propose a memory
- Normal conversation will automatically propose memories at the end
