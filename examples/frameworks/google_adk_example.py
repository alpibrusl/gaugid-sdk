"""
Google ADK + Gaugid: Personalized Multi-Agent System

This example demonstrates how to integrate Gaugid SDK with Google Agent Development Kit (ADK)
to build production-ready multi-agent systems with personalized user context.

Requires: GOOGLE_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
"""

import asyncio
import os
from typing import Dict, List
from gaugid import GaugidClient

# Google ADK imports (version 1.0+)
# Note: Google ADK API structure may vary. This example supports both ADK and direct Gemini API.
try:
    import google.generativeai as genai
    # Try importing ADK - structure may vary by version
    try:
        from google.adk import Agent, AgentConfig, AgentCoordinator
        GOOGLE_ADK_AVAILABLE = True
        USE_ADK = True
    except ImportError:
        # Fallback: Use Gemini API directly with multi-agent pattern
        GOOGLE_ADK_AVAILABLE = True
        USE_ADK = False
        print("⚠️  Google ADK not found, using Gemini API directly for multi-agent pattern")
except ImportError:
    GOOGLE_ADK_AVAILABLE = False
    USE_ADK = False
    print("⚠️  Google Generative AI not installed. Install with: pip install google-generativeai>=0.8.0")


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


def create_personalized_agents(
    api_key: str,
    user_context: str,
    client: GaugidClient
) -> Dict[str, any]:
    """Create multiple agents with personalized user context."""
    
    genai.configure(api_key=api_key)
    
    # Base system prompt with user context
    base_system_prompt = f"""You are part of a multi-agent system that helps users with various tasks.

## USER PROFILE (from Gaugid)
{user_context}

## Guidelines
- Adapt your communication style to match user preferences
- Reference their expertise level when explaining concepts
- Consider their current projects and learning goals
- Be aware of their tool preferences
- Personalize examples and recommendations

Be helpful, technical, and precise. Adapt to the user's expertise level."""
    
    if USE_ADK:
        # Use Google ADK Agent structure
        from google.adk import Agent, AgentConfig
        
        research_agent = Agent(
            name="research_agent",
            config=AgentConfig(
                model="gemini-2.0-flash-exp",
                system_instruction=f"""{base_system_prompt}

You specialize in research and information gathering.
Focus on the user's current projects and interests.""",
                tools=["web_search"]
            )
        )
        
        writing_agent = Agent(
            name="writing_agent",
            config=AgentConfig(
                model="gemini-2.0-flash-exp",
                system_instruction=f"""{base_system_prompt}

You specialize in writing and communication.
Match the user's communication style and preferences.""",
                tools=[]
            )
        )
        
        analysis_agent = Agent(
            name="analysis_agent",
            config=AgentConfig(
                model="gemini-2.0-flash-exp",
                system_instruction=f"""{base_system_prompt}

You specialize in data analysis and insights.
Consider the user's professional background when providing analysis.""",
                tools=[]
            )
        )
        
        return {
            "research": {"name": "Research Agent", "agent": research_agent},
            "writing": {"name": "Writing Agent", "agent": writing_agent},
            "analysis": {"name": "Analysis Agent", "agent": analysis_agent},
        }
    else:
        # Fallback: Use Gemini API directly
        research_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=f"""{base_system_prompt}

You are a Research Specialist. Your role is to conduct thorough research on user topics.
You understand the user's interests, expertise level, and preferences. Use this knowledge
to tailor your research approach and recommendations.""",
        )
        
        writing_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=f"""{base_system_prompt}

You are a Content Writer. Your role is to create personalized content based on research.
You adapt your writing style to match the user's preferences and expertise level.
You use research findings to create relevant, personalized content.""",
        )
        
        analysis_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=f"""{base_system_prompt}

You are a Data Analyst. Your role is to analyze information and provide personalized insights.
You consider the user's professional background and interests when providing analysis.
You present findings in a way that matches their expertise level.""",
        )
        
        return {
            "research": {"name": "Research Agent", "model": research_model},
            "writing": {"name": "Writing Agent", "model": writing_model},
            "analysis": {"name": "Analysis Agent", "model": analysis_model},
        }


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
        context="Learned during Google ADK agent interaction"
    )


async def main():
    """Main function demonstrating Google ADK + Gaugid integration."""
    
    if not GOOGLE_ADK_AVAILABLE:
        print("❌ Google ADK is not installed.")
        print("   Install with: pip install google-adk>=0.1.0")
        return
    
    # Check for API keys
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🚀 Google ADK + Gaugid: Multi-Agent System")
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
        
        # Create personalized agents
        print("2️⃣ Creating personalized agents with user context...")
        agents = create_personalized_agents(google_api_key, user_context, client)
        print(f"   ✅ Created {len(agents)} agents:")
        for name, agent_info in agents.items():
            print(f"      - {agent_info['name']}")
        print()
        
        # Interactive agent interaction
        print("═══════════════════════════════════════════════════════════")
        print("   💬 Agent System Ready! Type 'quit' to exit.")
        print("   Available agents: research, writing, analysis")
        print("═══════════════════════════════════════════════════════════\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == "quit":
                break
            
            if not user_input:
                continue
            
            # Determine which agent to use based on input
            if any(word in user_input.lower() for word in ["research", "find", "search", "look up"]):
                agent_info = agents["research"]
            elif any(word in user_input.lower() for word in ["write", "create", "draft", "content"]):
                agent_info = agents["writing"]
            elif any(word in user_input.lower() for word in ["analyze", "insight", "summary", "conclusion"]):
                agent_info = agents["analysis"]
            else:
                # Default to research agent
                agent_info = agents["research"]
            
            agent_name = agent_info["name"]
            
            print(f"\n🤖 {agent_name} is processing...")
            
            try:
                # Get response from agent (ADK or direct Gemini)
                if USE_ADK and "agent" in agent_info:
                    # Use ADK agent
                    response = await agent_info["agent"].process(user_input)
                    response_text = str(response)
                elif "model" in agent_info:
                    # Use direct Gemini model
                    response = agent_info["model"].generate_content(user_input)
                    response_text = response.text
                else:
                    response_text = "Error: Agent not properly configured"
                
                print(f"\n{agent_name}: {response_text}\n")
                
                # Propose memory about the interaction
                await propose_learned_memory(
                    client,
                    f"User interacted with {agent_name}: {user_input[:100]}",
                    category="a2p:context.interactions",
                    memory_type="episodic",
                    confidence=0.7
                )
                
            except Exception as e:
                print(f"   ❌ Error: {e}\n")
        
        # Propose final learning
        print("\n4️⃣ Proposing learnings from session...")
        await propose_learned_memory(
            client,
            "User completed a session with Google ADK multi-agent system",
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
