"""
LlamaIndex + Gaugid Memory Block Example

This example demonstrates how to use GaugidMemoryBlock with LlamaIndex's
Memory system, allowing agents to store and retrieve long-term memories
using Gaugid profiles.

Based on: https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/memory/memory.py

Requires: OPENAI_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
Install: pip install gaugid[llama-index]
"""

import os
import asyncio

try:
    from llama_index.core.memory import Memory
    from llama_index.core.base.llms.types import ChatMessage
    from llama_index.llms.openai import OpenAI
    from gaugid.integrations.llama_index import GaugidMemoryBlock
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False
    print("⚠️  LlamaIndex not installed. Install with: pip install gaugid[llama-index]")


async def main():
    """Main function demonstrating LlamaIndex + Gaugid Memory Block integration."""
    
    if not LLAMA_INDEX_AVAILABLE:
        print("❌ LlamaIndex is not installed.")
        print("   Install with: pip install gaugid[llama-index]")
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
    print("     🚀 LlamaIndex + Gaugid Memory Block")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Create Gaugid memory blocks
    print("1️⃣ Creating GaugidMemoryBlocks...")
    
    # User preferences block (semantic memory)
    preferences_block = GaugidMemoryBlock(
        name="user_preferences",
        connection_token=connection_token,
        description="User preferences and settings",
        priority=1,  # High priority - don't truncate
        memory_type="semantic",
    )
    
    # Knowledge block (semantic memory)
    knowledge_block = GaugidMemoryBlock(
        name="user_knowledge",
        connection_token=connection_token,
        description="User's knowledge and facts",
        priority=2,
        memory_type="semantic",
    )
    
    # Context block (episodic memory)
    context_block = GaugidMemoryBlock(
        name="conversation_context",
        connection_token=connection_token,
        description="Conversation context and history",
        priority=3,  # Lower priority - can be truncated
        memory_type="episodic",
    )
    
    print("   ✅ Created 3 memory blocks:")
    print("      - user_preferences (semantic)")
    print("      - user_knowledge (semantic)")
    print("      - conversation_context (episodic)\n")
    
    # Create LlamaIndex Memory with Gaugid blocks
    print("2️⃣ Creating LlamaIndex Memory with Gaugid blocks...")
    memory = Memory(
        memory_blocks=[
            preferences_block,
            knowledge_block,
            context_block,
        ],
        session_id="user-123",
        token_limit=30000,
    )
    print("   ✅ Memory created\n")
    
    # Create LLM
    llm = OpenAI(api_key=openai_api_key, model="gpt-4o-mini")
    
    print("═══════════════════════════════════════════════════════════")
    print("   💬 Example Usage")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Add messages to memory
    print("3️⃣ Adding messages to memory...")
    user_message = ChatMessage(
        role="user",
        content="I prefer dark mode for all applications."
    )
    await memory.aput(user_message)
    print(f"   ✅ Added: {user_message.content}\n")
    
    # Add another message
    user_message2 = ChatMessage(
        role="user",
        content="I'm working on a Python project using FastAPI."
    )
    await memory.aput(user_message2)
    print(f"   ✅ Added: {user_message2.content}\n")
    
    # Get messages with memory blocks
    print("4️⃣ Retrieving messages with memory blocks...")
    messages = await memory.aget()
    print(f"   ✅ Retrieved {len(messages)} messages with memory context\n")
    
    # Check memory block content
    print("5️⃣ Checking memory block content...")
    preferences = await preferences_block._aget()
    print(f"   ✅ Preferences block: {preferences[:100]}...\n" if preferences else "   ✅ Preferences block: (empty)\n")
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 LlamaIndex Memory can now:")
    print("   - Store long-term memories in Gaugid profiles")
    print("   - Retrieve memories when context is needed")
    print("   - Manage memory blocks with different priorities")
    print("   - Persist knowledge across conversations!")


if __name__ == "__main__":
    asyncio.run(main())
