"""
Anthropic Claude Memory Tool + Gaugid Example

This example demonstrates how to use GaugidMemoryTool with Anthropic's
memory tool, allowing Claude to store and retrieve information across
conversations using Gaugid profiles.

Based on: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool

Requires: ANTHROPIC_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
Install: pip install gaugid[anthropic]
"""

import os

try:
    from anthropic import Anthropic
    from gaugid.integrations.anthropic import GaugidMemoryTool
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Anthropic SDK not installed. Install with: pip install gaugid[anthropic]")


def main():
    """Main function demonstrating Anthropic Memory Tool + Gaugid integration."""
    
    if not ANTHROPIC_AVAILABLE:
        print("❌ Anthropic SDK is not installed.")
        print("   Install with: pip install gaugid[anthropic]")
        return
    
    # Check for API keys
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 Anthropic Memory Tool + Gaugid")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Create Gaugid memory tool
    print("1️⃣ Creating GaugidMemoryTool...")
    memory_tool = GaugidMemoryTool(
        connection_token=connection_token,
        namespace_prefix="claude",
        memory_type="episodic",
    )
    print("   ✅ GaugidMemoryTool created\n")
    
    # Create Anthropic client
    client = Anthropic(api_key=anthropic_api_key)
    
    print("2️⃣ Claude will automatically use Gaugid for memory storage\n")
    
    # Example: Store a memory
    print("═══════════════════════════════════════════════════════════")
    print("   💬 Example Conversation")
    print("═══════════════════════════════════════════════════════════\n")
    
    print("3️⃣ Storing a memory...")
    response1 = client.beta.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Remember that I prefer dark mode for all applications."
            }
        ],
        tools=[memory_tool],
        betas=["context-management-2025-06-27"],
    )
    
    # Process tool calls
    for content_block in response1.content:
        if content_block.type == "text":
            print(f"   Claude: {content_block.text}\n")
        elif content_block.type == "tool_use":
            if content_block.name == "memory":
                print(f"   🔧 Claude using memory tool: {content_block.input.get('command', 'unknown')}\n")
    
    # Example: Retrieve the memory
    print("4️⃣ Retrieving stored memory...")
    response2 = client.beta.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "What are my preferences for application themes?"
            }
        ],
        tools=[memory_tool],
        betas=["context-management-2025-06-27"],
    )
    
    for content_block in response2.content:
        if content_block.type == "text":
            print(f"   Claude: {content_block.text}\n")
        elif content_block.type == "tool_use":
            if content_block.name == "memory":
                print(f"   🔧 Claude using memory tool: {content_block.input.get('command', 'unknown')}\n")
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 Claude can now:")
    print("   - Store memories in Gaugid profiles automatically")
    print("   - Retrieve past memories across conversations")
    print("   - Build knowledge over time using persistent storage")
    print("   - Access memories even after context window resets!")


if __name__ == "__main__":
    main()
