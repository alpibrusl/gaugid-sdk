# Anthropic Claude Integration

This tutorial shows how to integrate Gaugid SDK with **Anthropic Claude** to build personalized chatbots with long context windows.

## Overview

We'll build a **personalized chatbot** that:
- Loads user context from Gaugid profiles
- Uses Claude's long context window for detailed personalization
- Maintains conversation history
- Proposes memories learned during conversations

## Prerequisites

Install dependencies using `uv`:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies from pyproject.toml
cd docs
uv pip install -e .[anthropic]
```

Set environment variables:
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"
```

## Step 1: Load User Context

Create a function to load and format user context:

```python
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
```

## Step 2: Create Personalized Chat Function

Create a function that uses Claude with user context:

```python
from anthropic import Anthropic
from anthropic.types import MessageParam

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
```

## Step 3: Complete Example

Here's the complete working example:

```python
import asyncio
import os
from anthropic import Anthropic
from anthropic.types import MessageParam
from gaugid import GaugidClient

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
```

## Advanced: Streaming Responses

For better UX, use streaming:

```python
from anthropic import Anthropic

async def chat_with_claude_streaming(
    anthropic_client: Anthropic,
    user_context: str,
    messages: list[MessageParam],
    model: str = "claude-4-5"
) -> str:
    """Chat with Claude using streaming."""
    
    system_prompt = f"""User Profile: {user_context}"""
    
    with anthropic_client.messages.stream(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=messages
    ) as stream:
        full_response = ""
        for text in stream.text_stream:
            print(text, end="", flush=True)
            full_response += text
        print()  # New line after stream
        return full_response
```

## Key Integration Points

### 1. System Prompt
```python
system_prompt = f"""User Profile:
{user_context}
..."""
```

### 2. Message History
```python
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"},
    # ...
]
```

### 3. Memory Proposals
```python
await gaugid_client.propose_memory(
    user_did=user_did,
    content="...",
    category="a2p:interests.technology"
)
```

## Model Versions (2026-01)

As of January 2026, recommended models:
- **Claude 4.5**: `claude-4-5` (latest, recommended)
- **Claude 4 Sonnet**: `claude-sonnet-4` (alternative)
- **Claude 4 Haiku**: `claude-haiku-4` (fast, cost-effective)

## Context Window Sizes

- **Claude 4.5**: 200K tokens
- **Claude 4 Sonnet**: 200K tokens
- **Claude 4 Haiku**: 200K tokens

This allows you to include extensive user context and conversation history.

## Best Practices

1. **Use system prompts** for user context (more efficient than messages)
2. **Stream responses** for better UX
3. **Manage message history** to stay within context limits
4. **Use appropriate models** based on needs (Sonnet for quality, Haiku for speed)
5. **Handle rate limits** gracefully

## Next Steps

- Learn about [Google Gemini](gemini.md) for fast inference
- Check out [LangGraph](langgraph.md) for state machines
- See [Advanced Tutorials](../advanced/multi-agent.md) for multi-agent systems

---

**Ready to try it?** Run the example and build personalized chatbots with Claude and Gaugid!
