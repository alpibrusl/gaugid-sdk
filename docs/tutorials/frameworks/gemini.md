# Google Gemini Integration

This tutorial shows how to integrate Gaugid SDK with **Google Gemini** to build fast, personalized chatbots with multimodal support.

## Overview

We'll build a **personalized chatbot** that:
- Loads user context from Gaugid profiles
- Uses Gemini's fast inference for responsive conversations
- Supports multimodal inputs (text, images)
- Proposes memories learned during conversations

## Prerequisites

Install dependencies using `uv`:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies from pyproject.toml
cd docs
uv pip install -e .[gemini]
```

Set environment variables:
```bash
export GOOGLE_API_KEY="your-google-api-key"
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

## Step 2: Configure Gemini with User Context

Create a Gemini model with personalized system instruction:

```python
import google.generativeai as genai

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
```

## Step 3: Complete Example

Here's the complete working example:

```python
import asyncio
import os
import google.generativeai as genai
from gaugid import GaugidClient

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
```

## Advanced: Multimodal Support

Gemini supports images and other media:

```python
import google.generativeai as genai
from pathlib import Path

async def chat_with_image(
    model: genai.GenerativeModel,
    text: str,
    image_path: str
) -> str:
    """Chat with Gemini using text and image."""
    
    image_data = Path(image_path).read_bytes()
    
    response = model.generate_content(
        [text, {"mime_type": "image/jpeg", "data": image_data}]
    )
    
    return response.text
```

## Advanced: Function Calling

Use function calling to propose memories:

```python
import google.generativeai as genai

def create_model_with_functions(api_key: str, user_context: str):
    """Create model with function calling for memory proposals."""
    
    genai.configure(api_key=api_key)
    
    # Define function for proposing memories
    propose_memory_func = genai.protos.FunctionDeclaration(
        name="propose_memory",
        description="Propose a new memory to the user's Gaugid profile",
        parameters={
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "category": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
            },
            "required": ["content", "category"]
        }
    )
    
    tools = [genai.protos.Tool(function_declarations=[propose_memory_func])]
    
    model = genai.GenerativeModel(
        model_name="gemini-3-flash-exp",
        system_instruction=f"User Profile: {user_context}",
        tools=tools
    )
    
    return model
```

## Key Integration Points

### 1. System Instruction
```python
    model = genai.GenerativeModel(
        model_name="gemini-3-flash-exp",
    system_instruction=f"User Profile: {user_context}"
)
```

### 2. Chat History
```python
# Start chat with history
chat = model.start_chat(history=[])

# Send messages
response = chat.send_message("Hello")
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
- **Gemini 3 Flash**: `gemini-3-flash-exp` (latest, released Dec 2025, fast, multimodal)
- **Gemini 3 Pro**: `gemini-3-pro` (latest, released Nov 2025, high quality)
- **Gemini 2.0 Flash**: `gemini-2.0-flash-exp` (previous generation, still available)

## Context Window Sizes

- **Gemini 3 Flash**: 2M tokens
- **Gemini 3 Pro**: 2M tokens
- **Gemini 2.0 Flash**: 1M tokens (previous generation)

## Best Practices

1. **Use system instructions** for user context
2. **Leverage chat history** for conversation continuity
3. **Use appropriate models** (Flash for speed, Pro for quality)
4. **Handle multimodal inputs** when relevant
5. **Stream responses** for better UX

## Next Steps

- Learn about [Google ADK](google-adk.md) for production multi-agent systems
- Check out [LangGraph](langgraph.md) for state machines
- See [Advanced Tutorials](../advanced/multi-agent.md) for multi-agent systems

---

**Ready to try it?** Run the example and build fast, personalized chatbots with Gemini and Gaugid!
