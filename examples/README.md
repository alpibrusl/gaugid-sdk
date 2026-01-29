# Gaugid SDK Examples

Complete working examples and interactive notebooks for integrating Gaugid SDK with popular AI agent frameworks.

## Structure

```
examples/
├── frameworks/          # Framework integration examples
│   ├── langchain_example.py
│   ├── langgraph_example.py
│   ├── anthropic_example.py
│   ├── openai_assistants_example.py
│   ├── gemini_example.py
│   └── README.md
├── use-cases/          # Realistic business use cases
│   ├── travel_agency.py
│   ├── food_delivery.py
│   ├── agent_to_agent_b2b.py
│   ├── child_safety_agent.py
│   └── README.md
└── notebooks/          # Jupyter notebook examples
    ├── langchain_gaugid.ipynb
    ├── anthropic_gaugid.ipynb
    ├── gemini_gaugid.ipynb
    └── README.md
```

## Quick Start

### Python Scripts

1. **Install dependencies**:
```bash
cd docs
uv pip install -e .[all]  # or specific framework
```

2. **Set environment variables**:
```bash
export OPENAI_API_KEY="sk-your-key"
export ANTHROPIC_API_KEY="sk-ant-your-key"
export GOOGLE_API_KEY="your-google-key"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"
```

3. **Run an example**:
```bash
cd examples/frameworks
python langchain_example.py
```

### Jupyter Notebooks

1. **Install Jupyter**:
```bash
uv pip install jupyter ipykernel
```

2. **Start Jupyter**:
```bash
jupyter notebook
# or
jupyter lab
```

3. **Open a notebook** and follow the instructions

## Available Examples

### Use Cases

Realistic business scenarios demonstrating Gaugid SDK integration:

- **[Travel Agency](use-cases/travel_agency.py)** - Personalized travel planning with ADK + Gemini
- **[Food Delivery](use-cases/food_delivery.py)** - Personalized ordering with LangGraph + Gemini
- **[A2A B2B](use-cases/agent_to_agent_b2b.py)** - Business agent negotiation with A2P-Signature
- **[Child Safety](use-cases/child_safety_agent.py)** - Child-safe agent with content restrictions

See [use-cases/README.md](use-cases/README.md) for detailed documentation.

### Basic Framework Integrations

These examples show basic integration patterns (loading context, personalizing responses):

#### LangChain
- **Script**: `frameworks/langchain_example.py`
- **Notebook**: `notebooks/langchain_gaugid.ipynb`
- Demonstrates personalized chains with Gaugid memory integration

#### LangGraph
- **Script**: `frameworks/langgraph_example.py`
- Demonstrates state machine chatbots with user context

#### Anthropic Claude
- **Script**: `frameworks/anthropic_example.py`
- **Notebook**: `notebooks/anthropic_gaugid.ipynb`
- Demonstrates Claude 4.5 integration with long context

#### OpenAI Assistants
- **Script**: `frameworks/openai_assistants_example.py`
- Demonstrates persistent assistants with personalized instructions

#### Google Gemini
- **Script**: `frameworks/gemini_example.py`
- **Notebook**: `notebooks/gemini_gaugid.ipynb`
- Demonstrates Gemini 3 integration with multimodal support

#### Google ADK
- **Script**: `frameworks/google_adk_example.py`
- **Notebook**: `notebooks/google_adk_gaugid.ipynb`
- Demonstrates Google ADK integration with personalized agents

#### CrewAI
- **Script**: `frameworks/crewai_example.py`
- **Notebook**: `notebooks/crewai_gaugid.ipynb`
- Demonstrates multi-agent teams with personalized context

### Memory Backend Integrations

These examples demonstrate using Gaugid as a persistent memory backend for framework-specific memory systems:

#### Google ADK Memory Service
- **Script**: `frameworks/google_adk_with_gaugid_memory.py`
- **Installation**: `pip install gaugid[adk]`
- Uses `GaugidMemoryService` as a `MemoryService` for Google ADK
- Based on: https://google.github.io/adk-docs/sessions/memory/

#### LangGraph Store
- **Script**: `frameworks/langgraph_store_example.py`
- **Installation**: `pip install gaugid[langgraph]`
- Uses `GaugidStore` as a `BaseStore` for LangGraph checkpoints

#### LangMem + Gaugid Store
- **Script**: `frameworks/langmem_gaugid_example.py`
- **Installation**: `pip install gaugid[langgraph] langmem`
- Shows how `GaugidStore` works with LangMem for automatic memory management

#### Anthropic Memory Tool
- **Script**: `frameworks/anthropic_memory_tool_example.py`
- **Installation**: `pip install gaugid[anthropic]`
- Uses `GaugidMemoryTool` as the backend for Claude's memory tool
- Based on: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool

#### OpenAI Agents Session
- **Script**: `frameworks/openai_agents_session_example.py`
- **Installation**: `pip install gaugid[openai]`
- Uses `GaugidSession` as a `Session` backend for OpenAI Agents SDK
- Based on: https://openai.github.io/openai-agents-python/ref/memory/

#### LlamaIndex Memory Block
- **Script**: `frameworks/llama_index_gaugid_example.py`
- **Installation**: `pip install gaugid[llama-index]`
- Uses `GaugidMemoryBlock` as a `BaseMemoryBlock` for LlamaIndex
- Based on: https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/memory/memory.py

#### Agno Memory Database
- **Script**: `frameworks/agno_gaugid_example.py`
- **Installation**: `pip install gaugid[agno]`
- Uses `GaugidDb` as a database backend for Agno's MemoryManager
- Based on: https://github.com/agno-agi/agno/blob/main/libs/agno/agno/memory/manager.py

## Features Demonstrated

All examples show:
- ✅ Loading user context from Gaugid profiles
- ✅ Personalizing AI responses based on user preferences
- ✅ Proposing memories learned during conversations
- ✅ Error handling and best practices

## Model Versions

All examples use the latest model versions as of January 2026:
- **GPT-5.2** (OpenAI)
- **Claude 4.5** (Anthropic)
- **Gemini 3 Flash/Pro** (Google)

## Documentation

For detailed tutorials, see the [Framework Integration Tutorials](../docs/tutorials/frameworks/).

## Contributing

Want to add an example? Follow the pattern in existing examples:
1. Load user context from Gaugid
2. Integrate with the framework
3. Personalize responses
4. Propose memories

---

**Ready to get started?** Pick an example and run it!
