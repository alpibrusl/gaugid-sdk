"""
Google ADK + Gaugid Memory Service Example

This example demonstrates how to use GaugidMemoryService with Google ADK agents,
allowing agents to store and retrieve long-term memories from Gaugid profiles.

Based on: https://google.github.io/adk-docs/sessions/memory/

Requires: GOOGLE_API_KEY and GAUGID_CONNECTION_TOKEN environment variables
"""

import asyncio
import os

try:
    from gaugid.integrations.adk import GaugidMemoryService
except ImportError:
    # Fallback for examples directory structure
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from gaugid_memory_service import GaugidMemoryService

try:
    from google.adk import Agent, Runner
    from google.adk.tools.preload_memory_tool import PreloadMemoryTool
    from google.genai import types
    import google.generativeai as genai
    GOOGLE_ADK_AVAILABLE = True
except ImportError:
    GOOGLE_ADK_AVAILABLE = False
    print("⚠️  Google ADK not installed. Install with: pip install google-adk>=0.1.0")


async def create_agent_with_gaugid_memory(
    google_api_key: str,
    connection_token: str,
    app_name: str = "adk-gaugid-demo"
) -> tuple[Agent, Runner]:
    """
    Create a Google ADK agent with Gaugid memory service.
    
    This agent will:
    - Load user context from Gaugid at the start of each turn (PreloadMemoryTool)
    - Store conversation information in Gaugid after each session
    - Search Gaugid memories when needed
    """
    
    if not GOOGLE_ADK_AVAILABLE:
        raise ImportError("Google ADK is not installed")
    
    # Configure Google AI
    genai.configure(api_key=google_api_key)
    
    # Create Gaugid memory service
    memory_service = GaugidMemoryService(
        connection_token=connection_token,
        app_name=app_name,
    )
    
    # Create agent with memory tool
    # PreloadMemoryTool automatically loads relevant memories at the start of each turn
    agent = Agent(
        model="gemini-2.0-flash-exp",
        name="gaugid_memory_agent",
        instruction="""You are a helpful AI assistant with access to long-term memory via Gaugid.

You can remember past conversations and user preferences through the memory system.
The PreloadMemoryTool automatically loads relevant memories at the start of each turn.
Use this context to provide personalized responses based on past interactions.

Be helpful, personalized, and remember important details about the user.
Reference past conversations when relevant to show continuity.""",
        tools=[PreloadMemoryTool()],  # Automatically loads memory at start of each turn
        after_agent_callback=auto_save_session_callback,  # Auto-save sessions to Gaugid
    )
    
    # Create runner with memory service
    runner = Runner(
        agent=agent,
        memory_service=memory_service,
    )
    
    return agent, runner


async def auto_save_session_callback(callback_context):
    """
    Callback to automatically save session to Gaugid memory.
    
    This is called after each agent turn, allowing you to save
    the session information to Gaugid. You can also save at session
    completion instead of after each turn.
    
    Based on: https://google.github.io/adk-docs/sessions/memory/
    """
    try:
        session = callback_context._invocation_context.session
        memory_service = callback_context._invocation_context.memory_service
        
        # Save session to memory
        await memory_service.add_session_to_memory(session)
    except Exception as e:
        # Log error but don't break the agent flow
        print(f"Warning: Failed to save session to memory: {e}")


async def main():
    """Main function demonstrating ADK + Gaugid memory integration."""
    
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
    print("     🚀 Google ADK + Gaugid Memory Service")
    print("═══════════════════════════════════════════════════════════\n")
    
    try:
        # Create agent with Gaugid memory
        print("1️⃣ Creating ADK agent with Gaugid memory service...")
        agent, runner = await create_agent_with_gaugid_memory(
            google_api_key=google_api_key,
            connection_token=connection_token,
            app_name="adk-demo"
        )
        print("   ✅ Agent created with PreloadMemoryTool")
        print("   ✅ GaugidMemoryService configured\n")
        
        # Interactive conversation
        print("═══════════════════════════════════════════════════════════")
        print("   💬 Agent Ready! Type 'quit' to exit.")
        print("   The agent will remember past conversations via Gaugid.")
        print("═══════════════════════════════════════════════════════════\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == "quit":
                break
            
            if not user_input:
                continue
            
            print(f"\n🤖 Agent processing (with Gaugid memory context)...\n")
            
            try:
                # Create request
                request = types.Content(
                    parts=[types.Part(text=user_input)]
                )
                
                # Run agent (memory will be preloaded automatically)
                response = await runner.run(request)
                
                # Extract response text
                response_text = ""
                if hasattr(response, 'parts'):
                    for part in response.parts:
                        if hasattr(part, 'text'):
                            response_text += part.text
                elif hasattr(response, 'text'):
                    response_text = response.text
                else:
                    response_text = str(response)
                
                print(f"Agent: {response_text}\n")
                
                # Optionally save session to memory after each turn
                # (In production, you might do this after session completion)
                
            except Exception as e:
                print(f"   ❌ Error: {e}\n")
        
        # Save final session to memory
        print("\n2️⃣ Saving session to Gaugid memory...")
        session = runner.session_service.get_current_session()
        if session:
            await runner.memory_service.add_session_to_memory(session)
            print("   ✅ Session saved to Gaugid profile!\n")
        
    finally:
        # Cleanup
        if 'runner' in locals() and hasattr(runner, 'memory_service'):
            await runner.memory_service.close()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Session Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 The agent will remember this conversation in future sessions!")


if __name__ == "__main__":
    asyncio.run(main())
