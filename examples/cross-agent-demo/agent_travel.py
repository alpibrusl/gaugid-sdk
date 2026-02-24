"""
Travel Agent — Google ADK + Gaugid

A travel planning agent that learns user preferences (destinations,
seat preferences, hotel types, dietary restrictions) and proposes
them as memories to the user's Gaugid profile.

Uses Google ADK with Gemini for the conversational AI layer and
GaugidClient for profile and memory operations.
"""

import asyncio

try:
    import google.generativeai as genai

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from gaugid import GaugidClient

from demo_config import (
    C,
    DemoConfig,
    AGENT_TRAVEL,
    agent_header,
    agent_says,
    memory_proposed,
    memory_loaded,
    success,
    error,
    info,
)

# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a professional travel planning assistant. You help users plan trips,
find great destinations, and remember their travel preferences.

When a user tells you about their travel preferences, acknowledge them warmly
and provide a brief, personalized travel recommendation based on what you learn.

Keep responses concise (2-4 sentences). Be friendly and knowledgeable.
"""

EXTRACTION_PROMPT = """\
Based on the following conversation with a user about travel, extract the key
travel preferences mentioned. Return ONLY a JSON array of objects, each with:
- "content": a clear statement of the preference
- "category": one of "a2p:travel.seats", "a2p:travel.hotels", "a2p:travel.dietary",
  "a2p:travel.destinations", "a2p:travel.style", "a2p:travel.budget"
- "memory_type": one of "semantic" (facts/preferences) or "episodic" (specific experiences)

Example:
[
  {"content": "Prefers window seats on flights", "category": "a2p:travel.seats", "memory_type": "semantic"},
  {"content": "Visited Tokyo in March 2024 and loved it", "category": "a2p:travel.destinations", "memory_type": "episodic"}
]

Conversation:
{conversation}

