# Framework Integration Examples

All framework tutorials use `uv` for dependency management. Dependencies are defined in `docs/pyproject.toml`.

## Quick Setup

1. **Install uv** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install dependencies for a specific framework**:
```bash
cd docs
uv pip install -e .[langchain]    # For LangChain
uv pip install -e .[langgraph]    # For LangGraph
uv pip install -e .[openai]        # For OpenAI
uv pip install -e .[anthropic]     # For Anthropic Claude
uv pip install -e .[gemini]        # For Google Gemini
uv pip install -e .[google-adk]    # For Google ADK
uv pip install -e .[crewai]        # For CrewAI
uv pip install -e .[llama-index]   # For LlamaIndex
uv pip install -e .[agno]          # For Agno
```

3. **Install all dependencies**:
```bash
cd docs
uv pip install -e .[all]
```

## Framework-Specific Tutorials

Each tutorial demonstrates the same use case (personalized chatbot) with different frameworks:

### Basic Integrations
- [LangChain](langchain.md) - Chains and sequential workflows
- [LangGraph](langgraph.md) - State machines and complex flows
- [OpenAI Assistants](openai-assistants.md) - GPT-4 with persistent assistants
- [Anthropic Claude](anthropic.md) - Claude 4.5 with long context
- [Google Gemini](gemini.md) - Fast inference and multimodal
- [Google ADK](google-adk.md) - Production multi-agent systems
- [CrewAI](crewai.md) - Multi-agent teams and collaboration

### Memory Backend Integrations

These frameworks support using Gaugid as a persistent memory backend:

- **Google ADK**: Use `GaugidMemoryService` as a `MemoryService` - See [examples](../../../examples/frameworks/google_adk_with_gaugid_memory.py)
- **LangGraph**: Use `GaugidStore` as a `BaseStore` - See [examples](../../../examples/frameworks/langgraph_store_example.py)
- **LangMem**: Works with `GaugidStore` - See [examples](../../../examples/frameworks/langmem_gaugid_example.py)
- **Anthropic**: Use `GaugidMemoryTool` as memory tool backend - See [examples](../../../examples/frameworks/anthropic_memory_tool_example.py)
- **OpenAI Agents**: Use `GaugidSession` as a `Session` backend - See [examples](../../../examples/frameworks/openai_agents_session_example.py)
- **LlamaIndex**: Use `GaugidMemoryBlock` as a `BaseMemoryBlock` - See [examples](../../../examples/frameworks/llama_index_gaugid_example.py)
- **Agno**: Use `GaugidDb` as a database backend - See [examples](../../../examples/frameworks/agno_gaugid_example.py)

**Installation**: `pip install gaugid[adk]` or `pip install gaugid[langgraph]` etc.

## Model Versions (2026-01)

All tutorials use the latest model versions as of January 2026:

- **Claude**: `claude-4-5` (latest)
- **GPT-5.2**: `gpt-5.2` (latest, released Dec 2025)
- **Gemini 3 Flash**: `gemini-3-flash-exp` (latest, released Dec 2025)
- **Gemini 3 Pro**: `gemini-3-pro` (latest, released Nov 2025)

Dependencies are managed via `uv` and `pyproject.toml`, so versions are automatically resolved to the latest compatible versions.
