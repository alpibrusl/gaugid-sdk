# CrewAI Integration

This tutorial shows how to integrate Gaugid SDK with **CrewAI** to build personalized multi-agent research teams.

## Overview

We'll build a **personalized research crew** that:
- Loads user context from Gaugid profiles
- Creates specialized agents with personalized backstories
- Coordinates agent collaboration
- Proposes memories learned during research

## Prerequisites

Install dependencies using `uv`:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies from pyproject.toml
cd docs
uv pip install -e .[crewai]
```

Set environment variables:
```bash
export OPENAI_API_KEY="sk-your-key-here"  # or ANTHROPIC_API_KEY
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

## Step 2: Create Personalized Crew

Create a crew with agents that have personalized backstories:

```python
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool

def create_personalized_crew(user_context: str, user_did: str) -> Crew:
    """Create a CrewAI crew with personalized agents."""
    
    # Research tool
    search_tool = SerperDevTool()
    
    # Researcher Agent
    researcher = Agent(
        role="Research Specialist",
        goal=f"""Conduct thorough research on topics relevant to the user.
        User context: {user_context}
        Adapt research depth to user's expertise level.""",
        backstory=f"""You are an expert researcher who understands the user's background:
        {user_context}
        You tailor your research approach to match their expertise and interests.""",
        tools=[search_tool],
        verbose=True
    )
    
    # Writer Agent
    writer = Agent(
        role="Technical Writer",
        goal=f"""Write clear, technical content that matches the user's communication style.
        User context: {user_context}
        Adapt writing style to user preferences.""",
        backstory=f"""You are a technical writer who knows the user's preferences:
        {user_context}
        You write in a style that matches their expertise level and communication preferences.""",
        tools=[],
        verbose=True
    )
    
    # Reviewer Agent
    reviewer = Agent(
        role="Quality Reviewer",
        goal=f"""Review and improve content based on user's standards.
        User context: {user_context}
        Ensure content meets user's quality expectations.""",
        backstory=f"""You are a quality reviewer familiar with the user's standards:
        {user_context}
        You ensure all content meets their expectations and preferences.""",
        tools=[],
        verbose=True
    )
    
    return Crew(
        agents=[researcher, writer, reviewer],
        tasks=[],  # Tasks will be added dynamically
        verbose=True
    )
```

## Step 3: Complete Example

Here's the complete working example:

```python
import asyncio
import os
from crewai import Task
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
    print("     🚀 CrewAI + Gaugid: Personalized Research Crew")
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
        
        # Create personalized crew
        print("2️⃣ Creating personalized research crew...")
        crew = create_personalized_crew(user_context, user_did)
        print("   ✅ Crew ready\n")
        
        # Interactive research loop
        print("═══════════════════════════════════════════════════════════")
        print("   🔍 Research crew ready! Type 'quit' to exit.")
        print("   Ask a research question and the crew will work together.")
        print("═══════════════════════════════════════════════════════════\n")
        
        while True:
            research_question = input("Research question: ").strip()
            
            if research_question.lower() == "quit":
                break
            
            if research_question.lower() == "propose":
                print("\n📝 Proposing a learned memory...")
                await gaugid_client.propose_memory(
                    user_did=user_did,
                    content="User is exploring CrewAI for research automation",
                    category="a2p:interests.technology",
                    confidence=0.75
                )
                print("   ✅ Memory proposed!\n")
                continue
            
            if not research_question:
                continue
            
            # Create research task
            research_task = Task(
                description=f"""Research the following question: {research_question}
                
                Consider the user's background and interests:
                {user_context}
                
                Tailor the research depth and approach accordingly.""",
                agent=crew.agents[0]  # Researcher
            )
            
            # Create writing task
            writing_task = Task(
                description="""Write a comprehensive summary of the research findings.
                Adapt the writing style to match user preferences.""",
                agent=crew.agents[1],  # Writer
                context=[research_task]
            )
            
            # Create review task
            review_task = Task(
                description="""Review and improve the written summary.
                Ensure it meets user's quality standards.""",
                agent=crew.agents[2],  # Reviewer
                context=[writing_task]
            )
            
            # Update crew with tasks
            crew.tasks = [research_task, writing_task, review_task]
            
            # Execute crew
            print("\n🔍 Crew working on research...\n")
            result = crew.kickoff()
            
            print(f"\n📄 Research Summary:\n{result}\n")
        
        # Propose final learning
        print("\n3️⃣ Proposing learnings from research sessions...")
        await gaugid_client.propose_memory(
            user_did=user_did,
            content="Used CrewAI for research automation",
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

## Key Integration Points

### 1. Personalized Backstories
```python
researcher = Agent(
    backstory=f"""User context: {user_context}
    You adapt to their expertise level..."""
)
```

### 2. Task Context
```python
task = Task(
    description=f"""Consider user background: {user_context}...""",
    agent=researcher
)
```

### 3. Memory Proposals
```python
await gaugid_client.propose_memory(
    user_did=user_did,
    content="...",
    category="a2p:interests.technology"
)
```

## Best Practices

1. **Personalize agent backstories** with user context
2. **Adapt task descriptions** to user expertise
3. **Coordinate agent collaboration** effectively
4. **Propose memories** from research findings
5. **Handle errors** gracefully across agents

## Next Steps

- Learn about [Agno](agno.md) for enterprise orchestration
- Check out [Google ADK](google-adk.md) for production systems
- See [Advanced Tutorials](../advanced/multi-agent.md) for complex workflows

---

**Ready to try it?** Run the example and build personalized research crews with CrewAI and Gaugid!
