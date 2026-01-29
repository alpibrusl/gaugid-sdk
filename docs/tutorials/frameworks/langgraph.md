# LangGraph Integration

This tutorial shows how to integrate Gaugid SDK with **LangGraph** to build a personalized chatbot using state machines.

## Overview

We'll build a **personalized chatbot** that:
- Loads user context from Gaugid profiles into graph state
- Personalizes responses based on user preferences
- Manages conversation state with LangGraph
- Proposes memories learned during conversations

## Prerequisites

Install dependencies using `uv`:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies from pyproject.toml
cd docs
uv pip install -e .[langgraph]
```

Set environment variables:
```bash
export OPENAI_API_KEY="sk-your-key-here"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"
```

## Step 1: Define Graph State

Define the state that includes user context:

```python
from typing import TypedDict, Annotated, Sequence
from operator import add
from langchain_core.messages import BaseMessage

class ChatState(TypedDict):
    """State for the chatbot graph."""
    messages: Annotated[Sequence[BaseMessage], add]
    user_did: str
    user_context: str
```

## Step 2: Load User Context

Create a function to load user context from Gaugid:

```python
from gaugid import GaugidClient

async def load_user_context(
    client: GaugidClient, 
    user_did: str
) -> str:
    """Load user context from Gaugid profile."""
    profile = await client.get_profile(
        user_did=user_did,
        scopes=["a2p:preferences", "a2p:professional", "a2p:context"]
    )
    
    # Format memories as context string
    memories = profile.get("memories", {}).get("episodic", [])
    context_lines = []
    
    for memory in memories:
        category = memory.get("category", "general")
        content = memory.get("content", "")
        context_lines.append(f"- [{category}] {content}")
    
    return "\n".join(context_lines) if context_lines else "No user context available."
```

## Step 3: Create Chatbot Graph

Create the LangGraph chatbot with Gaugid integration:

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

def create_chatbot_graph(llm: ChatOpenAI):
    """Create the LangGraph chatbot with Gaugid integration."""
    
    def chatbot_node(state: ChatState) -> dict:
        """Main chatbot node that generates responses."""
        # Build system prompt with user context
        system_prompt = f"""You are a helpful AI assistant.

USER CONTEXT (from their Gaugid profile - use this to personalize responses):
{state['user_context']}

Guidelines:
- Adapt your communication style to match user preferences
- Reference their expertise level when explaining concepts
- Consider their current learning goals
- Be aware of their tool preferences"""
        
        # Prepare messages with system prompt
        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
        
        # Generate response
        response = llm.invoke(messages)
        
        return {"messages": [response]}
    
    # Build graph
    graph = StateGraph(ChatState)
    graph.add_node("chatbot", chatbot_node)
    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    return graph.compile(checkpointer=MemorySaver())
```

## Step 4: Memory Proposal Function

Create a function to propose memories:

```python
async def propose_learned_memory(
    client: GaugidClient,
    user_did: str,
    content: str,
    category: str,
    confidence: float = 0.7
) -> None:
    """Propose a new memory learned from the conversation."""
    await client.propose_memory(
        user_did=user_did,
        content=content,
        category=category,
        confidence=confidence,
        context="Learned during LangGraph conversation"
    )
```

## Step 5: Complete Example

Here's the complete working example:

