"""
Basic usage example for Gaugid SDK.

This example demonstrates how to use GaugidClient to interact with
Gaugid profiles and memories using both connection token mode and DID mode.
"""

import asyncio
from gaugid import GaugidClient


async def main() -> None:
    """Example: Basic usage of GaugidClient."""
    # Initialize client with connection token
    # You can get a connection token through the OAuth flow
    client = GaugidClient(connection_token="gaugid_conn_xxx")

    try:
        print("=== Connection Token Mode (Recommended) ===\n")
        
        # Connection token mode: No DID needed - profile resolved from token
        profile = await client.get_profile(
            scopes=["a2p:preferences", "a2p:interests"],
        )

        print(f"Profile (from token context):")
        print(f"  ID: {profile.get('id')}")
        print(f"  Type: {profile.get('profileType')}")

        # Propose a new memory with memory_type
        result = await client.propose_memory(
            content="User prefers morning meetings",
            category="a2p:preferences",
            memory_type="episodic",  # episodic, semantic, or procedural
            confidence=0.8,
        )

        print(f"\nMemory proposal created:")
        print(f"  Proposal ID: {result.get('proposal_id')}")
        print(f"  Status: {result.get('status')}")

        print("\n=== DID Mode (Direct Access) ===\n")
        
        # DID mode: Explicit user DID
        user_did = "did:a2p:user:gaugid:alice"
        profile = await client.get_profile(
            user_did=user_did,
            scopes=["a2p:preferences", "a2p:interests"],
        )

        print(f"Profile for {user_did}:")
        print(f"  ID: {profile.get('id')}")
        print(f"  Type: {profile.get('profileType')}")

        # Request access with purpose object
        access_result = await client.request_access(
            scopes=["a2p:episodic"],
            purpose={
                "type": "memory_retrieval",
                "description": "Need to access user memories for context",
                "legalBasis": "user_consent",
            },
        )

        print(f"\nAccess request result:")
        print(f"  Receipt ID: {access_result.get('receiptId')}")
        print(f"  Granted scopes: {access_result.get('grantedScopes')}")

    finally:
        # Always close the client when done
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
