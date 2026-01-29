"""
Travel Agency Use Case: Personalized Travel Planning with Gaugid

This example demonstrates a travel agency AI assistant that:
- Remembers user travel preferences (window seats, hotel preferences, dietary restrictions)
- Learns from past trips (favorite destinations, travel patterns)
- Personalizes recommendations based on user profile
- Stores travel memories for future reference

Uses: Google ADK + Gemini (Vertex AI) + Gaugid Memory Service

Requires:
- GOOGLE_API_KEY or VERTEX_AI credentials
- GAUGID_CONNECTION_TOKEN
- pip install gaugid[adk] google-generativeai
"""

import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime

try:
    from google.adk import Agent, Runner
    from google.adk.tools.preload_memory_tool import PreloadMemoryTool
    from google.genai import types
    import google.generativeai as genai
    from gaugid.integrations.adk import GaugidMemoryService
    GOOGLE_ADK_AVAILABLE = True
except ImportError:
    GOOGLE_ADK_AVAILABLE = False
    print("⚠️  Google ADK not installed. Install with: pip install gaugid[adk]")

from gaugid import GaugidClient
from gaugid.logger import get_logger

logger = get_logger("travel_agency")


class TravelAgencyAssistant:
    """
    Travel agency AI assistant with personalized memory.
    
    Features:
    - Remembers user travel preferences
    - Learns from past trips
    - Personalizes recommendations
    - Stores travel memories in Gaugid
    """
    
    def __init__(
        self,
        google_api_key: str,
        connection_token: str,
        app_name: str = "travel-agency",
    ):
        """
        Initialize travel agency assistant.
        
        Args:
            google_api_key: Google API key for Gemini
            connection_token: Gaugid connection token
            app_name: Application name for memory namespace
        """
        if not GOOGLE_ADK_AVAILABLE:
            raise ImportError("Google ADK is not installed")
        
        # Configure Google AI
        genai.configure(api_key=google_api_key)
        
        # Create Gaugid memory service
        self.memory_service = GaugidMemoryService(
            connection_token=connection_token,
            app_name=app_name,
        )
        
        # Create travel planning agent
        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name="travel_planner",
            instruction="""You are a professional travel planning assistant with access to the user's travel history and preferences.

You can:
- Remember user preferences (seat preferences, hotel types, dietary restrictions)
- Learn from past trips (favorite destinations, travel patterns)
- Personalize recommendations based on user profile
- Store important travel information for future reference

Always personalize your recommendations based on what you know about the user.
Reference past trips when relevant to show continuity and understanding.""",
            tools=[PreloadMemoryTool()],  # Automatically loads memories
        )
        
        # Create runner with memory service
        self.runner = Runner(
            agent=self.agent,
            memory_service=self.memory_service,
        )
        
        logger.info("Travel agency assistant initialized")
    
    async def plan_trip(
        self,
        destination: str,
        dates: str,
        travelers: int = 1,
    ) -> str:
        """
        Plan a trip for the user.
        
        Args:
            destination: Travel destination
            dates: Travel dates
            travelers: Number of travelers
            
        Returns:
            Travel plan response
        """
        prompt = f"""Plan a trip to {destination} for {dates} for {travelers} traveler(s).

Consider:
- User's past travel preferences
- Favorite destinations and travel patterns
- Dietary restrictions and preferences
- Hotel and accommodation preferences
- Budget considerations from past trips

Provide a personalized travel plan."""
        
        request = types.Content(
            parts=[types.Part(text=prompt)]
        )
        
        response = await self.runner.run(request)
        
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
        
        # Save session to memory
        session = self.runner.session_service.get_current_session()
        if session:
            await self.memory_service.add_session_to_memory(session)
            logger.info("Travel planning session saved to Gaugid memory")
        
        return response_text
    
    async def remember_preference(
        self,
        preference_type: str,
        preference: str,
    ) -> None:
        """
        Remember a travel preference.
        
        Args:
            preference_type: Type of preference (e.g., "seat", "hotel", "dietary")
            preference: Preference value
        """
        prompt = f"""Remember that the user prefers: {preference} for {preference_type}.

Store this as a travel preference for future trip planning."""
        
        request = types.Content(
            parts=[types.Part(text=prompt)]
        )
        
        await self.runner.run(request)
        
        # Save to memory
        session = self.runner.session_service.get_current_session()
        if session:
            await self.memory_service.add_session_to_memory(session)
            logger.info(f"Preference saved: {preference_type} = {preference}")
    
    async def get_travel_history(self) -> str:
        """
        Get user's travel history summary.
        
        Returns:
            Travel history summary
        """
        prompt = """Summarize the user's travel history, including:
- Past destinations visited
- Travel patterns and preferences
- Favorite types of trips
- Budget considerations
- Any recurring travel preferences"""
        
        request = types.Content(
            parts=[types.Part(text=prompt)]
        )
        
        response = await self.runner.run(request)
        
        response_text = ""
        if hasattr(response, 'parts'):
            for part in response.parts:
                if hasattr(part, 'text'):
                    response_text += part.text
        elif hasattr(response, 'text'):
            response_text = response.text
        
        return response_text
    
    async def close(self) -> None:
        """Close the assistant and cleanup resources."""
        await self.memory_service.close()


async def main():
    """Example: Travel agency assistant."""
    
    if not GOOGLE_ADK_AVAILABLE:
        print("❌ Google ADK is not installed.")
        print("   Install with: pip install gaugid[adk]")
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
    print("     ✈️  Travel Agency Assistant")
    print("═══════════════════════════════════════════════════════════\n")
    
    try:
        # Initialize assistant
        assistant = TravelAgencyAssistant(
            google_api_key=google_api_key,
            connection_token=connection_token,
        )
        
        print("1️⃣ Remembering travel preferences...")
        await assistant.remember_preference("seat", "window seat on flights")
        await assistant.remember_preference("hotel", "boutique hotels in city centers")
        await assistant.remember_preference("dietary", "vegetarian meals")
        print("   ✅ Preferences saved\n")
        
        print("2️⃣ Planning a trip...")
        plan = await assistant.plan_trip(
            destination="Tokyo, Japan",
            dates="March 15-22, 2025",
            travelers=2,
        )
        print(f"   Travel Plan:\n{plan}\n")
        
        print("3️⃣ Getting travel history...")
        history = await assistant.get_travel_history()
        print(f"   Travel History:\n{history}\n")
        
    finally:
        if 'assistant' in locals():
            await assistant.close()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 The assistant remembers:")
    print("   - Travel preferences (seats, hotels, dietary)")
    print("   - Past trips and destinations")
    print("   - Travel patterns and preferences")
    print("   - All stored in Gaugid for future reference!")


if __name__ == "__main__":
    asyncio.run(main())
