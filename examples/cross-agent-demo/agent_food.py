"""
Food Agent — LangGraph + Gaugid

A food delivery agent that reads the user's shared Gaugid profile
(including travel preferences set by Agent 1), personalizes its
recommendations, and proposes new food-related memories.

Uses LangGraph for the conversational flow and GaugidClient for
profile and memory operations.
"""

import asyncio

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from gaugid import GaugidClient

from demo_config import (
    C,
    DemoConfig,
    AGENT_FOOD,
    agent_header,
    agent_says,
    memory_proposed,
    memory_loaded,
    success,
    error,
    info,
)

# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """\
You are a friendly food delivery assistant. You help users discover
restaurants and meals they'll love, based on their dietary preferences
and taste profile.

{profile_context}

Use the user's profile to personalize every recommendation.
If you see dietary restrictions, ALWAYS respect them.
Keep responses concise (2-4 sentences). Be enthusiastic about food.
"""

EXTRACTION_PROMPT = """\
Based on the following conversation about food, extract the key food
preferences mentioned. Return ONLY a JSON array of objects, each with:
- "content": a clear statement of the preference
- "category": one of "a2p:food.dietary", "a2p:food.cuisines", "a2p:food.restaurants",
  "a2p:food.dishes", "a2p:food.budget", "a2p:food.allergies"
- "memory_type": one of "semantic" (facts/preferences) or "episodic" (specific experiences)

Conversation:
{conversation}

