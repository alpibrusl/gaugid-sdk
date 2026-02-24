"""
Personal Assistant — Anthropic Claude + Gaugid

A general-purpose assistant that reads the user's FULL Gaugid profile
(travel + food + all other memories from every agent) and demonstrates
complete cross-agent context awareness.

Uses Anthropic Claude for the conversational AI layer and GaugidClient
for profile operations.
"""

import asyncio

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from gaugid import GaugidClient

from demo_config import (
    C,
    DemoConfig,
    AGENT_ASSISTANT,
    agent_header,
    agent_says,
    memory_loaded,
    success,
    info,
)

# ── Prompts ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """\
You are a helpful personal assistant with access to the user's profile
from Gaugid — a consent-based, cross-agent memory system.

The following profile data was approved by the user and shared with you.
It includes memories from different AI agents the user has interacted with.

{profile_context}

IMPORTANT INSTRUCTIONS:
- Reference specific memories from the profile to show you truly know the user.
- Mention preferences from DIFFERENT agents (travel, food, etc.) to demonstrate
  cross-agent awareness — this is the key value proposition.
- Be concise (3-5 sentences per response).
- Be warm, helpful, and slightly impressed by how well you know the user.
"""


# ── Personal Assistant Agent ──────────────────────────────────────────────────


class AssistantAgent:
    """Personal assistant that uses Anthropic Claude + Gaugid shared profile."""

    def __init__(self, config: DemoConfig):
        self.config = config
        self.client = GaugidClient(
            connection_token=config.gaugid_connection_token,
            api_url=config.gaugid_api_url or None,
        )
        self.conversation_history: list[dict[str, str]] = []
        self.profile_context: str = ""
        self.loaded_memories: list[dict] = []

        if ANTHROPIC_AVAILABLE and config.anthropic_api_key:
            self.anthropic = Anthropic(api_key=config.anthropic_api_key)
        else:
            self.anthropic = None

    async def load_full_profile(self) -> list[dict]:
        """
        Load the user's complete profile — ALL memories from ALL agents.
        This is the culmination: the assistant sees everything the user
        has approved from travel + food + any other source.
        """
        try:
            profile = await self.client.get_profile(
                scopes=[
                    "a2p:travel.*",
                    "a2p:food.*",
                    "a2p:preferences",
                    "a2p:interests",
                    "a2p:context.*",
                    "a2p:professional",
                ]
            )
            memories = []
            for mem_type in ("episodic", "semantic", "procedural"):
                for m in profile.get("memories", {}).get(mem_type, []):
                    m["_type"] = mem_type
                    memories.append(m)

            self.loaded_memories = memories

            # Build comprehensive profile context for Claude
            if memories:
                lines = [
                    "USER PROFILE (from Gaugid - approved memories from multiple AI agents):",
                    "",
                ]
                # Group by category prefix
                travel_mems = [m for m in memories if "travel" in m.get("category", "")]
                food_mems = [m for m in memories if "food" in m.get("category", "")]
                other_mems = [
                    m
                    for m in memories
                    if "travel" not in m.get("category", "") and "food" not in m.get("category", "")
                ]

                if travel_mems:
                    lines.append("Travel preferences (learned by Travel Agent):")
                    for m in travel_mems:
                        lines.append(f"  - {m.get('content', '')}")

                if food_mems:
                    lines.append("Food preferences (learned by Food Agent):")
                    for m in food_mems:
                        lines.append(f"  - {m.get('content', '')}")

                if other_mems:
                    lines.append("Other profile data:")
                    for m in other_mems:
                        lines.append(f"  - [{m.get('category', '')}] {m.get('content', '')}")

                self.profile_context = "\n".join(lines)
            else:
                self.profile_context = "No profile data available yet."

            return memories
        except Exception as e:
            info(f"Could not load full profile: {e}")
            self.profile_context = "No profile data available yet."
            return []

    async def chat(self, user_message: str) -> str:
        """Send a message to the assistant and get a response."""
        self.conversation_history.append({"role": "user", "content": user_message})

        if self.anthropic is not None:
            system = SYSTEM_PROMPT_TEMPLATE.format(profile_context=self.profile_context)
            messages = [
                {"role": m["role"], "content": m["content"]} for m in self.conversation_history
            ]

            response = self.anthropic.messages.create(
                model="claude-sonnet-4-5-20250514",
                max_tokens=1024,
                system=system,
                messages=messages,
            )
            reply = response.content[0].text.strip()
        else:
            reply = self._simulated_response(user_message)

        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply

    def _simulated_response(self, user_message: str) -> str:
        """Simulated responses demonstrating cross-agent awareness."""
        msg = user_message.lower()

        # Extract what we know from profile context
        ctx = self.profile_context.lower()
        knows_vegetarian = "vegetarian" in ctx
        knows_window = "window" in ctx
        knows_tokyo = "tokyo" in ctx or "japan" in ctx
        knows_italian = "italian" in ctx
        knows_spicy = "spicy" in ctx
        knows_boutique = "boutique" in ctx

        if "know about me" in msg or "what do you know" in msg:
            parts = ["Based on your Gaugid profile, I know quite a bit about you!"]
            if knows_vegetarian:
                parts.append("You follow a vegetarian diet.")
            if knows_window:
                parts.append("You prefer window seats on flights.")
            if knows_boutique:
                parts.append("You love boutique hotels in city centers.")
            if knows_tokyo:
                parts.append("You're interested in visiting Tokyo.")
            if knows_italian:
                parts.append("You enjoy Italian cuisine.")
            if knows_spicy:
                parts.append("You like spicy food.")
            parts.append(
                "All of this was learned by different AI agents and approved by "
                "you through Gaugid — I didn't have to ask you again!"
            )
            return " ".join(parts)

        elif "plan" in msg or "weekend" in msg or "evening" in msg:
            resp = "I'd love to help plan your evening!"
            if knows_vegetarian and knows_italian:
                resp += (
                    " Since you enjoy Italian food and are vegetarian, "
                    "how about starting with dinner at a great Italian place — "
                    "maybe some truffle mushroom risotto?"
                )
            if knows_tokyo:
                resp += (
                    " And if you're still dreaming about Tokyo, I could help "
                    "you start planning that trip while you enjoy your meal!"
                )
            return resp

        elif "trip" in msg or "travel" in msg:
            resp = "Let me pull together what I know for your trip!"
            if knows_window:
                resp += " I'll look for flights with window seat availability."
            if knows_boutique:
                resp += " And boutique hotels in the city center, of course."
            if knows_vegetarian:
                resp += " I'll also flag restaurants with strong vegetarian menus."
            resp += (
                " Notice how I know all this from your travel and food agents — "
                "no need to repeat yourself!"
            )
            return resp

        else:
            return (
                "I have your full profile from Gaugid, which includes "
                "preferences learned by both your travel agent and food agent. "
                "I can use all of this context to help you with anything — "
                "that's the power of portable, user-owned AI memory!"
            )

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.close()


# ── Standalone Entry Point ────────────────────────────────────────────────────


async def run(config: DemoConfig) -> None:
    """Run the assistant agent demo segment."""
    agent_header(AGENT_ASSISTANT)
    agent = AssistantAgent(config)

    try:
        # Load the full profile — ALL memories from ALL agents
        info("Loading FULL profile (all memories from all agents)...")
        all_memories = await agent.load_full_profile()
        if all_memories:
            memory_loaded(all_memories, "Complete profile loaded from Gaugid")
        else:
            info("No memories found in profile.")

        # Demonstrate cross-agent awareness
        user_messages = [
            "What do you know about me?",
            "Can you help me plan a nice evening?",
            "What about planning that Japan trip?",
        ]

        for msg in user_messages:
            print(f"\n  {C.WHITE}{C.BOLD}User:{C.RESET} {msg}")
            reply = await agent.chat(msg)
            agent_says(AGENT_ASSISTANT, reply)

        print()
        success(
            "The assistant demonstrated cross-agent context awareness — "
            "travel + food preferences, all from one Gaugid profile!"
        )
    finally:
        await agent.close()


if __name__ == "__main__":
    config = DemoConfig.from_env()
    asyncio.run(run(config))