Extract preferences (JSON array only, no other text):
"""


# ── Travel Agent ──────────────────────────────────────────────────────────────


class TravelAgent:
    """Travel agent that uses Google Gemini + Gaugid for persistent memory."""

    def __init__(self, config: DemoConfig):
        self.config = config
        self.client = GaugidClient(
            connection_token=config.gaugid_connection_token,
            api_url=config.gaugid_api_url or None,
        )
        self.conversation_history: list[dict[str, str]] = []

        if GOOGLE_AVAILABLE and config.google_api_key:
            genai.configure(api_key=config.google_api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
        else:
            self.model = None

    async def load_existing_profile(self) -> list[dict]:
        """Load existing memories from the user's profile."""
        try:
            profile = await self.client.get_profile(scopes=["a2p:travel.*", "a2p:preferences"])
            memories = []
            for mem_type in ("episodic", "semantic", "procedural"):
                memories.extend(profile.get("memories", {}).get(mem_type, []))
            return memories
        except Exception as e:
            info(f"No existing travel profile found: {e}")
            return []

    async def chat(self, user_message: str) -> str:
        """Send a message to the travel agent and get a response."""
        self.conversation_history.append({"role": "user", "content": user_message})

        if self.model is not None:
            # Build prompt with conversation history
            chat_history = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
                for m in self.conversation_history
            )
            prompt = f"{SYSTEM_PROMPT}\n\nConversation so far:\n{chat_history}\n\nAssistant:"

            response = self.model.generate_content(prompt)
            reply = response.text.strip()
        else:
            # Simulated response when no API key
            reply = self._simulated_response(user_message)

        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    async def extract_and_propose_memories(self) -> list[dict]:
        """Extract preferences from conversation and propose as memories."""
        import json

        conversation_text = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Agent'}: {m['content']}"
            for m in self.conversation_history
        )

        preferences = []

        if self.model is not None:
            prompt = EXTRACTION_PROMPT.format(conversation=conversation_text)
            response = self.model.generate_content(prompt)
            raw = response.text.strip()

            # Parse JSON from response (handle markdown code blocks)
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            try:
                preferences = json.loads(raw)
            except json.JSONDecodeError:
                info("Could not parse extraction result, using fallback")
                preferences = self._fallback_extraction()
        else:
            preferences = self._fallback_extraction()

        # Propose each extracted preference to Gaugid
        proposed = []
        for pref in preferences:
            try:
                result = await self.client.propose_memory(
                    content=pref["content"],
                    category=pref.get("category", "a2p:travel.general"),
                    memory_type=pref.get("memory_type", "semantic"),
                    confidence=0.85,
                    context="Learned during travel planning conversation",
                )
                memory_proposed(
                    AGENT_TRAVEL,
                    pref["content"],
                    pref.get("category", "a2p:travel.general"),
                )
                proposed.append({**pref, "proposal_id": result.get("proposal_id")})
            except Exception as e:
                error(f"Failed to propose memory: {e}")

        return proposed

    def _simulated_response(self, user_message: str) -> str:
        """Provide simulated responses when no API key is available."""
        msg = user_message.lower()
        if "window" in msg or "seat" in msg:
            return (
                "Window seats are a great choice! There's nothing like watching "
                "the landscape unfold below. I'll remember your preference for "
                "window seats when planning your flights."
            )
        elif "hotel" in msg or "boutique" in msg:
            return (
                "Boutique hotels in city centers are wonderful — you get that "
                "authentic local feel with easy access to everything. I'll keep "
                "that in mind for your accommodation bookings."
            )
        elif "vegetarian" in msg or "vegan" in msg or "diet" in msg:
            return (
                "Noted! I'll make sure all restaurant and flight meal "
                "recommendations accommodate your vegetarian dietary preferences. "
                "Many destinations have fantastic vegetarian scenes."
            )
        elif "japan" in msg or "tokyo" in msg:
            return (
                "Japan is a phenomenal choice! Tokyo's blend of ultra-modern and "
                "traditional culture is incredible. The vegetarian ramen scene is "
                "also surprisingly good. I'll note this as a destination you love."
            )
        else:
            return (
                "Thanks for sharing that! I've noted your preference and will "
                "use it to personalize your future travel recommendations."
            )

    def _fallback_extraction(self) -> list[dict]:
        """Extract preferences using simple keyword matching."""
        preferences = []
        full_text = " ".join(m["content"] for m in self.conversation_history if m["role"] == "user")
        lower = full_text.lower()

        if "window" in lower:
            preferences.append(
                {
                    "content": "Prefers window seats on flights",
                    "category": "a2p:travel.seats",
                    "memory_type": "semantic",
                }
            )
        if "boutique" in lower or "city center" in lower:
            preferences.append(
                {
                    "content": "Prefers boutique hotels in city centers",
                    "category": "a2p:travel.hotels",
                    "memory_type": "semantic",
                }
            )
        if "vegetarian" in lower:
            preferences.append(
                {
                    "content": "Follows a vegetarian diet",
                    "category": "a2p:travel.dietary",
                    "memory_type": "semantic",
                }
            )
        if "japan" in lower or "tokyo" in lower:
            preferences.append(
                {
                    "content": "Interested in traveling to Japan, especially Tokyo",
                    "category": "a2p:travel.destinations",
                    "memory_type": "episodic",
                }
            )
        return preferences

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.close()


# ── Standalone Entry Point ────────────────────────────────────────────────────


async def run(config: DemoConfig) -> list[dict]:
    """
    Run the travel agent demo segment.

    Returns:
        List of proposed memory dicts.
    """
    agent_header(AGENT_TRAVEL)
    agent = TravelAgent(config)

    try:
        # Load existing profile
        existing = await agent.load_existing_profile()
        if existing:
            memory_loaded(existing, "Existing travel memories")

        # Simulated user conversation
        user_messages = [
            "I always prefer window seats on my flights.",
            "For hotels, I love boutique places in city centers — not big chains.",
            "I'm vegetarian, so dining options matter a lot when I travel.",
            "I've been dreaming about visiting Tokyo! Any recommendations?",
        ]

        for msg in user_messages:
            print(f"\n  {C.WHITE}{C.BOLD}User:{C.RESET} {msg}")
            reply = await agent.chat(msg)
            agent_says(AGENT_TRAVEL, reply)

        # Extract and propose memories
        print()
        info("Extracting travel preferences from conversation...")
        proposed = await agent.extract_and_propose_memories()
        print()
        success(f"Proposed {len(proposed)} travel memories to Gaugid profile")

        return proposed
    finally:
        await agent.close()


if __name__ == "__main__":
    config = DemoConfig.from_env()
    missing = config.validate()
    if "GAUGID_CONNECTION_TOKEN" in [m.split(" ")[0] for m in missing]:
        print(f"{C.RED}GAUGID_CONNECTION_TOKEN is required{C.RESET}")
    else:
        asyncio.run(run(config))
