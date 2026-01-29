# Google ADK Integration

This tutorial shows how to integrate Gaugid SDK with **Google Agent Development Kit (ADK)** to build production-ready multi-agent systems.

## Overview

We'll build a **personalized multi-agent system** that:
- Loads user context from Gaugid profiles
- Creates multiple agents with shared user context
- Coordinates agent interactions
- Proposes memories learned during agent operations

## Prerequisites

Install dependencies using `uv`:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies from pyproject.toml
cd docs
uv pip install -e .[google-adk]
```

Set environment variables:
```bash
export GOOGLE_API_KEY="your-google-api-key"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"
```

## Step 1: Load User Context

Create a function to load user context:

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

## Step 2: Create Agents with User Context

Create multiple agents that share user context:

```python
from google.adk import Agent, AgentConfig
import google.generativeai as genai

def create_agents_with_context(
    api_key: str,
    user_context: str,
    user_did: str
) -> dict[str, Agent]:
    """Create multiple agents with shared user context."""
    
    genai.configure(api_key=api_key)
    
    # Base instruction for all agents
    base_instruction = f"""You are part of a multi-agent system helping a user.

USER PROFILE (from Gaugid - use this to personalize all responses):
{user_context}

All agents should adapt to the user's preferences and expertise level."""
    
    # Research Agent
    research_agent = Agent(
        name="research_agent",
        config=AgentConfig(
            model="gemini-3-flash-exp",
            system_instruction=f"""{base_instruction}

You specialize in research and information gathering.
Focus on the user's current projects and interests.""",
            tools=["web_search", "code_interpreter"]
        )
    )
    
    # Code Agent
    code_agent = Agent(
        name="code_agent",
        config=AgentConfig(
            model="gemini-3-flash-exp",
            system_instruction=f"""{base_instruction}

You specialize in code generation and debugging.
Adapt code examples to the user's preferred tools and languages.""",
            tools=["code_interpreter"]
        )
    )
    
    # Writing Agent
    writing_agent = Agent(
        name="writing_agent",
        config=AgentConfig(
            model="gemini-3-flash-exp",
            system_instruction=f"""{base_instruction}

You specialize in writing and communication.
Match the user's communication style and preferences.""",
            tools=[]
        )
    )
    
    return {
        "research": research_agent,
        "code": code_agent,
        "writing": writing_agent
    }
```

## Step 3: Complete Example

Here's the complete working example:

```python
import asyncio
import os
from google.adk import AgentCoordinator
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
    print("     🚀 Google ADK + Gaugid: Multi-Agent System")
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
        
        # Create agents
        print("2️⃣ Creating agents with shared user context...")
        agents = create_agents_with_context(google_key, user_context, user_did)
        print(f"   ✅ Created {len(agents)} agents\n")
        
        # Create coordinator
        coordinator = AgentCoordinator(agents=list(agents.values()))
        
        # Interactive conversation
        print("═══════════════════════════════════════════════════════════")
        print("   💬 Multi-agent system ready! Type 'quit' to exit.")
        print("   Agents will coordinate based on your request.")
        print("═══════════════════════════════════════════════════════════\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == "quit":
                break
            
            if user_input.lower() == "propose":
                print("\n📝 Proposing a learned memory...")
                await gaugid_client.propose_memory(
                    user_did=user_did,
                    content="User is exploring Google ADK for multi-agent systems",
                    category="a2p:interests.technology",
                    confidence=0.75
                )
                print("   ✅ Memory proposed!\n")
                continue
            
            if not user_input:
                continue
            
            # Route to appropriate agent(s)
            response = await coordinator.route_and_execute(
                user_input=user_input,
                user_context=user_context
            )
            
            print(f"\n🤖 System: {response}\n")
        
        # Propose final learning
        print("\n3️⃣ Proposing learnings from interaction...")
        await gaugid_client.propose_memory(
            user_did=user_did,
            content="Used multi-agent system with Google ADK",
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

## Advanced: Agent Coordination

Implement intelligent agent routing:

```python
from google.adk import AgentCoordinator

class PersonalizedCoordinator(AgentCoordinator):
    """Coordinator that uses user context for routing."""
    
    def __init__(self, agents: list[Agent], user_context: str):
        super().__init__(agents)
        self.user_context = user_context
    
    async def route(self, user_input: str) -> list[Agent]:
        """Route user input to appropriate agents based on context."""
        # Analyze user input and context to determine which agents to use
        # This is a simplified example
        if "code" in user_input.lower() or "programming" in user_input.lower():
            return [self.agents["code"]]
        elif "research" in user_input.lower() or "find" in user_input.lower():
            return [self.agents["research"]]
        elif "write" in user_input.lower() or "draft" in user_input.lower():
            return [self.agents["writing"]]
        else:
            # Use all agents for complex queries
            return list(self.agents.values())
```

## Key Integration Points

### 1. Shared User Context
```python
# All agents share the same user context
base_instruction = f"""User Profile: {user_context}"""
```

### 2. Agent Specialization
```python
# Each agent has specialized instructions but shares user context
research_agent = Agent(
    system_instruction=f"""{base_instruction}
    You specialize in research..."""
)
```

### 3. Memory Proposals
```python
# Propose memories after agent interactions
await gaugid_client.propose_memory(
    user_did=user_did,
    content="...",
    category="a2p:interests.technology"
)
```

## Best Practices

1. **Share user context** across all agents
2. **Specialize agents** for different tasks
3. **Coordinate agent interactions** intelligently
4. **Propose memories** from agent learnings
5. **Handle errors** gracefully across agents

## Model Versions (2026-01)

As of January 2026, recommended models:
- **Gemini 3 Flash**: `gemini-3-flash-exp` (latest, released Dec 2025, fast, multimodal)
- **Gemini 3 Pro**: `gemini-3-pro` (latest, released Nov 2025, high quality)
- **Gemini 2.0 Flash**: `gemini-2.0-flash-exp` (previous generation, still available)

## Next Steps

- Learn about [CrewAI](crewai.md) for research teams
- Check out [Agno](agno.md) for enterprise orchestration
- See [Advanced Tutorials](../advanced/multi-agent.md) for complex workflows

---

**Ready to try it?** Run the example and build production multi-agent systems with Google ADK and Gaugid!
