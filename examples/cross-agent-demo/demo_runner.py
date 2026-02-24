#!/usr/bin/env python3
"""
Gaugid Cross-Agent Demo — Three Agents, One Profile

This demo shows the core value proposition of Gaugid:
your AI context follows you across ANY agent, and YOU control it.

Demo flow:
  1. Travel Agent (Google ADK) learns your travel preferences
  2. Dashboard pause — you approve/reject the proposed memories
  3. Food Agent (LangGraph) reads the shared profile and already
     knows your dietary preferences without being told
  4. Food Agent proposes new food memories
  5. Personal Assistant (Anthropic) sees EVERYTHING — travel + food
  6. Final dashboard view — full profile, consent trail, audit log

Run:
    python demo_runner.py

Environment variables:
    GAUGID_CONNECTION_TOKEN  — required (get from dashboard.gaugid.com)
    GOOGLE_API_KEY           — optional (for real Gemini responses)
    ANTHROPIC_API_KEY        — optional (for real Claude responses)
    GAUGID_API_URL           — optional (defaults to production)
    DEMO_MODE=true           — optional (skip API calls, use simulated responses)
"""

import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from demo_config import (  # noqa: E402
    C,
    DemoConfig,
    LINE_WIDTH,
    banner,
    section,
    step,
    info,
    error,
    success,
    pause_for_dashboard,
    format_profile_summary,
)
from gaugid import GaugidClient  # noqa: E402


async def show_final_profile(config: DemoConfig) -> None:
    """Load and display the final profile state."""
    client = GaugidClient(
        connection_token=config.gaugid_connection_token,
        api_url=config.gaugid_api_url or None,
    )
    try:
        profile = await client.get_profile(
            scopes=[
                "a2p:travel.*",
                "a2p:food.*",
                "a2p:preferences",
                "a2p:interests",
                "a2p:context.*",
                "a2p:professional",
            ]
        )
        summary = format_profile_summary(profile)
        print(summary)
    except Exception as e:
        error(f"Could not load final profile: {e}")
    finally:
        await client.close()


async def main() -> None:
    # ── Load & Validate Config ────────────────────────────────────────────

    config = DemoConfig.from_env()
    missing = config.validate()

    banner("GAUGID CROSS-AGENT DEMO — Three Agents, One Profile")

    print(f"  {C.BOLD}The Pitch:{C.RESET}")
    print("  Your AI context follows you across ANY agent,")
    print("  and YOU control it. That's what no one else offers.")
    print()

    # Check required config
    if "GAUGID_CONNECTION_TOKEN" in missing:
        error("GAUGID_CONNECTION_TOKEN environment variable is required.")
        print("\n  Get a connection token from the Gaugid dashboard.")
        print("  Then: export GAUGID_CONNECTION_TOKEN=gaugid_conn_xxx")
        return

    # Show config status
    has_google = bool(config.google_api_key)
    has_anthropic = bool(config.anthropic_api_key)

    section("Configuration")
    success("Gaugid connection token: set")
    if has_google:
        success("Google API key: set (real Gemini responses)")
    else:
        info("Google API key: not set (using simulated responses)")
    if has_anthropic:
        success("Anthropic API key: set (real Claude responses)")
    else:
        info("Anthropic API key: not set (using simulated responses)")

    if not has_google and not has_anthropic:
        print(f"\n  {C.YELLOW}Tip: Set GOOGLE_API_KEY and/or ANTHROPIC_API_KEY")
        print(f"  for real AI responses instead of simulated ones.{C.RESET}")

    print()
    input(f"  {C.BOLD}Press Enter to start the demo...{C.RESET}")

    # ── Step 1: Travel Agent ──────────────────────────────────────────────

    section("STEP 1: Travel Agent learns your preferences")
    step(1, "Talking to the Travel Agent (Google ADK + Gemini)...")
    print(f"  {C.DIM}The travel agent will learn about your seat, hotel,")
    print(f"  dietary preferences, and dream destinations.{C.RESET}")

    import agent_travel

    travel_proposals = await agent_travel.run(config)

    # ── Step 2: Dashboard Pause ───────────────────────────────────────────

    section("STEP 2: Approve memories in the Gaugid Dashboard")
    step(2, "Check the dashboard for memory proposals")
    print(f"\n  The Travel Agent proposed {C.BOLD}{len(travel_proposals)}{C.RESET} memories.")
    print(f"  Open {C.UNDERLINE}dashboard.gaugid.com{C.RESET} to review them.")
    print()
    print(f"  {C.GREEN}Approve{C.RESET} the ones you want to keep.")
    print(f"  {C.RED}Reject{C.RESET} anything you don't want shared.")
    print(f"  {C.YELLOW}This is user control in action.{C.RESET}")

    pause_for_dashboard()

    # ── Step 3: Food Agent ────────────────────────────────────────────────

    section("STEP 3: Food Agent uses your shared profile")
    step(3, "Talking to the Food Agent (LangGraph + Gemini)...")
    print(f"  {C.DIM}Watch: the food agent already knows your dietary")
    print(f"  preferences from the travel agent's memories!{C.RESET}")

    import agent_food

    food_proposals = await agent_food.run(config)

    # ── Step 4: Dashboard Pause (optional) ────────────────────────────────

    section("STEP 4: Review food memories (optional)")
    step(4, "The Food Agent proposed new memories")
    print(f"\n  The Food Agent proposed {C.BOLD}{len(food_proposals)}{C.RESET} new memories.")
    print("  Open the dashboard to approve them if you'd like.")

    pause_for_dashboard()

    # ── Step 5: Personal Assistant ────────────────────────────────────────

    section("STEP 5: Personal Assistant sees EVERYTHING")
    step(5, "Talking to the Personal Assistant (Anthropic Claude)...")
    print(f"  {C.DIM}The assistant loads your complete profile: travel")
    print(f"  preferences + food preferences + everything else.{C.RESET}")
    print(f"  {C.DIM}All from different agents, all user-approved.{C.RESET}")

    import agent_assistant

    await agent_assistant.run(config)

    # ── Step 6: Final Profile View ────────────────────────────────────────

    section("STEP 6: Your Complete Gaugid Profile")
    step(6, "Loading final profile state...")
    print()
    await show_final_profile(config)

    # ── Finale ────────────────────────────────────────────────────────────

    border = "=" * LINE_WIDTH
    print(f"\n{C.GREEN}{C.BOLD}{border}")
    print("  DEMO COMPLETE")
    print(f"{border}{C.RESET}")
    print()
    print(f"  {C.BOLD}What just happened:{C.RESET}")
    print(f"  {C.TRAVEL}  Travel Agent{C.RESET} learned your preferences    (Google ADK)")
    print(f"  {C.FOOD}  Food Agent{C.RESET} read & extended your profile (LangGraph)")
    print(f"  {C.ASSISTANT}  Assistant{C.RESET} saw everything, seamlessly     (Anthropic)")
    print()
    print(f"  {C.BOLD}The key insight:{C.RESET}")
    print("  Three different agents, three different frameworks,")
    print(f"  three different AI providers — {C.BOLD}one portable profile{C.RESET}.")
    print("  And the user controlled it all through the dashboard.")
    print()
    print(f"  {C.BOLD}That's Gaugid.{C.RESET}")
    print("  Consent-first, portable AI memory you actually own.")
    print()
    print(f"  {C.DIM}Learn more: https://gaugid.com")
    print(f"  Dashboard: https://dashboard.gaugid.com{C.RESET}")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n  {C.YELLOW}Demo interrupted.{C.RESET}")
        sys.exit(0)
