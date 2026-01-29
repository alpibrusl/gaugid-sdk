"""
Google Gemini + Gaugid: Personalized Chatbot

A chatbot using Gemini 3 with Gaugid profiles for personalization.
Requires: GOOGLE_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
"""

import asyncio
import os
import google.generativeai as genai
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


def create_personalized_model(
    api_key: str,
    user_context: str,
    model_name: str = "gemini-3-flash-exp"  # Latest Gemini 3 Flash as of 2026-01
):
    """Create a Gemini model with personalized system instruction."""
    
    genai.configure(api_key=api_key)
    
    system_instruction = f"""You are a helpful AI assistant.

USER PROFILE (from Gaugid - use this to personalize all responses):
{user_context}

Guidelines:
- Adapt your communication style to match user preferences
- Reference their expertise level when explaining concepts
- Consider their current projects and learning goals
- Be aware of their tool preferences
- Personalize examples and recommendations

Be helpful, technical, and precise. Adapt to the user's expertise level."""
    
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
    
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction,
        generation_config=generation_config
    )
    
    return model


async def main():
    # Check for API keys
    google_key = os.getenv("GOOGLE_API_KEY")
    if not google_key:
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 Google Gemini + Gaugid: Personalized Chatbot")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Initialize clients
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
        
        # Create personalized model
        print("2️⃣ Creating personalized Gemini model...")
        model = create_personalized_model(google_key, user_context)
        print("   ✅ Model ready\n")
        
        # Initialize chat session
        chat = model.start_chat(history=[])
        
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
                    content="User is exploring Google Gemini API",
                    category="a2p:interests.technology",
                    confidence=0.75
                )
                print("   ✅ Memory proposed!\n")
                continue
            
            if not user_input:
                continue
            
            # Get response from Gemini
            response = chat.send_message(user_input)
            print(f"\n🤖 Assistant: {response.text}\n")
        
        # Propose final learning
        print("\n3️⃣ Proposing learnings from conversation...")
        await gaugid_client.propose_memory(
            user_did=user_did,
            content="Had a productive conversation using Google Gemini",
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
