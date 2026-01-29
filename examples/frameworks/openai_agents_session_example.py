"""
OpenAI Agents SDK + Gaugid Session Example

This example demonstrates how to use GaugidSession with OpenAI Agents SDK,
allowing agents to maintain conversation history across sessions using
Gaugid profiles.

Based on: https://openai.github.io/openai-agents-python/ref/memory/

Requires: OPENAI_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
Install: pip install gaugid[openai]
"""

import os

try:
    from openai import OpenAI
    from openai.agents import Agent
    from gaugid.integrations.openai import GaugidSession
    OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    OPENAI_AGENTS_AVAILABLE = False
    print("⚠️  OpenAI Agents SDK not installed. Install with: pip install gaugid[openai]")


async def main():
    """Main function demonstrating OpenAI Agents SDK + Gaugid Session integration."""
    
    if not OPENAI_AGENTS_AVAILABLE:
        print("❌ OpenAI Agents SDK is not installed.")
        print("   Install with: pip install gaugid[openai]")
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
    print("     🚀 OpenAI Agents SDK + Gaugid Session")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Create Gaugid session
    print("1️⃣ Creating GaugidSession...")
    session = GaugidSession(
        session_id="user-123",
        connection_token=connection_token,
        memory_type="episodic",
    )
    print("   ✅ GaugidSession created\n")
    
    # Create OpenAI client
    client = OpenAI(api_key=openai_api_key)
    
    # Create agent with Gaugid session
    print("2️⃣ Creating OpenAI agent with GaugidSession...")
    agent = Agent(
        model="gpt-4o",
        session=session,
    )
    print("   ✅ Agent created with persistent session\n")
    
    print("═══════════════════════════════════════════════════════════")
    print("   💬 Example Conversation")
    print("═══════════════════════════════════════════════════════════\n")
    
    # First message
    print("3️⃣ Sending first message...")
    result1 = await agent.run(
        "Hello! My name is Alice and I'm interested in Python programming."
    )
    print(f"   User: Hello! My name is Alice and I'm interested in Python programming.")
    print(f"   Agent: {result1.output}\n")
    
    # Second message (should remember context)
    print("4️⃣ Sending second message (agent should remember context)...")
    result2 = await agent.run(
        "What's my name and what am I interested in?"
    )
    print(f"   User: What's my name and what am I interested in?")
    print(f"   Agent: {result2.output}\n")
    
    # Check session items
    print("5️⃣ Checking session history...")
    items = await session.get_items()
    print(f"   ✅ Session contains {len(items)} items\n")
    
    # Clear session (optional)
    # await session.clear_session()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 The agent can now:")
    print("   - Maintain conversation history across sessions")
    print("   - Store session data in Gaugid profiles")
    print("   - Remember context from previous conversations")
    print("   - Persist session state using Gaugid storage!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
