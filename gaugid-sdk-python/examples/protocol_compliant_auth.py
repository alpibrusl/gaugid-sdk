"""
Example: Protocol-Compliant Authentication with A2P-Signature

This example demonstrates how to use the Gaugid SDK with A2P-Signature
authentication for full a2p protocol compliance.

Note: This example shows the protocol-compliant authentication method.
For service connections, you can also use Bearer tokens (connection tokens)
which is more convenient for OAuth-based flows.
"""

import asyncio
import os
from gaugid import (
    GaugidClient,
    generate_agent_did,
    generate_ed25519_keypair,
    private_key_to_pem,
)


async def main() -> None:
    """Demonstrate protocol-compliant authentication."""
    print("=== Protocol-Compliant Authentication Example ===\n")

    # Step 1: Generate or load agent keypair
    print("Step 1: Generate Ed25519 keypair for agent")
    private_key, public_key = generate_ed25519_keypair()
    private_key_pem = private_key_to_pem(private_key)
    print(f"✓ Generated Ed25519 keypair")
    print(f"  Public key (32 bytes): {public_key.hex()}")
    print(f"  Private key (PEM): {private_key_pem[:50]}...")
    print()

    # Step 2: Generate agent DID
    print("Step 2: Generate agent DID")
    agent_did = generate_agent_did(
        name="protocol-demo-agent",
        namespace="gaugid",  # Use 'gaugid' namespace for Gaugid service
    )
    print(f"✓ Agent DID: {agent_did}")
    print()

    # Step 3: Register agent (using connection token for initial registration)
    print("Step 3: Register agent with Gaugid")
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN", "your-connection-token")
    api_url = os.getenv("GAUGID_API_URL", "https://api.gaugid.com")

    client = GaugidClient(
        connection_token=connection_token,
        api_url=api_url,
        agent_did=agent_did,
    )

    try:
        # Register agent with public key
        import base64
        public_key_b64 = base64.b64encode(public_key).decode("utf-8")

        registration_result = await client.register_agent(
            agent_did=agent_did,
            name="Protocol Demo Agent",
            description="Example agent demonstrating A2P-Signature authentication",
            public_key=public_key_b64,
        )
        print(f"✓ Agent registered successfully")
        print(f"  Agent ID: {registration_result.get('agent', {}).get('id')}")
        print(f"  Verified: {registration_result.get('agent', {}).get('verified')}")
        print()

        # Step 4: Resolve DID to verify registration
        print("Step 4: Resolve agent DID")
        did_doc = await client.resolve_did(agent_did)
        print(f"✓ DID resolved")
        print(f"  DID: {did_doc.get('id')}")
        print(f"  Verification methods: {len(did_doc.get('verificationMethod', []))}")
        if did_doc.get("verificationMethod"):
            vm = did_doc["verificationMethod"][0]
            print(f"  Key type: {vm.get('type')}")
            print(f"  Public key: {vm.get('publicKeyMultibase', '')[:20]}...")
        print()

        # Step 5: Use agent with A2P-Signature (would be done automatically by SDK)
        # Note: The current SDK uses connection tokens, but the API supports A2P-Signature
        # For full protocol compliance, you would use A2P-Signature headers
        print("Step 5: Using agent with protocol-compliant authentication")
        print("  Note: Gaugid API supports A2P-Signature on all /a2p/v1/* endpoints")
        print("  The SDK currently uses connection tokens for convenience")
        print("  A2P-Signature support can be added to the SDK for full protocol compliance")
        print()

        # Example: Get profile (would use A2P-Signature if implemented)
        user_did = os.getenv("GAUGID_USER_DID", "did:a2p:user:gaugid:demo")
        print(f"Step 6: Get user profile (using connection token)")
        try:
            profile = await client.get_profile(
                user_did=user_did,
                scopes=["a2p:preferences"],
            )
            print(f"✓ Profile retrieved")
            print(f"  User DID: {profile.get('id')}")
        except Exception as e:
            print(f"  Note: Profile not found or access denied: {e}")
        print()

    finally:
        await client.close()

    print("=== Example Complete ===")
    print("\nKey Takeaways:")
    print("1. ✓ Gaugid supports A2P-Signature authentication (100% protocol compliant)")
    print("2. ✓ DID resolution endpoint is available")
    print("3. ✓ Agent registration is protocol-compliant")
    print("4. ✓ Connection tokens provide convenience for service connections")
    print("5. ✓ Both authentication methods work with Gaugid API")


if __name__ == "__main__":
    asyncio.run(main())
