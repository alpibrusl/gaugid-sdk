"""
Agno + Gaugid Database Example

This example demonstrates how to use GaugidDb with Agno's MemoryManager,
allowing agents to store and retrieve user memories using Gaugid profiles.

Based on: https://github.com/agno-agi/agno/blob/main/libs/agno/agno/memory/manager.py

Requires: OPENAI_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
Install: pip install gaugid[agno]
"""

import os
import asyncio

try:
    from agno.memory.manager import MemoryManager
    from agno.models.openai import OpenAIChat
    from gaugid.integrations.agno import GaugidDb
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    print("⚠️  Agno not installed. Install with: pip install gaugid[agno]")


async def main():
    """Main function demonstrating Agno + Gaugid Database integration."""
    
    if not AGNO_AVAILABLE:
        print("❌ Agno is not installed.")
        print("   Install with: pip install gaugid[agno]")
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
    print("     🚀 Agno + Gaugid Database")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Create Gaugid database
    print("1️⃣ Creating GaugidDb for Agno...")
    db = GaugidDb(
        connection_token=connection_token,
        user_id="user-123",
        memory_type="semantic",
    )
    print("   ✅ GaugidDb created\n")
    
    # Create MemoryManager with Gaugid database
    print("2️⃣ Creating Agno MemoryManager with GaugidDb...")
    memory_manager = MemoryManager(
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        db=db,
        add_memories=True,
        update_memories=True,
        delete_memories=False,  # Gaugid doesn't support deletion yet
        clear_memories=False,   # Gaugid doesn't support bulk deletion yet
    )
    print("   ✅ MemoryManager created\n")
    
    print("═══════════════════════════════════════════════════════════")
    print("   💬 Example Usage")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Get user memories
    print("3️⃣ Retrieving user memories...")
    memories = await memory_manager.aget_user_memories(user_id="user-123")
    print(f"   ✅ Found {len(memories)} existing memories\n")
    
    # Add a memory (via MemoryManager tools)
    print("4️⃣ MemoryManager can automatically add memories during agent runs")
    print("   The agent will use memory tools to store important information\n")
    
    # Search memories
    print("5️⃣ Searching memories...")
    matching = await db.search_memories(
        query="preferences",
        user_id="user-123",
        limit=5
    )
    print(f"   ✅ Found {len(matching)} matching memories\n")
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 Agno MemoryManager can now:")
    print("   - Store user memories in Gaugid profiles")
    print("   - Retrieve memories for context")
    print("   - Search memories by query")
    print("   - Manage memories with topics and metadata")
    print("   - Persist knowledge across agent runs!")


if __name__ == "__main__":
    asyncio.run(main())
