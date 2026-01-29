"""
User-Facing Application Example

This example demonstrates how to build a user-facing application (UI, profile
management, etc.) using connection tokens via OAuth flow.

Use Case: Web apps, mobile apps, dashboards, profile management tools
"""

import asyncio
from gaugid import GaugidClient
from gaugid.auth import OAuthFlow


async def main() -> None:
    """Example: User-facing application with OAuth."""
    print("=== User-Facing Application Example ===\n")
    print("Use Case: Web app, mobile app, or dashboard\n")
    
    # Step 1: OAuth Flow (User authorizes your app)
    print("Step 1: User OAuth Authorization")
    flow = OAuthFlow(
        client_id="my-web-app",
        client_secret="my-secret",
        redirect_uri="https://myapp.com/callback",
    )
    
    # Get authorization URL
    auth_url, state = flow.get_authorization_url(
        scopes=["a2p:preferences", "a2p:interests", "a2p:episodic"]
    )
    
    print(f"Redirect user to: {auth_url}")
    print("User will authorize and be redirected back with a code.\n")
    
    # In a real app, you'd get this from the redirect
    redirect_url = input("Enter redirect URL (or press Enter to skip): ").strip()
    if not redirect_url:
        print("Skipping OAuth flow...")
        return
    
    # Exchange code for token
    code = flow.parse_authorization_response(redirect_url, expected_state=state)
    token_response = await flow.exchange_code(code=code, state=state)
    
    print(f"✅ User authorized! Connection token obtained.\n")
    
    # Step 2: Create client with connection token
    print("Step 2: Initialize client with connection token")
    client = GaugidClient.from_oauth_response(token_response)
    print("✅ Client initialized (user DID and profiles loaded)\n")
    
    # Step 3: Use connection token mode (no DID needed!)
    print("Step 3: Access user profile (connection token mode)")
    try:
        # Get profile - no DID needed, resolved from token
        profile = await client.get_profile(
            scopes=["a2p:preferences", "a2p:interests"]
        )
        
        print(f"✅ Profile loaded:")
        print(f"   ID: {profile.get('id')}")
        print(f"   Type: {profile.get('profileType')}")
        print(f"   Preferences: {profile.get('common', {}).get('preferences', {})}\n")
        
        # Create/update profile data
        print("Step 4: Propose new memory (connection token mode)")
        memory_result = await client.propose_memory(
            content="User prefers dark mode UI",
            category="a2p:preferences",
            memory_type="semantic",
            confidence=0.9,
        )
        print(f"✅ Memory proposed: {memory_result.get('proposal_id')}\n")
        
        # Request additional access
        print("Step 5: Request additional access")
        access_result = await client.request_access(
            scopes=["a2p:episodic"],
            purpose={
                "type": "memory_retrieval",
                "description": "Need to access user memories for personalization",
                "legalBasis": "user_consent",
            },
        )
        print(f"✅ Access granted: {access_result.get('grantedScopes')}\n")
        
    finally:
        await client.close()
        await flow.close()
    
    print("=== Summary ===")
    print("✅ Connection tokens are perfect for user-facing applications:")
    print("   - User authorizes via OAuth")
    print("   - No need to know user DIDs")
    print("   - Easy to revoke (user can revoke access)")
    print("   - Better privacy (DIDs not exposed)")
    print("\n💡 For AI agents, use A2P-Signature (see protocol_compliant_auth.py)")


if __name__ == "__main__":
    asyncio.run(main())
