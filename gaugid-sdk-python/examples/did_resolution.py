"""
Example: DID Resolution

This example demonstrates how to resolve DIDs to their DID documents
using the a2p protocol DID resolution endpoint.
"""

import asyncio
import os
from gaugid import GaugidClient, generate_agent_did


async def main() -> None:
    """Demonstrate DID resolution."""
    print("=== DID Resolution Example ===\n")

    # Initialize client
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN", "your-connection-token")
    api_url = os.getenv("GAUGID_API_URL", "https://api.gaugid.com")

    client = GaugidClient(
        connection_token=connection_token,
        api_url=api_url,
    )

    try:
        # Example 1: Resolve an agent DID
        print("Example 1: Resolve agent DID")
        agent_did = generate_agent_did(
            name="example-agent",
            namespace="gaugid",
        )
        print(f"Resolving: {agent_did}")

        try:
            did_doc = await client.resolve_did(agent_did)
            print("✓ DID resolved successfully")
            print(f"  DID: {did_doc.get('id')}")
            print(f"  Context: {did_doc.get('@context')}")
            print(f"  Verification methods: {len(did_doc.get('verificationMethod', []))}")

            if did_doc.get("verificationMethod"):
                for vm in did_doc["verificationMethod"]:
                    print(f"    - {vm.get('id')}")
                    print(f"      Type: {vm.get('type')}")
                    print(f"      Controller: {vm.get('controller')}")

            if did_doc.get("authentication"):
                print(f"  Authentication: {did_doc.get('authentication')}")
            if did_doc.get("assertionMethod"):
                print(f"  Assertion method: {did_doc.get('assertionMethod')}")
        except Exception as e:
            print(f"  ✗ Resolution failed: {e}")
            print("  Note: DID may not be registered yet")
        print()

        # Example 2: Resolve a user DID
        print("Example 2: Resolve user DID")
        user_did = os.getenv("GAUGID_USER_DID", "did:a2p:user:gaugid:demo")
        print(f"Resolving: {user_did}")

        try:
            did_doc = await client.resolve_did(user_did)
            print("✓ DID resolved successfully")
            print(f"  DID: {did_doc.get('id')}")
            print(f"  Verification methods: {len(did_doc.get('verificationMethod', []))}")
        except Exception as e:
            print(f"  ✗ Resolution failed: {e}")
            print("  Note: User DID may not exist or may not be registered")
        print()

        print("=== Example Complete ===")
        print("\nKey Points:")
        print("1. ✓ DID resolution is a public endpoint (no auth required)")
        print("2. ✓ Returns W3C-compliant DID documents")
        print("3. ✓ Supports both agent and user DIDs")
        print("4. ✓ Used for verifying signatures in A2P-Signature authentication")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