```python
import asyncio
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from gaugid import GaugidClient

# Import the functions we defined above
from state import ChatState
from context import load_user_context
from graph import create_chatbot_graph
from memory import propose_learned_memory

async def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 LangGraph + Gaugid: Personalized Chatbot")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Initialize Gaugid client
    client = GaugidClient(connection_token=connection_token)
    user_did = "did:a2p:user:gaugid:demo"
    
    try:
        # Load user context
        print("1️⃣ Loading user context from Gaugid...")
        user_context = await load_user_context(client, user_did)
        print("   📋 User context:")
        for line in user_context.split("\n"):
            print(f"      {line}")
        print()
        
        # Create LLM and graph
        print("2️⃣ Creating LangGraph chatbot...")
        llm = ChatOpenAI(model="gpt-5.2", temperature=0.7)  # Latest GPT-5.2 as of 2026-01
        chatbot = create_chatbot_graph(llm)
        print("   ✅ Chatbot ready\n")
        
        # Initial state
        config = {"configurable": {"thread_id": "demo-thread"}}
        initial_state = {
            "messages": [],
            "user_did": user_did,
            "user_context": user_context,
        }
        
        # Interactive chat loop
        print("═══════════════════════════════════════════════════════════")
        print("   💬 Chat started! Type 'quit' to exit, 'propose' to")
        print("      see how memory proposals work.")
        print("═══════════════════════════════════════════════════════════\n")
        
        state = initial_state
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == "quit":
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == "propose":
                # Demo: Propose a learned memory
                print("\n📝 Proposing a learned memory to user profile...")
                await propose_learned_memory(
                    client=client,
                    user_did=user_did,
                    content="Interested in LangGraph for building AI agents",
                    category="a2p:interests.technology",
                    confidence=0.8
                )
                print("   ✅ Memory proposed! (User would review in their Gaugid app)\n")
                continue
            
            if not user_input:
                continue
            
            # Add user message and run graph
            state["messages"] = list(state["messages"]) + [HumanMessage(content=user_input)]
            
            result = chatbot.invoke(state, config)
            state = result
            
            # Get last AI message
            ai_message = result["messages"][-1]
            print(f"\n🤖 Assistant: {ai_message.content}\n")
        
        # Propose final learning
        print("\n3️⃣ Proposing learnings from conversation...")
        await propose_learned_memory(
            client=client,
            user_did=user_did,
            content="Had a productive conversation about LangGraph",
            category="a2p:context.interactions",
            confidence=0.7
        )
        print("   ✅ Memory proposed!\n")
        
    finally:
        await client.close()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Session Complete!")
    print("═══════════════════════════════════════════════════════════\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced: Multi-Node Graph

For more complex flows, you can add multiple nodes:

```python
def create_advanced_chatbot_graph(llm: ChatOpenAI):
    """Create an advanced chatbot graph with multiple nodes."""
    
    def load_context_node(state: ChatState) -> dict:
        """Node that loads user context (if not already loaded)."""
        if not state.get("user_context"):
            # Load context here if needed
            pass
        return {}
    
    def chatbot_node(state: ChatState) -> dict:
        """Main chatbot node."""
        system_prompt = f"""User context: {state['user_context']}"""
        messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
        response = llm.invoke(messages)
        return {"messages": [response]}
    
    def propose_memory_node(state: ChatState) -> dict:
        """Node that proposes memories based on conversation."""
        # Analyze conversation and propose memories
        # This would be called periodically or at conversation end
        return {}
    
    # Build graph
    graph = StateGraph(ChatState)
    graph.add_node("load_context", load_context_node)
    graph.add_node("chatbot", chatbot_node)
    graph.add_node("propose_memory", propose_memory_node)
    
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "chatbot")
    graph.add_edge("chatbot", END)
    # Add conditional edge to propose_memory based on conversation length
    
    return graph.compile(checkpointer=MemorySaver())
```

## Key Integration Points

### 1. State Management
```python
# Include user context in state
state = {
    "messages": [],
    "user_did": user_did,
    "user_context": user_context,  # Loaded from Gaugid
}
```

### 2. System Prompt in Nodes
```python
def chatbot_node(state: ChatState) -> dict:
    system_prompt = f"""User context: {state['user_context']}"""
    # Use in LLM call
```

### 3. Memory Proposals
```python
# Propose memories after conversation
await propose_learned_memory(client, user_did, content, category)
```

## Best Practices

1. **Load context once** and store in state
2. **Use checkpoints** to persist conversation state
3. **Add conditional edges** for memory proposals
4. **Handle errors** in graph nodes gracefully
5. **Respect rate limits** when proposing memories

## Comparison with LangChain

| Feature | LangChain | LangGraph |
|---------|-----------|-----------|
| **State Management** | Chain state | Graph state with checkpoints |
| **Complexity** | Simple chains | Complex state machines |
| **Persistence** | Manual | Built-in checkpoints |
| **Best For** | Sequential workflows | Multi-step processes |

## Next Steps

- Learn about [OpenAI Assistants](openai-assistants.md) for persistent assistants
- Check out [CrewAI](crewai.md) for multi-agent systems
- See [Advanced Tutorials](../advanced/multi-agent.md) for complex workflows

---

**Ready to try it?** Run the example and build state machine chatbots with LangGraph and Gaugid!
