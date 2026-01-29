"""
CrewAI + Gaugid: Personalized Multi-Agent Research Team

This example demonstrates how to integrate Gaugid SDK with CrewAI to build
personalized multi-agent research teams that learn from user interactions.

Requires: OPENAI_API_KEY (or ANTHROPIC_API_KEY) and GAUGID_CONNECTION_TOKEN environment variables
"""

import asyncio
import os
from typing import List
from gaugid import GaugidClient

# CrewAI imports
try:
    from crewai import Agent, Task, Crew, Process
    from crewai_tools import SerperDevTool, WebsiteSearchTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    print("⚠️  CrewAI not installed. Install with: pip install crewai>=0.80.0 crewai-tools>=0.15.0")


async def load_user_context(client: GaugidClient) -> str:
    """Load user context from Gaugid profile using connection token mode."""
    # Connection token mode: No DID needed - profile resolved from token
    profile = await client.get_profile(
        scopes=["a2p:preferences", "a2p:professional", "a2p:context", "a2p:interests"]
    )
    
    # Extract memories from different memory types
    memories = profile.get("memories", {})
    episodic = memories.get("episodic", [])
    semantic = memories.get("semantic", [])
    procedural = memories.get("procedural", [])
    
    context_parts = []
    
    # Add episodic memories
    for memory in episodic:
        category = memory.get("category", "general")
        content = memory.get("content", "")
        context_parts.append(f"- [Episodic: {category}] {content}")
    
    # Add semantic memories
    for memory in semantic:
        category = memory.get("category", "general")
        content = memory.get("content", "")
        context_parts.append(f"- [Semantic: {category}] {content}")
    
    # Add procedural memories
    for memory in procedural:
        category = memory.get("category", "general")
        content = memory.get("content", "")
        context_parts.append(f"- [Procedural: {category}] {content}")
    
    # Add preferences
    preferences = profile.get("common", {}).get("preferences", {})
    if preferences:
        context_parts.append(f"\n## Preferences")
        for key, value in preferences.items():
            context_parts.append(f"- {key}: {value}")
    
    return "\n".join(context_parts) if context_parts else "No user context available."


def create_personalized_crew(user_context: str, client: GaugidClient) -> Crew:
    """Create a CrewAI crew with personalized agents based on user context."""
    
    # Research Agent
    researcher = Agent(
        role="Research Specialist",
        goal="Conduct thorough research on topics of interest to the user",
        backstory=f"""You are a research specialist with deep knowledge of the user's interests and expertise.

## USER PROFILE (from Gaugid)
{user_context}

You understand the user's professional background, interests, and learning goals.
Use this knowledge to tailor your research approach and find relevant information.""",
        verbose=True,
        allow_delegation=False,
        tools=[SerperDevTool(), WebsiteSearchTool()],
    )
    
    # Writer Agent
    writer = Agent(
        role="Content Writer",
        goal="Create personalized, engaging content based on research findings",
        backstory=f"""You are a skilled content writer who creates personalized content.

## USER PROFILE (from Gaugid)
{user_context}

You adapt your writing style to match the user's preferences and expertise level.
You use research findings to create relevant, personalized content that resonates with the user.""",
        verbose=True,
        allow_delegation=False,
    )
    
    # Analyst Agent
    analyst = Agent(
        role="Data Analyst",
        goal="Analyze information and provide personalized insights",
        backstory=f"""You are a data analyst who provides personalized insights.

## USER PROFILE (from Gaugid)
{user_context}

You consider the user's professional background and interests when providing analysis.
You present findings in a way that matches their expertise level and learning style.""",
        verbose=True,
        allow_delegation=False,
    )
    
    # Create tasks
    research_task = Task(
        description="Research the topic provided by the user, considering their interests and expertise level",
        agent=researcher,
        expected_output="A comprehensive research report with key findings and sources",
    )
    
    writing_task = Task(
        description="Create personalized content based on the research findings, adapted to the user's preferences",
        agent=writer,
        expected_output="Well-written, personalized content that matches the user's style and expertise level",
    )
    
    analysis_task = Task(
        description="Analyze the research and content to provide personalized insights and recommendations",
        agent=analyst,
        expected_output="Actionable insights and recommendations tailored to the user's needs",
    )
    
    # Create crew
    crew = Crew(
        agents=[researcher, writer, analyst],
        tasks=[research_task, writing_task, analysis_task],
        process=Process.sequential,
        verbose=True,
    )
    
    return crew


