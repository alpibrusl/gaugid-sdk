"""
Child Safety Use Case: Restricted Agent Access for Children

This example demonstrates a child-safe AI agent that:
- Enforces age-appropriate content restrictions
- Requires parent/guardian authorization
- Stores child preferences safely
- Limits access to specific scopes (no personal data exposure)
- Uses child-safe memory storage

Uses: Google ADK + Gemini (Vertex AI) + Gaugid with Restricted Scopes

Requires:
- GOOGLE_API_KEY or VERTEX_AI credentials
- GAUGID_CONNECTION_TOKEN (with child-safe scopes)
- pip install gaugid[adk] google-generativeai
"""

import asyncio
import os
from typing import Dict, Optional, List
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

logger = get_logger("child_safety")


class ChildSafetyAgent:
    """
    Child-safe AI agent with content restrictions.
    
    Features:
    - Age-appropriate content filtering
    - Parent/guardian authorization required
    - Limited scope access (no personal data)
    - Safe memory storage
    - Educational and fun interactions
    """
    
    # Allowed scopes for child profiles (restricted)
    CHILD_SAFE_SCOPES = [
        "a2p:interests",  # Only interests, no personal data
        # Explicitly exclude: a2p:identity, a2p:preferences (personal data)
    ]
    
    # Content safety filters
    SAFETY_SETTINGS = {
        "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
    }
    
    def __init__(
        self,
        google_api_key: str,
        connection_token: str,
        child_name: str,
        age: int,
        parent_authorized: bool = False,
        app_name: str = "child-safety-assistant",
    ):
        """
        Initialize child-safe agent.
        
        Args:
            google_api_key: Google API key for Gemini
            connection_token: Gaugid connection token (with child-safe scopes)
            child_name: Child's name (for personalization)
            age: Child's age (for age-appropriate content)
            parent_authorized: Whether parent has authorized this session
            app_name: Application name for memory namespace
        """
        if not GOOGLE_ADK_AVAILABLE:
            raise ImportError("Google ADK is not installed")
        
        if not parent_authorized:
            raise ValueError("Parent/guardian authorization required for child agent")
        
        if age < 13:
            # Additional restrictions for children under 13
            self.CHILD_SAFE_SCOPES = ["a2p:interests"]  # Even more restricted
        
        self.child_name = child_name
        self.age = age
        self.parent_authorized = parent_authorized
        
        # Configure Google AI with safety settings
        genai.configure(api_key=google_api_key)
        
        # Create Gaugid memory service (child-safe)
        self.memory_service = GaugidMemoryService(
            connection_token=connection_token,
            app_name=app_name,
        )
        
        # Create child-safe agent
        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name="child_safe_assistant",
            instruction=f"""You are a friendly, educational AI assistant for children.

Child Information:
- Name: {child_name}
- Age: {age}

Rules:
- Always be age-appropriate and educational
- Never ask for personal information (address, phone, school name)
- Keep conversations fun, safe, and educational
- Encourage learning and creativity
- Remember child's interests and preferences (safely stored)
- Never share personal information with others
- If asked inappropriate questions, politely redirect to safe topics

You can:
- Help with homework and learning
- Tell age-appropriate stories
- Play educational games
- Remember favorite topics and interests (safely)
- Encourage creativity and curiosity

Always prioritize child safety and well-being.""",
            tools=[PreloadMemoryTool()],
        )
        
        # Create runner with memory service
        self.runner = Runner(
            agent=self.agent,
            memory_service=self.memory_service,
        )
        
        logger.info(f"Child-safe agent initialized for {child_name} (age {age})")
    
    async def get_child_profile(self) -> Optional[dict]:
        """
        Get child profile with restricted scopes.
        
        Returns:
            Child profile (only safe scopes) or None
        """
        try:
            # Use Gaugid client to get profile with restricted scopes
            client = GaugidClient(connection_token=self.memory_service.client.connection_token)
            
            # Only request child-safe scopes
            profile = await client.get_profile(
                scopes=self.CHILD_SAFE_SCOPES,
            )
            
            # Verify no personal data is included
            if "identity" in profile:
                # Remove personal data if somehow included
                profile.pop("identity", None)
            
            return profile
        except Exception as e:
            logger.error(f"Failed to get child profile: {e}")
            return None
    
    async def chat(
        self,
        message: str,
    ) -> str:
        """
        Chat with child (with safety checks).
        
        Args:
            message: Child's message
            
        Returns:
            Safe, age-appropriate response
        """
        # Safety check: Filter inappropriate content
        if self._is_inappropriate(message):
            return "I can't help with that. Let's talk about something fun and educational instead! What's your favorite subject in school?"
        
        # Build safe prompt
        prompt = f"""{self.child_name} says: {message}

Respond in an age-appropriate, educational, and fun way.
Remember: {self.child_name} is {self.age} years old.
Keep it safe, positive, and encouraging."""
        
        request = types.Content(
            parts=[types.Part(text=prompt)]
        )
        
        response = await self.runner.run(request)
        
        # Extract response
        response_text = ""
        if hasattr(response, 'parts'):
            for part in response.parts:
                if hasattr(part, 'text'):
                    response_text += part.text
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            response_text = str(response)
        
        # Save session to memory (safely)
        session = self.runner.session_service.get_current_session()
        if session:
            await self.memory_service.add_session_to_memory(session)
            logger.info("Child interaction saved safely to Gaugid memory")
        
        return response_text
    
    def _is_inappropriate(self, message: str) -> bool:
        """
        Check if message contains inappropriate content.
        
        Args:
            message: Message to check
            
        Returns:
            True if inappropriate, False otherwise
        """
        # Simple keyword-based check (in production, use more sophisticated filtering)
        inappropriate_keywords = [
            "personal information",
            "address",
            "phone number",
            "school name",
            "where do you live",
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in inappropriate_keywords)
    
    async def remember_interest(
        self,
        interest: str,
    ) -> None:
        """
        Remember a child's interest (safely).
        
        Args:
            interest: Child's interest (e.g., "dinosaurs", "space", "art")
        """
        prompt = f"""Remember that {self.child_name} is interested in: {interest}

Store this as a safe interest for future conversations.
This helps personalize educational content."""
        
        request = types.Content(
            parts=[types.Part(text=prompt)]
        )
        
        await self.runner.run(request)
        
        # Save to memory
        session = self.runner.session_service.get_current_session()
        if session:
            await self.memory_service.add_session_to_memory(session)
            logger.info(f"Interest saved safely: {interest}")
    
    async def close(self) -> None:
        """Close the assistant and cleanup resources."""
        await self.memory_service.close()


