"""
User-friendly login example for Gaugid SDK.

This example demonstrates the improved user experience:
1. Login via OAuth
2. Automatically get user DIDs from account
3. Select a profile
4. Use the profile without manually specifying DIDs
"""

import asyncio
from gaugid import GaugidClient
from gaugid.auth import OAuthFlow


async def main() -> None:
    """Example: User-friendly login and profile selection."""
    # Step 1: OAuth Login
    print("🔐 Step 1: OAuth Login")
    flow = OAuthFlow(
        client_id="my-service",
        client_secret="my-secret",
        redirect_uri="https://myapp.com/callback",
    )
    
    # Get authorization URL
    auth_url, state = flow.get_authorization_url(
        scopes=["a2p:preferences", "a2p:interests", "a2p:memories"]
    )
    
    print(f"Please visit: {auth_url}")
    print("After authorization, you'll be redirected back with a code.")
    
    # In a real app, you'd get this from the redirect
    redirect_url = input("Enter the redirect URL: ").strip()
    
    # Parse and exchange code
    code = flow.parse_authorization_response(redirect_url, expected_state=state)
    token_response = await flow.exchange_code(code=code, state=state)
    
    print(f"✅ Logged in! User DID: {token_response.user_did}")
    if token_response.profiles:
        print(f"   Available profiles: {len(token_response.profiles)}")
    
    # Step 2: Create client from OAuth response
    # This automatically sets up user account information
    print("\n📋 Step 2: Create client with user account info")
    client = GaugidClient.from_oauth_response(token_response)
    
    # Step 3: List available profiles
    print("\n📝 Step 3: List available profiles")
    profiles = await client.list_profiles()
    
    if not profiles:
        print("No profiles available.")
        return
    
    print(f"Found {len(profiles)} profile(s):")
    for i, profile in enumerate(profiles):
        profile_did = profile.get("did", "Unknown")
        profile_name = profile.get("name", "Unnamed")
        print(f"  {i+1}. {profile_name} ({profile_did})")
    
    # Step 4: Select a profile (or use auto-selected if only one)
    print("\n✅ Step 4: Select profile")
    if len(profiles) > 1:
        # Multiple profiles - let user choose
        choice = input(f"Select profile (1-{len(profiles)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(profiles):
                selected_did = profiles[idx].get("did")
                if selected_did:
                    client.select_profile(selected_did)
                    print(f"✅ Selected: {profiles[idx].get('name', 'Profile')}")
            else:
                print("Invalid choice, using first profile")
                client.select_profile(profiles[0].get("did", ""))
        except ValueError:
            print("Invalid input, using first profile")
            client.select_profile(profiles[0].get("did", ""))
    else:
        # Only one profile - auto-selected
        print(f"✅ Auto-selected: {profiles[0].get('name', 'Profile')}")
    
    # Step 5: Use the selected profile (no need to specify DID!)
    print("\n🚀 Step 5: Use the selected profile")
    try:
        # Get profile without specifying DID (uses connection token mode)
        profile = await client.get_current_profile(
            scopes=["a2p:preferences", "a2p:interests"]
        )
        
        print(f"Profile loaded:")
        print(f"  ID: {profile.get('id')}")
        print(f"  Type: {profile.get('profileType')}")
        
        # Propose memory without specifying DID (connection token mode)
        # memory_type can be: "episodic", "semantic", or "procedural"
        result = await client.propose_memory_to_current(
            content="User prefers morning meetings",
            category="a2p:preferences",
            memory_type="episodic",  # episodic, semantic, or procedural
            confidence=0.8,
        )
        
        print(f"\n✅ Memory proposed!")
        print(f"   Proposal ID: {result.get('proposal_id')}")
        print(f"   Status: {result.get('status')}")
        
        # You can also use connection token mode directly (no profile selection needed)
        print("\n💡 Tip: You can also use connection token mode directly:")
        print("   profile = await client.get_profile(scopes=[...])")
        print("   result = await client.propose_memory(content=..., memory_type='episodic')")
        
    finally:
        await client.close()
        await flow.close()


if __name__ == "__main__":
    asyncio.run(main())
