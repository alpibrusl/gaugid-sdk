"""
Gaugid SDK Integrations

Optional integrations with popular AI agent frameworks.
These modules require additional dependencies to be installed.

Install with: pip install gaugid[adk] or pip install gaugid[langgraph]
"""

__all__ = []

# Google ADK integration (requires google-adk package)
try:
    from gaugid.integrations.adk import GaugidMemoryService
    __all__.append("GaugidMemoryService")
except ImportError:
    # ADK not installed - this is expected if gaugid[adk] is not installed
    pass

# LangGraph integration (requires langgraph package)
try:
    from gaugid.integrations.langgraph import GaugidStore
    __all__.append("GaugidStore")
except ImportError:
    # LangGraph not installed - this is expected if gaugid[langgraph] is not installed
    pass

# Anthropic integration (requires anthropic package)
try:
    from gaugid.integrations.anthropic import GaugidMemoryTool
    __all__.append("GaugidMemoryTool")
except ImportError:
    # Anthropic not installed - this is expected if gaugid[anthropic] is not installed
    pass

# OpenAI Agents integration (requires openai-agents package)
try:
    from gaugid.integrations.openai import GaugidSession
    __all__.append("GaugidSession")
except ImportError:
    # OpenAI Agents not installed - this is expected if gaugid[openai] is not installed
    pass

# LlamaIndex integration (requires llama-index-core package)
try:
    from gaugid.integrations.llama_index import GaugidMemoryBlock
    __all__.append("GaugidMemoryBlock")
except ImportError:
    # LlamaIndex not installed - this is expected if gaugid[llama-index] is not installed
    pass

# Agno integration (requires agno package)
try:
    from gaugid.integrations.agno import GaugidDb
    __all__.append("GaugidDb")
except ImportError:
    # Agno not installed - this is expected if gaugid[agno] is not installed
    pass
