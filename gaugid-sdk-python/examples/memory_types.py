"""
Memory types example for Gaugid SDK.

This example demonstrates how to use different memory types (episodic,
semantic, and procedural) when proposing memories.
"""

import asyncio
from gaugid import GaugidClient


async def main() -> None:
    """Example: Using different memory types."""
    # Initialize client with connection token
    client = GaugidClient(connection_token="gaugid_conn_xxx")

    try:
        print("=== Memory Types Example ===\n")
        
        # 1. Episodic Memory - Specific events and experiences
        print("1. Proposing episodic memory (specific event)...")
        episodic_result = await client.propose_memory(
            content="User attended Python conference on 2025-01-15",
            category="a2p:professional",
            memory_type="episodic",
            confidence=0.95,
            context="Conference attendance record",
        )
        print(f"   Proposal ID: {episodic_result.get('proposal_id')}")
        print(f"   Status: {episodic_result.get('status')}\n")

        # 2. Semantic Memory - General knowledge and facts
        print("2. Proposing semantic memory (general knowledge)...")
        semantic_result = await client.propose_memory(
            content="User is a senior software engineer with 10 years of experience",
            category="a2p:professional",
            memory_type="semantic",
            confidence=0.9,
            context="Professional profile information",
        )
        print(f"   Proposal ID: {semantic_result.get('proposal_id')}")
        print(f"   Status: {semantic_result.get('status')}\n")

        # 3. Procedural Memory - Skills and how-to information
        print("3. Proposing procedural memory (skill/behavior)...")
        procedural_result = await client.propose_memory(
            content="User prefers to use async/await patterns in Python projects",
            category="a2p:professional",
            memory_type="procedural",
            confidence=0.85,
            context="Observed coding patterns",
        )
        print(f"   Proposal ID: {procedural_result.get('proposal_id')}")
        print(f"   Status: {procedural_result.get('status')}\n")

        # 4. Connection token mode (no DID needed)
        print("4. Using connection token mode (no DID required)...")
        token_mode_result = await client.propose_memory(
            content="User prefers dark mode UI",
            category="a2p:preferences",
            memory_type="semantic",
            confidence=0.8,
        )
        print(f"   Proposal ID: {token_mode_result.get('proposal_id')}")
        print(f"   Status: {token_mode_result.get('status')}\n")

        # 5. DID mode (explicit user DID)
        print("5. Using DID mode (explicit user DID)...")
        user_did = "did:a2p:user:gaugid:alice"
        did_mode_result = await client.propose_memory(
            content="User prefers morning meetings",
            user_did=user_did,
            category="a2p:preferences",
            memory_type="episodic",
            confidence=0.75,
        )
        print(f"   Proposal ID: {did_mode_result.get('proposal_id')}")
        print(f"   Status: {did_mode_result.get('status')}\n")

        print("=== Summary ===")
        print("Memory types:")
        print("  - episodic: Specific events and experiences")
        print("  - semantic: General knowledge and facts")
        print("  - procedural: Skills and behavioral patterns")
        print("\nModes:")
        print("  - Connection token mode: Omit user_did (recommended)")
        print("  - DID mode: Provide user_did for direct access")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