Extract preferences (JSON array only, no other text):
"""


# ── Food Agent ────────────────────────────────────────────────────────────────


class FoodAgent:
    """Food agent that uses LangChain/Gemini + Gaugid for shared memory."""

    def __init__(self, config: DemoConfig):
        self.config = config
        self.client = GaugidClient(
            connection_token=config.gaugid_connection_token,
            api_url=config.gaugid_api_url or None,
        )
        self.conversation_history: list[dict[str, str]] = []
        self.profile_context: str = ""

        if LANGGRAPH_AVAILABLE and config.google_api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=config.google_api_key,
                temperature=0.7,
            )
        else:
            self.llm = None

    async def load_shared_profile(self) -> list[dict]:
        """
        Load the user's full profile — including memories from OTHER agents.
        This is the key moment: the food agent sees travel preferences
        that were proposed by the travel agent.
        """
        try:
            profile = await self.client.get_profile(
                scopes=[
                    "a2p:travel.*",
                    "a2p:food.*",
                    "a2p:preferences",
                    "a2p:interests",
                ]
            )
            memories = []
            for mem_type in ("episodic", "semantic", "procedural"):
                memories.extend(profile.get("memories", {}).get(mem_type, []))

            # Build profile context string for the LLM
            if memories:
                context_lines = ["USER PROFILE (from Gaugid - shared across agents):"]
                for m in memories:
                    cat = m.get("category", "general")
                    content = m.get("content", "")
                    context_lines.append(f"- [{cat}] {content}")
                self.profile_context = "\n".join(context_lines)
            else:
                self.profile_context = "No existing profile information available."

            return memories
        except Exception as e:
            info(f"Could not load shared profile: {e}")
            self.profile_context = "No existing profile information available."
            return []

    async def chat(self, user_message: str) -> str:
        """Send a message to the food agent and get a response."""
        self.conversation_history.append({"role": "user", "content": user_message})

        if self.llm is not None:
            system = SYSTEM_PROMPT_TEMPLATE.format(profile_context=self.profile_context)
            messages = [SystemMessage(content=system)]
            for m in self.conversation_history:
                if m["role"] == "user":
                    messages.append(HumanMessage(content=m["content"]))
                else:
                    messages.append(AIMessage(content=m["content"]))

            response = self.llm.invoke(messages)
            reply = response.content.strip()
        else:
            reply = self._simulated_response(user_message)

        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    async def extract_and_propose_memories(self) -> list[dict]:
        """Extract food preferences and propose as memories."""
        import json

        conversation_text = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Agent'}: {m['content']}"
            for m in self.conversation_history
        )

        preferences = []

        if self.llm is not None:
            prompt = EXTRACTION_PROMPT.format(conversation=conversation_text)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = response.content.strip()

            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            try:
                preferences = json.loads(raw)
            except json.JSONDecodeError:
                info("Could not parse extraction result, using fallback")
                preferences = self._fallback_extraction()
        else:
            preferences = self._fallback_extraction()

        proposed = []
        for pref in preferences:
            try:
                result = await self.client.propose_memory(
                    content=pref["content"],
                    category=pref.get("category", "a2p:food.general"),
                    memory_type=pref.get("memory_type", "semantic"),
                    confidence=0.85,
                    context="Learned during food delivery conversation",
                )
                memory_proposed(
                    AGENT_FOOD,
                    pref["content"],
                    pref.get("category", "a2p:food.general"),
                )
                proposed.append({**pref, "proposal_id": result.get("proposal_id")})
            except Exception as e:
                error(f"Failed to propose memory: {e}")

        return proposed

    def _simulated_response(self, user_message: str) -> str:
        """Simulated responses when no API key is available."""
        msg = user_message.lower()

        # Check if we have travel context to reference
        has_vegetarian = "vegetarian" in self.profile_context.lower()
        has_tokyo = (
            "tokyo" in self.profile_context.lower() or "japan" in self.profile_context.lower()
        )

        if "recommend" in msg or "suggest" in msg or "dinner" in msg:
            base = "I'd love to help with dinner recommendations!"
            if has_vegetarian:
                base += (
                    " I see from your profile that you're vegetarian — "
                    "I'll make sure all suggestions are veggie-friendly."
                )
            if has_tokyo:
                base += (
                    " And since you're interested in Japanese food, how about "
                    "a great Japanese restaurant with amazing vegetable tempura?"
                )
            return base

        elif "italian" in msg or "pasta" in msg:
            resp = "Italian is a fantastic choice!"
            if has_vegetarian:
                resp += (
                    " Since you're vegetarian, I'd recommend trying the "
                    "truffle mushroom risotto or the eggplant parmigiana. "
                    "Both are incredible at Trattoria Verde."
                )
            else:
                resp += (
                    " There are some amazing pasta spots nearby. "
                    "Trattoria Verde has incredible handmade pasta."
                )
            return resp

        elif "spicy" in msg:
            return (
                "Noted — you enjoy spicy food! I'll prioritize restaurants "
                "that offer good heat levels. Thai and Sichuan places nearby "
                "have excellent spicy vegetarian options."
            )

        elif "budget" in msg or "price" in msg:
            return (
                "I'll keep recommendations in the mid-range budget. "
                "There are great quality-to-price options for "
                "vegetarian dining in your area."
            )

        else:
            return (
                "Got it! I've noted that preference. It helps me find "
                "the perfect restaurants and dishes for you."
            )

    def _fallback_extraction(self) -> list[dict]:
        """Extract preferences using keyword matching."""
        preferences = []
        full_text = " ".join(m["content"] for m in self.conversation_history if m["role"] == "user")
        lower = full_text.lower()

        if "italian" in lower or "pasta" in lower:
            preferences.append(
                {
                    "content": "Enjoys Italian cuisine, especially pasta dishes",
                    "category": "a2p:food.cuisines",
                    "memory_type": "semantic",
                }
            )
        if "spicy" in lower:
            preferences.append(
                {
                    "content": "Likes spicy food",
                    "category": "a2p:food.cuisines",
                    "memory_type": "semantic",
                }
            )
        if "budget" in lower or "mid-range" in lower:
            preferences.append(
                {
                    "content": "Prefers mid-range budget for dining",
                    "category": "a2p:food.budget",
                    "memory_type": "semantic",
                }
            )
        if "delivery" in lower:
            preferences.append(
                {
                    "content": "Uses food delivery services regularly",
                    "category": "a2p:food.general",
                    "memory_type": "procedural",
                }
            )

        # Always add a cuisine preference if nothing else was found
        if not preferences:
            preferences.append(
                {
                    "content": "Exploring diverse cuisine options",
                    "category": "a2p:food.cuisines",
                    "memory_type": "semantic",
                }
            )

        return preferences

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.close()


# ── Standalone Entry Point ────────────────────────────────────────────────────


async def run(config: DemoConfig) -> list[dict]:
    """
    Run the food agent demo segment.

    Returns:
        List of proposed memory dicts.
    """
    agent_header(AGENT_FOOD)
    agent = FoodAgent(config)

    try:
        # Load shared profile — cross-agent context sharing
        info("Loading shared profile (including travel agent's memories)...")
        shared_memories = await agent.load_shared_profile()
        if shared_memories:
            memory_loaded(shared_memories, "Shared profile loaded from Gaugid")
        else:
            info("No shared memories found yet.")

        # Simulated user conversation
        user_messages = [
            "Can you recommend something for dinner tonight?",
            "I love Italian food — any good pasta places nearby?",
            "I also enjoy spicy food. What are my options?",
            "Keep it mid-range budget please.",
        ]

        for msg in user_messages:
            print(f"\n  {C.WHITE}{C.BOLD}User:{C.RESET} {msg}")
            reply = await agent.chat(msg)
            agent_says(AGENT_FOOD, reply)

        # Extract and propose food memories
        print()
        info("Extracting food preferences from conversation...")
        proposed = await agent.extract_and_propose_memories()
        print()
        success(f"Proposed {len(proposed)} food memories to Gaugid profile")

        return proposed
    finally:
        await agent.close()


if __name__ == "__main__":
    config = DemoConfig.from_env()
    asyncio.run(run(config))
