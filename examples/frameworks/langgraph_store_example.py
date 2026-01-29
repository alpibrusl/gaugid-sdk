"""
LangGraph + Gaugid Store Example

This example demonstrates how to use GaugidStore as a BaseStore for LangGraph,
allowing agents to use Gaugid profiles as persistent key-value stores.

Requires: OPENAI_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
Install: pip install gaugid[langgraph]
"""

import asyncio
import os
from typing import TypedDict, Annotated, Sequence
from operator import add

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
    from langgraph.graph import StateGraph, START, END
    from gaugid.integrations.langgraph import GaugidStore
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️  LangGraph not installed. Install with: pip install gaugid[langgraph]")


class ChatState(TypedDict):
    """State for the chatbot graph."""
    messages: Annotated[Sequence[BaseMessage], add]
    user_context: str


async def main():
    """Main function demonstrating LangGraph + Gaugid Store integration."""
    
    if not LANGGRAPH_AVAILABLE:
        print("❌ LangGraph is not installed.")
        print("   Install with: pip install gaugid[langgraph]")
        return
    
    # Check for API keys
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 LangGraph + Gaugid Store")
    print("═══════════════════════════════════════════════════════════\n")
    
    try:
        # Create Gaugid store
        print("1️⃣ Creating GaugidStore for LangGraph...")
        store = GaugidStore(
            connection_token=connection_token,
            namespace_prefix=("langgraph", "chatbot"),
            memory_type="episodic",
        )
        print("   ✅ GaugidStore created\n")
        
        # Create LLM
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Define chatbot node
        def chatbot_node(state: ChatState) -> dict:
            """Main chatbot node that generates responses."""
            system_prompt = f"""You are a helpful AI assistant.

USER CONTEXT (from their Gaugid profile):
{state['user_context']}

Adapt your responses based on the user's preferences and context."""
            
            messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
            response = llm.invoke(messages)
            
            return {"messages": [response]}
        
        # Build graph
        print("2️⃣ Creating LangGraph with GaugidStore...")
        graph = StateGraph(ChatState)
        graph.add_node("chatbot", chatbot_node)
        graph.add_edge(START, "chatbot")
        graph.add_edge("chatbot", END)
        
        # Compile with GaugidStore as checkpointer
        app = graph.compile(checkpointer=store)
        print("   ✅ Graph compiled with GaugidStore\n")
        
        # Example conversation
        print("═══════════════════════════════════════════════════════════")
        print("   💬 Example Conversation")
        print("═══════════════════════════════════════════════════════════\n")
        
        config = {"configurable": {"thread_id": "example-thread-1"}}
        
        # Initial state with user context
        initial_state = {
            "messages": [HumanMessage(content="Hello! Tell me about yourself.")],
            "user_context": "User is interested in AI and machine learning.",
        }
        
        result = app.invoke(initial_state, config)
        print(f"User: {initial_state['messages'][0].content}")
        print(f"Assistant: {result['messages'][-1].content}\n")
        
        # Store some data in the store
        print("3️⃣ Storing data in GaugidStore...")
        await store.aput(
            namespace=("langgraph", "chatbot", "preferences"),
            key="user_pref_1",
            value={"preference": "prefers technical explanations", "source": "conversation"},
        )
        print("   ✅ Data stored\n")
        
        # Retrieve data
        print("4️⃣ Retrieving data from GaugidStore...")
        item = await store.aget(
            namespace=("langgraph", "chatbot", "preferences"),
            key="user_pref_1",
        )
        if item:
            print(f"   ✅ Retrieved: {item.value}\n")
        
        # Search data
        print("5️⃣ Searching GaugidStore...")
        results = await store.asearch(
            namespace_prefix=("langgraph", "chatbot"),
            limit=5,
        )
        print(f"   ✅ Found {len(results)} items\n")
        
    finally:
        # Cleanup
        if 'store' in locals():
            await store.close()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 The store persists data in Gaugid profiles across sessions!")


if __name__ == "__main__":
    asyncio.run(main())