async def propose_learned_memory(
    client: GaugidClient,
    content: str,
    category: str = "a2p:context.interactions",
    memory_type: str = "episodic",
    confidence: float = 0.8
) -> None:
    """Propose a learned memory to the user's profile."""
    await client.propose_memory(
        content=content,
        category=category,
        memory_type=memory_type,
        confidence=confidence,
        context="Learned during CrewAI research session"
    )


async def main():
    """Main function demonstrating CrewAI + Gaugid integration."""
    
    if not CREWAI_AVAILABLE:
        print("❌ CrewAI is not installed.")
        print("   Install with: pip install crewai>=0.80.0 crewai-tools>=0.15.0")
        return
    
    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_key and not anthropic_key:
        print("❌ Error: OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable must be set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    # Check for Serper API key (for search tool)
    serper_key = os.getenv("SERPER_API_KEY")
    if not serper_key:
        print("⚠️  Warning: SERPER_API_KEY not set. Search functionality will be limited.")
        print("   Get a free key at: https://serper.dev")
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 CrewAI + Gaugid: Personalized Research Crew")
    print("═══════════════════════════════════════════════════════════\n")
    
    # Initialize Gaugid client
    client = GaugidClient(connection_token=connection_token)
    
    try:
        # Load user context
        print("1️⃣ Loading user context from Gaugid...")
        user_context = await load_user_context(client)
        print("   ✅ User context loaded:")
        for line in user_context.split("\n")[:8]:
            if line.strip():
                print(f"      {line}")
        print()
        
        # Create personalized crew
        print("2️⃣ Creating personalized research crew...")
        crew = create_personalized_crew(user_context, client)
        print("   ✅ Crew ready with 3 specialized agents:")
        print("      - Research Specialist")
        print("      - Content Writer")
        print("      - Data Analyst")
        print()
        
        # Interactive research sessions
        print("═══════════════════════════════════════════════════════════")
        print("   💬 Research Crew Ready! Type 'quit' to exit.")
        print("   The crew will research, write, and analyze for you.")
        print("═══════════════════════════════════════════════════════════\n")
        
        while True:
            user_input = input("Research topic: ").strip()
            
            if user_input.lower() == "quit":
                break
            
            if not user_input:
                continue
            
            print(f"\n🔍 Crew is working on: '{user_input}'...")
            print("   (This may take a moment)\n")
            
            try:
                # Execute crew
                result = crew.kickoff(inputs={"topic": user_input})
                
                print("\n" + "="*60)
                print("📊 CREW RESULTS")
                print("="*60)
                print(result)
                print("="*60 + "\n")
                
                # Propose memory about the research session
                await propose_learned_memory(
                    client,
                    f"User requested research on: {user_input}",
                    category="a2p:interests.research",
                    memory_type="episodic",
                    confidence=0.8
                )
                
                # Extract key learnings and propose as semantic memory
                if "key findings" in str(result).lower() or "insights" in str(result).lower():
                    await propose_learned_memory(
                        client,
                        f"Research session completed on topic: {user_input[:100]}",
                        category="a2p:context.interactions",
                        memory_type="semantic",
                        confidence=0.7
                    )
                
                print("✅ Memory proposed to user profile!\n")
                
            except Exception as e:
                print(f"   ❌ Error: {e}\n")
        
        # Propose final learning
        print("\n3️⃣ Proposing learnings from session...")
        await propose_learned_memory(
            client,
            "User completed a research session with CrewAI multi-agent team",
            category="a2p:context.interactions",
            memory_type="episodic",
            confidence=0.8
        )
        print("   ✅ Memory proposed!\n")
        
    finally:
        await client.close()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Session Complete!")
    print("═══════════════════════════════════════════════════════════\n")


if __name__ == "__main__":
    asyncio.run(main())
