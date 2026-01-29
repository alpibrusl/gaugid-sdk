"""
LangGraph + Gaugid: Personalized Chatbot

A real LangGraph chatbot that uses Gaugid profiles for personalization.
Requires: OPENAI_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
"""

import asyncio
import os
from typing import TypedDict, Annotated, Sequence
from operator import add

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from gaugid import GaugidClient


class ChatState(TypedDict):
    """State for the chatbot graph."""
    messages: Annotated[Sequence[BaseMessage], add]
    user_did: str
    user_context: str


async def load_user_context(client: GaugidClient, user_did: str) -> str:
    """Load user context from Gaugid profile for the agent."""
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
        llm = ChatOpenAI(model="gpt-5.2", temperature=0.7)
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
