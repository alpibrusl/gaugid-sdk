"""
OpenAI Assistants + Gaugid: Personalized Assistant

A persistent OpenAI assistant that uses Gaugid profiles for personalization.
Requires: OPENAI_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
"""

import asyncio
import os
import time
from openai import OpenAI
from gaugid import GaugidClient


async def load_user_context(client: GaugidClient, user_did: str) -> str:
    """Load user context from Gaugid profile and format for OpenAI."""
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


async def create_personalized_assistant(
    openai_client: OpenAI,
    user_context: str,
    user_did: str
) -> str:
    """Create a personalized OpenAI assistant."""
    
    instructions = f"""You are a helpful AI assistant.

USER PROFILE (from Gaugid - use this to personalize all responses):
{user_context}

Guidelines:
- Adapt your communication style to match user preferences
- Reference their expertise level when explaining concepts
- Consider their current projects and learning goals
- Be aware of their tool preferences
- Personalize examples and recommendations

Be helpful, technical, and precise. Adapt to the user's expertise level."""
    
    assistant = openai_client.beta.assistants.create(
        name=f"Personalized Assistant for {user_did}",
        instructions=instructions,
        model="gpt-5.2",  # Latest GPT-5.2 model as of 2026-01
        tools=[{"type": "code_interpreter"}],  # Optional: add tools
    )
    
    return assistant.id


async def main():
    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 OpenAI Assistants + Gaugid: Personalized Assistant")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Initialize clients
    openai_client = OpenAI(api_key=openai_key)
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
        
        # Create personalized assistant
        print("2️⃣ Creating personalized OpenAI assistant...")
        assistant_id = await create_personalized_assistant(
            openai_client=openai_client,
            user_context=user_context,
            user_did=user_did
        )
        print(f"   ✅ Assistant created: {assistant_id}\n")
        
        # Create a thread for this conversation
        print("3️⃣ Creating conversation thread...")
        thread = openai_client.beta.threads.create()
        thread_id = thread.id
        print(f"   ✅ Thread created: {thread_id}\n")
        
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
                    content="User is exploring OpenAI Assistants API",
                    category="a2p:interests.technology",
                    confidence=0.75
                )
                print("   ✅ Memory proposed!\n")
                continue
            
            if not user_input:
                continue
            
            # Add user message to thread
            openai_client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_input
            )
            
            # Run the assistant
            run = openai_client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                time.sleep(0.5)
                run = openai_client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status == "completed":
                # Get the latest messages
                messages = openai_client.beta.threads.messages.list(
                    thread_id=thread_id,
                    limit=1
                )
                
                if messages.data:
                    assistant_message = messages.data[0]
                    if assistant_message.content:
                        content = assistant_message.content[0]
                        if hasattr(content, 'text'):
                            print(f"\n🤖 Assistant: {content.text.value}\n")
            else:
                print(f"\n❌ Error: Run status {run.status}\n")
        
        # Propose final learning
        print("\n4️⃣ Proposing learnings from conversation...")
        await gaugid_client.propose_memory(
            user_did=user_did,
            content="Had a productive conversation using OpenAI Assistants",
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