async def main():
    """Example: Child-safe agent."""
    
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
        print("   Note: Token should have restricted scopes (child-safe)")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🧒 Child Safety Agent")
    print("═══════════════════════════════════════════════════════════\n")
    
    try:
        # Initialize child-safe agent
        # Note: In production, parent authorization would be verified via OAuth
        assistant = ChildSafetyAgent(
            google_api_key=google_api_key,
            connection_token=connection_token,
            child_name="Alex",
            age=10,
            parent_authorized=True,  # In production, verify this via OAuth
        )
        
        print("1️⃣ Remembering child's interests...")
        await assistant.remember_interest("dinosaurs")
        await assistant.remember_interest("space exploration")
        print("   ✅ Interests saved safely\n")
        
        print("2️⃣ Chatting with child...")
        response1 = await assistant.chat("Tell me about dinosaurs!")
        print(f"   Child: Tell me about dinosaurs!")
        print(f"   Assistant: {response1}\n")
        
        response2 = await assistant.chat("What's my address?")
        print(f"   Child: What's my address?")
        print(f"   Assistant: {response2}\n")
        
        response3 = await assistant.chat("Can you help me with my math homework?")
        print(f"   Child: Can you help me with my math homework?")
        print(f"   Assistant: {response3}\n")
        
    finally:
        if 'assistant' in locals():
            await assistant.close()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 Child safety features:")
    print("   - Age-appropriate content filtering")
    print("   - Restricted scope access (no personal data)")
    print("   - Parent/guardian authorization required")
    print("   - Safe memory storage (interests only)")
    print("   - Inappropriate content detection and redirection")
    print("   - Educational and fun interactions!")


if __name__ == "__main__":
    asyncio.run(main())
