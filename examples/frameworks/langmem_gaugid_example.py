"""
LangMem + Gaugid Store Example

This example demonstrates how to use GaugidStore with LangMem for automatic
memory management in LangGraph agents.

LangMem provides memory tools that work with any BaseStore implementation,
including our GaugidStore. This allows agents to automatically extract,
store, and search memories using Gaugid profiles.

Based on: https://langchain-ai.github.io/langmem/#creating-an-agent

Requires: ANTHROPIC_API_KEY (or other LLM provider) and GAUGID_CONNECTION_TOKEN
Install: pip install gaugid[langgraph] langmem
"""

import os

try:
    from langgraph.prebuilt import create_react_agent
    from langmem import create_manage_memory_tool, create_search_memory_tool
    from gaugid.integrations.langgraph import GaugidStore
    LANGMEM_AVAILABLE = True
except ImportError:
    LANGMEM_AVAILABLE = False
    print("⚠️  LangMem or LangGraph not installed.")
    print("   Install with: pip install gaugid[langgraph] langmem")


def main():
    """Main function demonstrating LangMem + Gaugid Store integration."""
    
    if not LANGMEM_AVAILABLE:
        print("❌ Required packages not installed.")
        print("   Install with: pip install gaugid[langgraph] langmem")
        return
    
    # Check for API keys
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("   You can also use OPENAI_API_KEY or other supported providers")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 LangMem + Gaugid Store")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Create GaugidStore (works with LangMem!)
    print("1️⃣ Creating GaugidStore for LangMem...")
    store = GaugidStore(
        connection_token=connection_token,
        namespace_prefix=("langmem", "agent"),
        memory_type="episodic",  # or "semantic" for long-term knowledge
    )
    print("   ✅ GaugidStore created\n")
    
    # Create agent with LangMem memory tools
    print("2️⃣ Creating agent with LangMem memory tools...")
    agent = create_react_agent(
        "anthropic:claude-3-5-sonnet-latest",
        tools=[
            # Memory tools use GaugidStore for persistence
            create_manage_memory_tool(namespace=("memories",)),
            create_search_memory_tool(namespace=("memories",)),
        ],
        store=store,  # LangMem uses BaseStore - GaugidStore works!
    )
    print("   ✅ Agent created with memory capabilities\n")
    
    print("═══════════════════════════════════════════════════════════")
    print("   💬 Example Conversation")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Store a memory
    print("3️⃣ Storing a memory...")
    response1 = agent.invoke(
        {"messages": [{"role": "user", "content": "Remember that I prefer dark mode."}]}
    )
    print(f"   User: Remember that I prefer dark mode.")
    print(f"   Agent: {response1['messages'][-1].content}\n")
    
    # Retrieve the memory
    print("4️⃣ Retrieving stored memory...")
    response2 = agent.invoke(
        {"messages": [{"role": "user", "content": "What are my lighting preferences?"}]}
    )
    print(f"   User: What are my lighting preferences?")
    print(f"   Agent: {response2['messages'][-1].content}\n")
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 The agent automatically:")
    print("   - Extracts important information from conversations")
    print("   - Stores memories in Gaugid profiles via GaugidStore")
    print("   - Searches past memories when relevant")
    print("   - Persists knowledge across sessions!")


if __name__ == "__main__":
    main()
