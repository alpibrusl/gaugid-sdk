"""
Anthropic Claude + Gaugid: Personalized Chatbot

A chatbot using Claude 4.5 with Gaugid profiles for personalization.
Requires: ANTHROPIC_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
"""

import asyncio
import os
from anthropic import Anthropic
from anthropic.types import MessageParam
from gaugid import GaugidClient


async def load_user_context(client: GaugidClient, user_did: str) -> str:
    """Load user context from Gaugid profile."""
    profile = await client.get_profile(
        user_did=user_did,
        scopes=["a2p:preferences", "a2p:professional", "a2p:context", "a2p:interests"]
    )
    
    # Format memories as context
    memories = profile.get("memories", {}).get("episodic", [])
    context_parts = []
    
    for memory in memories:
        category = memory.get("category", "general")
        content = memory.get("content", "")
        context_parts.append(f"- [{category}] {content}")
    
    return "\n".join(context_parts) if context_parts else "No user context available."


async def chat_with_claude(
    anthropic_client: Anthropic,
    user_context: str,
    messages: list[MessageParam],
    model: str = "claude-4-5"  # Latest Claude 4.5 as of 2026-01
) -> str:
    """Chat with Claude using personalized context."""
    
    system_prompt = f"""You are a helpful AI assistant.

USER PROFILE (from Gaugid - use this to personalize all responses):
{user_context}

Guidelines:
- Adapt your communication style to match user preferences
- Reference their expertise level when explaining concepts
- Consider their current projects and learning goals
- Be aware of their tool preferences
- Personalize examples and recommendations

Be helpful, technical, and precise. Adapt to the user's expertise level."""
    
    response = anthropic_client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=messages
    )
    
    return response.content[0].text


async def main():
    # Check for API keys
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 Anthropic Claude + Gaugid: Personalized Chatbot")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Initialize clients
    anthropic_client = Anthropic(api_key=anthropic_key)
    gaugid_client = GaugidClient(connection_token=connection_token)
    user_did = "did:a2p:user:gaugid:demo"
    
    try:
        # Load user context
        print("1️⃣ Loading user context from Gaugid...")
        user_context = await load_user_context(gaugid_client, user_did)
        print("   📋 User context:")
        for line in user_context.split("\n")[:5]:
            print(f"      {line}")
        print()
        
        # Initialize conversation history
        messages: list[MessageParam] = []
        
        # Interactive conversation
        print("═══════════════════════════════════════════════════════════")
        print("   💬 Chat started! Type 'quit' to exit.")
        print("   Type 'propose' to propose a learned memory.")
        print("═══════════════════════════════════════════════════════════\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == "quit":
                break
            
            if user_input.lower() == "propose":
                print("\n📝 Proposing a learned memory...")
                await gaugid_client.propose_memory(
                    user_did=user_did,
                    content="User is exploring Anthropic Claude API",
                    category="a2p:interests.technology",
                    confidence=0.75
                )
                print("   ✅ Memory proposed!\n")
                continue
            
            if not user_input:
                continue
            
            # Add user message to history
            messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Get response from Claude
            response = await chat_with_claude(
                anthropic_client=anthropic_client,
                user_context=user_context,
                messages=messages
            )
            
            # Add assistant response to history
            messages.append({
                "role": "assistant",
                "content": response
            })
            
            print(f"\n🤖 Assistant: {response}\n")
        
        # Propose final learning
        print("\n2️⃣ Proposing learnings from conversation...")
        await gaugid_client.propose_memory(
            user_did=user_did,
            content="Had a productive conversation using Anthropic Claude",
            category="a2p:context.interactions",
            confidence=0.7
        )
        print("   ✅ Memory proposed!\n")
        
    finally:
        await gaugid_client.close()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Session Complete!")
    print("═══════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    asyncio.run(main())
