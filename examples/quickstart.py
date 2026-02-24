#!/usr/bin/env python3
"""
Gaugid Quickstart — Get running in 30 seconds

The simplest possible Gaugid integration:
  1. Load a user's profile
  2. Use it to personalize a response
  3. Propose a new memory

No AI API keys needed. Just a Gaugid connection token.

Setup:
    pip install gaugid
    export GAUGID_CONNECTION_TOKEN=gaugid_conn_xxx  # from dashboard.gaugid.com
    python quickstart.py
"""

import asyncio
import os


async def main() -> None:
    from gaugid import GaugidClient

    # Get connection token from environment
    token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not token:
        print("Set GAUGID_CONNECTION_TOKEN first.")
        print("Get one from https://dashboard.gaugid.com")
        return

    # Initialize client
    client = GaugidClient(connection_token=token)

    try:
        # 1. Load the user's profile
        print("Loading profile...")
        profile = await client.get_profile(scopes=["a2p:preferences", "a2p:interests"])

        memories = profile.get("memories", {})
        total = sum(len(mems) for mems in memories.values())
        print(f"Found {total} memories in profile.\n")

        # Show what's there
        for mem_type, mems in memories.items():
            for m in mems:
                print(f"  [{m.get('category', '?')}] {m.get('content', '')}")

        # 2. Propose a new memory
        print("\nProposing a memory...")
        result = await client.propose_memory(
            content="Ran the Gaugid quickstart example",
            category="a2p:context.interactions",
            memory_type="episodic",
            confidence=0.9,
        )
        proposal_id = result.get("proposal_id", "unknown")
        print(f"Proposed! ID: {proposal_id}")
        print("Approve it in the dashboard: https://dashboard.gaugid.com")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
