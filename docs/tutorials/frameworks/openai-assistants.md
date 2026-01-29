# OpenAI Assistants Integration

This tutorial shows how to integrate Gaugid SDK with **OpenAI Assistants API** to build persistent, personalized AI assistants.

## Overview

We'll build a **personalized assistant** that:
- Loads user context from Gaugid profiles
- Creates persistent assistants with personalized instructions
- Maintains conversation threads
- Proposes memories learned during conversations

## Prerequisites

Install dependencies using `uv`:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies from pyproject.toml
cd docs
uv pip install -e .[openai]
```

Set environment variables:
```bash
export OPENAI_API_KEY="sk-your-key-here"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"
```

## Step 1: Load User Context

Create a function to load and format user context:

```python
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
```

## Step 2: Create Personalized Assistant

Create an assistant with personalized instructions:

```python
from openai import OpenAI

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
```

## Step 3: Complete Example

Here's the complete working example:

```python
import asyncio
import os
from openai import OpenAI
from gaugid import GaugidClient

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
            import time
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
```

## Advanced: Assistant Tools Integration

You can add tools that interact with Gaugid:

```python
from openai import OpenAI

def create_assistant_with_gaugid_tools(
    openai_client: OpenAI,
    user_context: str,
    gaugid_client: GaugidClient
) -> str:
    """Create assistant with Gaugid-integrated tools."""
    
    instructions = f"""You are a helpful AI assistant with access to user profile data.

USER PROFILE:
{user_context}

You can propose memories to the user's profile when you learn something new."""
    
    # Define custom function for proposing memories
    tools = [
        {
            "type": "function",
            "function": {
                "name": "propose_memory",
                "description": "Propose a new memory to the user's Gaugid profile",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The memory content"
                        },
                        "category": {
                            "type": "string",
                            "description": "Memory category (e.g., a2p:preferences, a2p:interests)"
                        },
                        "confidence": {
                            "type": "number",
                            "description": "Confidence level (0.0-1.0)",
                            "minimum": 0.0,
                            "maximum": 1.0
                        }
                    },
                    "required": ["content", "category"]
                }
            }
        }
    ]
    
    assistant = openai_client.beta.assistants.create(
        name="Gaugid-Integrated Assistant",
        instructions=instructions,
        model="gpt-5.2",
        tools=tools
    )
    
    return assistant.id
```

## Key Integration Points

### 1. Instructions with User Context
```python
instructions = f"""User Profile:
{user_context}
..."""
```

### 2. Thread Management
```python
# Create thread per conversation
thread = openai_client.beta.threads.create()

# Add messages to thread
openai_client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content=user_input
)
```

### 3. Memory Proposals
```python
# Propose memories after learning
await gaugid_client.propose_memory(
    user_did=user_did,
    content="...",
    category="a2p:interests.technology"
)
```

## Best Practices

1. **Create one assistant per user** or reuse with dynamic instructions
2. **Use threads** to maintain conversation history
3. **Update assistant instructions** when user context changes
4. **Handle run status** properly (queued, in_progress, completed, failed)
5. **Rate limit memory proposals** to avoid overwhelming users

## Model Versions (2026-01)

As of January 2026, recommended models:
- **GPT-5.2**: `gpt-5.2` (latest, released Dec 2025, recommended)
- **GPT-5.1**: `gpt-5.1` (alternative, released Nov 2025)
- **GPT-4o**: `gpt-4o` (previous generation, still available)

## Next Steps

- Learn about [Anthropic Claude](anthropic.md) for long context
- Check out [Google Gemini](gemini.md) for fast inference
- See [Advanced Tutorials](../advanced/multi-agent.md) for multi-agent systems

---

**Ready to try it?** Run the example and build persistent assistants with OpenAI and Gaugid!
