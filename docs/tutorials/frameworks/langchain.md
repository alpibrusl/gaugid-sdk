# LangChain Integration

This tutorial shows how to integrate Gaugid SDK with **LangChain** to build a personalized chatbot that remembers user preferences and context.

## Overview

We'll build a **personalized chatbot** that:
- Loads user context from Gaugid profiles
- Personalizes responses using LangChain chains
- Proposes memories learned during conversations
- Maintains conversation history

## Prerequisites

Install dependencies using `uv`:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies from pyproject.toml
cd docs
uv pip install -e .[langchain]
```

Set environment variables:
```bash
export OPENAI_API_KEY="sk-your-key-here"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"
```

## Step 1: Setup User Profile

First, create a user profile with preferences:

```python
import asyncio
from gaugid import GaugidClient

async def setup_user_profile(client: GaugidClient) -> str:
    """Create a user profile with preferences."""
    # In production, this would be done by the user through the Gaugid dashboard
    # For this example, we'll assume the profile already exists
    user_did = "did:a2p:user:gaugid:demo"
    
    # The profile should have memories like:
    # - Professional background
    # - Communication preferences
    # - Current projects
    # - Interests
    
    return user_did
```

## Step 2: Create Gaugid Memory Class

Create a LangChain-compatible memory class that integrates with Gaugid:

```python
from typing import List
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import BaseMessage
from gaugid import GaugidClient

class GaugidMemory:
    """LangChain-compatible memory that integrates with Gaugid profiles."""
    
    def __init__(self, client: GaugidClient, user_did: str, agent_did: str):
        self.client = client
        self.user_did = user_did
        self.agent_did = agent_did
        self.conversation_memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        self.user_context = ""
    
    async def load_user_context(self) -> str:
        """Load user context from Gaugid profile."""
        profile = await self.client.get_profile(
            user_did=self.user_did,
            scopes=["a2p:preferences", "a2p:professional", "a2p:context", "a2p:interests"]
        )
        
        # Extract memories and format as context
        memories = profile.get("memories", {}).get("episodic", [])
        context_parts = []
        
        for memory in memories:
            category = memory.get("category", "general")
            content = memory.get("content", "")
            context_parts.append(f"- [{category}] {content}")
        
        self.user_context = "\n".join(context_parts)
        return self.user_context
    
    async def propose_memory(
        self, 
        content: str, 
        category: str, 
        confidence: float = 0.7
    ) -> None:
        """Propose a learned memory back to the user's profile."""
        await self.client.propose_memory(
            user_did=self.user_did,
            content=content,
            category=category,
            confidence=confidence,
            context="Learned during LangChain conversation"
        )
    
    def add_user_message(self, message: str) -> None:
        """Add a user message to conversation memory."""
        self.conversation_memory.chat_memory.add_user_message(message)
    
    def add_ai_message(self, message: str) -> None:
        """Add an AI message to conversation memory."""
        self.conversation_memory.chat_memory.add_ai_message(message)
    
    def get_chat_history(self) -> List[BaseMessage]:
        """Get the chat history."""
        return self.conversation_memory.chat_memory.messages
```

## Step 3: Create Personalized Chain

Create a LangChain chain with personalized system prompt:

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

def create_personalized_chain(llm: ChatOpenAI, user_context: str):
    """Create a LangChain chain with personalized system prompt."""
    
    system_template = f"""You are a helpful AI assistant specializing in software development.

## USER PROFILE (from Gaugid)
{user_context}

## Guidelines
- Adapt your communication style to match user preferences
- Reference their expertise level when explaining concepts
- Consider their current projects and learning goals
- Be aware of their tool preferences
- Personalize examples and recommendations

Be helpful, technical, and precise. Adapt to the user's expertise level."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    
    chain = prompt | llm | StrOutputParser()
    return chain
```

## Step 4: Complete Example

Here's the complete working example:

```python
import asyncio
import os
from langchain_openai import ChatOpenAI
from gaugid import GaugidClient

# Import the classes we defined above
from gaugid_memory import GaugidMemory
from chain import create_personalized_chain

async def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 LangChain + Gaugid: Personalized Chatbot")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Initialize Gaugid client
    client = GaugidClient(connection_token=connection_token)
    user_did = "did:a2p:user:gaugid:demo"
    
    try:
        # Create memory with Gaugid integration
        print("1️⃣ Loading user context from Gaugid...")
        memory = GaugidMemory(
            client=client,
            user_did=user_did,
            agent_did="did:a2p:agent:local:langchain-assistant"
        )
        user_context = await memory.load_user_context()
        print("   ✅ User context loaded:")
        for line in user_context.split("\n")[:5]:
            print(f"      {line}")
        print()
        
        # Create personalized chain
        print("2️⃣ Creating personalized LangChain chain...")
        llm = ChatOpenAI(model="gpt-5.2", temperature=0.7)  # Latest GPT-5.2 as of 2026-01
        chain = create_personalized_chain(llm, user_context)
        print("   ✅ Chain ready\n")
        
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
                await memory.propose_memory(
                    content="User is exploring LangChain for AI applications",
                    category="a2p:interests.technology",
                    confidence=0.75
                )
                print("   ✅ Memory proposed!\n")
                continue
            
            if not user_input:
                continue
            
            # Add to memory and get response
            memory.add_user_message(user_input)
            
            response = chain.invoke({
                "input": user_input,
                "chat_history": memory.get_chat_history()[:-1],
            })
            
            memory.add_ai_message(response)
            print(f"\n🤖 Assistant: {response}\n")
        
        # Propose final learning
        print("\n3️⃣ Proposing learnings from conversation...")
        await memory.propose_memory(
            content="User had a productive conversation about LangChain integration",
            category="a2p:context.interactions",
            confidence=0.7
        )
        print("   ✅ Memory proposed!\n")
        
    finally:
        await client.close()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Session Complete!")
    print("═══════════════════════════════════════════════════════════\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Integration Points

### 1. Context Loading
```python
# Load user context once at startup
user_context = await memory.load_user_context()
```

### 2. System Prompt Injection
```python
# Inject context into system prompt
system_template = f"""User Profile:
{user_context}
..."""
```

### 3. Memory Proposals
```python
# Propose memories after learning something
await memory.propose_memory(
    content="User prefers Python over JavaScript",
    category="a2p:preferences.tools",
    confidence=0.8
)
```

## Advanced: Custom Memory Backend

For production, you might want to persist conversation history in Gaugid:

```python
class PersistentGaugidMemory(GaugidMemory):
    """Memory that persists conversation history to Gaugid."""
    
    async def save_conversation(self) -> None:
        """Save conversation history as a memory proposal."""
        history = self.get_chat_history()
        summary = self._summarize_conversation(history)
        
        await self.propose_memory(
            content=summary,
            category="a2p:context.conversations",
            confidence=0.6
        )
    
    def _summarize_conversation(self, history: List[BaseMessage]) -> str:
        """Summarize conversation history."""
        # Use LLM to summarize conversation
        # This is a simplified version
        return f"Conversation with {len(history)} messages"
```

## Best Practices

1. **Load context once** at startup, not on every message
2. **Cache user profiles** to reduce API calls
3. **Batch memory proposals** instead of proposing after every message
4. **Handle errors gracefully** when profile access is denied
5. **Respect consent policies** by only requesting necessary scopes

## Next Steps

- Learn about [LangGraph integration](langgraph.md) for state machines
- Check out [OpenAI Assistants](openai-assistants.md) for persistent assistants
- See [Advanced Tutorials](../advanced/multi-agent.md) for multi-agent systems

---

**Ready to try it?** Run the example and start building personalized chatbots with LangChain and Gaugid!
