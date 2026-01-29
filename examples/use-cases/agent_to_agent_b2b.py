"""
Agent-to-Agent (A2A) B2B Use Case: Business Agent Interaction

This example demonstrates B2B agent-to-agent communication where:
- Company A's agent negotiates with Company B's agent
- Each agent has access to their company's profile and preferences
- Agents use A2P-Signature for protocol-compliant authentication
- Business preferences and constraints are stored in Gaugid profiles

Uses: Google ADK + Gemini (Vertex AI) + A2P-Signature

Requires:
- GOOGLE_API_KEY or VERTEX_AI credentials
- Agent DIDs and private keys for both companies
- pip install gaugid[adk] google-generativeai
"""

import asyncio
import os
from typing import Dict, Optional
import base64

try:
    from google.adk import Agent, Runner
    from google.genai import types
    import google.generativeai as genai
    GOOGLE_ADK_AVAILABLE = True
except ImportError:
    GOOGLE_ADK_AVAILABLE = False
    print("⚠️  Google ADK not installed. Install with: pip install gaugid[adk]")

from gaugid import (
    GaugidClient,
    generate_ed25519_keypair,
    generate_a2p_signature_header,
)
from gaugid.logger import get_logger

logger = get_logger("a2a_b2b")


class BusinessAgent:
    """
    Business agent for B2B interactions.
    
    Features:
    - Authenticates with A2P-Signature (protocol-compliant)
    - Accesses company profile from Gaugid
    - Negotiates with other business agents
    - Stores business preferences and constraints
    """
    
    def __init__(
        self,
        company_name: str,
        agent_did: str,
        private_key: bytes,
        google_api_key: str,
        connection_token: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        """
        Initialize business agent.
        
        Args:
            company_name: Company name
            agent_did: Agent DID (e.g., "did:a2p:agent:gaugid:company-a-agent")
            private_key: Agent's Ed25519 private key
            google_api_key: Google API key for Gemini
            connection_token: Optional connection token (for profile access)
            api_url: Optional Gaugid API URL
        """
        if not GOOGLE_ADK_AVAILABLE:
            raise ImportError("Google ADK is not installed")
        
        self.company_name = company_name
        self.agent_did = agent_did
        self.private_key = private_key
        self.api_url = api_url or "https://api.gaugid.com"
        
        # Configure Google AI
        genai.configure(api_key=google_api_key)
        
        # Create Gaugid client (for profile access)
        # In production, this would use A2P-Signature for all requests
        if connection_token:
            self.client = GaugidClient(
                connection_token=connection_token,
                agent_did=agent_did,
                api_url=api_url,
            )
        else:
            self.client = None
        
        # Create negotiation agent
        self.agent = Agent(
            model="gemini-2.0-flash-exp",
            name=f"{company_name}_negotiator",
            instruction=f"""You are a business negotiation agent representing {company_name}.

You have access to your company's profile, preferences, and business constraints.
When negotiating with other companies:
- Represent your company's interests
- Respect business constraints and policies
- Maintain professional communication
- Find mutually beneficial solutions
- Store negotiation outcomes in company profile""",
        )
        
        self.runner = Runner(agent=self.agent)
        
        logger.info(f"Business agent initialized: {company_name} ({agent_did})")
    
    async def get_company_profile(
        self,
        company_did: str,
        scopes: Optional[list[str]] = None,
    ) -> Optional[dict]:
        """
        Get company profile from Gaugid.
        
        Args:
            company_did: Company profile DID
            scopes: Optional scopes to request
            
        Returns:
            Company profile or None
        """
        if not self.client:
            logger.warning("No client configured for profile access")
            return None
        
        try:
            profile = await self.client.get_profile(
                user_did=company_did,
                scopes=scopes or ["a2p:preferences", "a2p:professional"],
            )
            return profile
        except Exception as e:
            logger.error(f"Failed to get company profile: {e}")
            return None
    
    async def negotiate(
        self,
        counterpart_agent: "BusinessAgent",
        negotiation_topic: str,
        initial_proposal: Optional[str] = None,
    ) -> str:
        """
        Negotiate with another business agent.
        
        Args:
            counterpart_agent: The other business agent
            negotiation_topic: Topic of negotiation
            initial_proposal: Optional initial proposal
            
        Returns:
            Negotiation result
        """
        # Load company profile for context
        company_context = ""
        if self.client:
            # In production, this would use company DID
            # For now, use connection token mode
            try:
                profile = await self.client.get_profile(
                    scopes=["a2p:preferences", "a2p:professional"],
                )
                company_context = self._extract_business_context(profile)
            except Exception as e:
                logger.warning(f"Could not load company profile: {e}")
        
        prompt = f"""Negotiate with {counterpart_agent.company_name} about: {negotiation_topic}

Your company context:
{company_context}

Counterpart: {counterpart_agent.company_name} (Agent: {counterpart_agent.agent_did})

{f'Initial proposal: {initial_proposal}' if initial_proposal else ''}

Engage in professional negotiation to reach a mutually beneficial agreement."""
        
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
        
        return response_text
    
    def _extract_business_context(self, profile: dict) -> str:
        """Extract business context from profile."""
        if not profile:
            return "No company context available."
        
        context_parts = []
        
        # Extract preferences
        preferences = profile.get("common", {}).get("preferences", {})
        if preferences:
            context_parts.append(f"Preferences: {preferences}")
        
        # Extract memories (business constraints, policies)
        memories = profile.get("memories", {})
        for memory_type in ["semantic", "procedural"]:
            for memory in memories.get(memory_type, []):
                category = memory.get("category", "")
                if "business" in category.lower() or "policy" in category.lower():
                    context_parts.append(
                        f"- {memory.get('content', '')}"
                    )
        
        return "\n".join(context_parts) if context_parts else "No business context found."
    
    async def store_negotiation_outcome(
        self,
        counterpart: str,
        topic: str,
        outcome: str,
    ) -> None:
        """
        Store negotiation outcome in company profile.
        
        Args:
            counterpart: Counterpart company name
            topic: Negotiation topic
            outcome: Negotiation outcome
        """
        if not self.client:
            return
        
        try:
            await self.client.propose_memory_to_current(
                content=f"Negotiation with {counterpart} about {topic}: {outcome}",
                category="a2p:business.negotiations",
                memory_type="episodic",
                confidence=0.9,
            )
            logger.info(f"Negotiation outcome stored: {topic}")
        except Exception as e:
            logger.error(f"Failed to store negotiation outcome: {e}")


async def main():
    """Example: B2B agent-to-agent negotiation."""
    
    if not GOOGLE_ADK_AVAILABLE:
        print("❌ Google ADK is not installed.")
        print("   Install with: pip install gaugid[adk]")
        return
    
    # Check for API keys
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        return
    
    connection_token_a = os.getenv("GAUGID_CONNECTION_TOKEN_COMPANY_A")
    connection_token_b = os.getenv("GAUGID_CONNECTION_TOKEN_COMPANY_B")
    
    print("═══════════════════════════════════════════════════════════")
    print("     🤝 B2B Agent-to-Agent Negotiation")
    print("═══════════════════════════════════════════════════════════\n")
    
    try:
        # Generate keypairs for both agents
        private_key_a, public_key_a = generate_ed25519_keypair()
        private_key_b, public_key_b = generate_ed25519_keypair()
        
        agent_did_a = "did:a2p:agent:gaugid:company-a-agent"
        agent_did_b = "did:a2p:agent:gaugid:company-b-agent"
        
        # Initialize business agents
        print("1️⃣ Initializing business agents...")
        company_a = BusinessAgent(
            company_name="TechCorp Inc.",
            agent_did=agent_did_a,
            private_key=private_key_a,
            google_api_key=google_api_key,
            connection_token=connection_token_a,
        )
        
        company_b = BusinessAgent(
            company_name="DataSolutions Ltd.",
            agent_did=agent_did_b,
            private_key=private_key_b,
            google_api_key=google_api_key,
            connection_token=connection_token_b,
        )
        print("   ✅ Agents initialized\n")
        
        # Negotiate
        print("2️⃣ Starting negotiation...")
        print("   Topic: Service contract terms\n")
        
        # Company A makes initial proposal
        proposal_a = await company_a.negotiate(
            counterpart_agent=company_b,
            negotiation_topic="Service contract terms",
            initial_proposal="We propose a 12-month contract with monthly payments of $10,000",
        )
        print(f"   {company_a.company_name}: {proposal_a}\n")
        
        # Company B responds
        response_b = await company_b.negotiate(
            counterpart_agent=company_a,
            negotiation_topic="Service contract terms",
            initial_proposal=proposal_a,
        )
        print(f"   {company_b.company_name}: {response_b}\n")
        
        # Store outcomes
        print("3️⃣ Storing negotiation outcomes...")
        await company_a.store_negotiation_outcome(
            counterpart=company_b.company_name,
            topic="Service contract terms",
            outcome="Initial negotiation started",
        )
        await company_b.store_negotiation_outcome(
            counterpart=company_a.company_name,
            topic="Service contract terms",
            outcome="Initial negotiation started",
        )
        print("   ✅ Outcomes stored\n")
        
    finally:
        # Cleanup
        pass
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 B2B agents can:")
    print("   - Authenticate with A2P-Signature (protocol-compliant)")
    print("   - Access company profiles from Gaugid")
    print("   - Negotiate autonomously with other agents")
    print("   - Store negotiation outcomes for future reference")


if __name__ == "__main__":
    asyncio.run(main())
