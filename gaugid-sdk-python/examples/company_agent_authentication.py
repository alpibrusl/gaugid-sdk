"""
Company Agent Authentication Example

This example demonstrates how a company's AI agent would authenticate
and access user profiles. There are two main authentication flows:

1. A2P-Signature (Protocol-Native) - For protocol-compliant agents
2. Connection Tokens (OAuth) - For user-facing services

Both require user consent via the access request workflow.
"""

import asyncio
import base64
import os
from gaugid import (
    GaugidClient,
    generate_ed25519_keypair,
    generate_a2p_signature_header,
    private_key_to_pem,
)
from gaugid.logger import setup_logging

# Configure logging
setup_logging(level="INFO")

# Configuration
API_URL = os.getenv("GAUGID_API_URL", "https://api.alpha.gaugid.com")
COMPANY_NAMESPACE = "acme-corp"  # Your company namespace
AGENT_NAME = "travel-assistant"  # Your agent name


async def example_1_oauth_flow() -> None:
    """
    Example 1: OAuth Flow (Recommended for User-Facing Services)
    
    This is the simplest flow for company agents that interact with users
    through a web interface or mobile app.
    
    Flow:
    1. User visits your service
    2. User authorizes via OAuth (grants scopes)
    3. You receive a connection token
    4. You can access user's profile with granted scopes
    """
    print("=" * 70)
    print("Example 1: OAuth Flow (User-Facing Service)")
    print("=" * 70)
    print()
    
    from gaugid.auth import OAuthFlow
    
    # Step 1: Set up OAuth flow
    # In production, these would be from your service registration
    CLIENT_ID = os.getenv("GAUGID_CLIENT_ID", "acme-travel-service")
    CLIENT_SECRET = os.getenv("GAUGID_CLIENT_SECRET", "your-secret-here")
    REDIRECT_URI = os.getenv("GAUGID_REDIRECT_URI", "https://acme.com/oauth/callback")
    
    flow = OAuthFlow(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        api_url=API_URL,
    )
    
    # Step 2: Get authorization URL
    # Request the scopes your agent needs
    scopes = [
        "a2p:preferences",  # User preferences
        "a2p:interests",   # User interests
        "a2p:memories",    # User memories
    ]
    
    auth_url, state = flow.get_authorization_url(scopes=scopes)
    
    print("Step 1: User visits authorization URL")
    print(f"   {auth_url}\n")
    print("Step 2: User authorizes your service (grants scopes)")
    print("Step 3: User is redirected back with authorization code\n")
    
    # In a real app, you'd get this from the redirect
    print("(In production, you'd get the code from the redirect URL)")
    print("For this example, you would:")
    print("  1. Visit the auth_url above")
    print("  2. Authorize the service")
    print("  3. Copy the redirect URL")
    print("  4. Extract the code and exchange it for a token\n")
    
    # Simulated: Exchange code for token
    # In production:
    # redirect_url = request.args.get('redirect_uri')  # From OAuth callback
    # code = flow.parse_authorization_response(redirect_url, expected_state=state)
    # token_response = await flow.exchange_code(code=code, state=state)
    
    print("Step 4: Create client with connection token")
    print("   client = GaugidClient.from_oauth_response(token_response)\n")
    
    print("Step 5: Access user profile (no DID needed!)")
    print("   profile = await client.get_profile(scopes=['a2p:preferences'])\n")
    
    print("✅ Benefits:")
    print("   - User-friendly OAuth flow")
    print("   - No need to know user DIDs")
    print("   - User can revoke access anytime")
    print("   - Better privacy (DIDs not exposed)")
    
    await flow.close()


async def example_2_a2p_signature_flow() -> None:
    """
    Example 2: A2P-Signature Flow (Protocol-Native)
    
    This is for protocol-compliant agents that want to use the native
    a2p protocol authentication. This is more complex but provides
    better interoperability and decentralization.
    
    Flow:
    1. Generate Ed25519 keypair for your agent
    2. Register agent with public key
    3. User grants access via access request
    4. Sign requests with A2P-Signature header
    5. Access user profiles with granted scopes
    """
    print("\n" + "=" * 70)
    print("Example 2: A2P-Signature Flow (Protocol-Native)")
    print("=" * 70)
    print()
    
    # Step 1: Generate keypair for your agent
    print("Step 1: Generate Ed25519 keypair for your agent")
    private_key, public_key = generate_ed25519_keypair()
    public_key_b64 = base64.b64encode(public_key).decode("utf-8")
    private_key_pem = private_key_to_pem(private_key)
    
    print(f"   ✓ Generated keypair")
    print(f"   Private key (PEM): {private_key_pem[:50]}...")
    print(f"   Public key (base64): {public_key_b64[:50]}...")
    print(f"   ⚠️  Store private key securely! Never expose it.\n")
    
    # Step 2: Register agent
    # You need a connection token for registration (one-time setup)
    # This could be from a service account or admin token
    registration_token = os.getenv("GAUGID_REGISTRATION_TOKEN")
    
    if not registration_token:
        print("Step 2: Register agent (requires registration token)")
        print("   Set GAUGID_REGISTRATION_TOKEN environment variable")
        print("   Or use a connection token from OAuth for registration\n")
        print("   agent_did = f'did:a2p:agent:gaugid:{AGENT_NAME}'")
        print("   client = GaugidClient(")
        print("       connection_token=registration_token,")
        print("       api_url=API_URL,")
        print("       namespace=COMPANY_NAMESPACE,")
        print("   )")
        print("   result = await client.register_agent(")
        print("       agent_did=agent_did,")
        print("       name='Acme Travel Assistant',")
        print("       description='AI travel assistant for Acme Corp',")
        print("       public_key=public_key_b64,")
        print("   )\n")
    else:
        agent_did = f"did:a2p:agent:gaugid:{AGENT_NAME}"
        client = GaugidClient(
            connection_token=registration_token,
            api_url=API_URL,
            namespace=COMPANY_NAMESPACE,
        )
        
        try:
            print("Step 2: Register agent with public key")
            result = await client.register_agent(
                agent_did=agent_did,
                name="Acme Travel Assistant",
                description="AI travel assistant for Acme Corp",
                public_key=public_key_b64,
            )
            print(f"   ✓ Agent registered: {agent_did}")
            print(f"   Agent ID: {result.get('agent', {}).get('id')}\n")
        except Exception as e:
            print(f"   ⚠️  Registration failed: {e}\n")
        finally:
            await client.close()
    
    # Step 3: User grants access
    print("Step 3: User grants access to your agent")
    print("   The user must approve an access request from your agent.")
    print("   This can be done via:")
    print("   - Gaugid dashboard")
    print("   - Access request API endpoint")
    print("   - OAuth flow (which creates access automatically)\n")
    
    # Step 4: Use A2P-Signature for requests
    print("Step 4: Sign requests with A2P-Signature")
    print("   For each API request, generate an A2P-Signature header:")
    print()
    print("   header = generate_a2p_signature_header(")
    print("       agent_did=agent_did,")
    print("       private_key=private_key,")
    print("       method='GET',")
    print("       path='/a2p/v1/profile/did:a2p:user:gaugid:alice',")
    print("   )")
    print("   headers = {'Authorization': header}\n")
    
    print("✅ Benefits:")
    print("   - Protocol-native (works with any a2p implementation)")
    print("   - Decentralized (no token management)")
    print("   - No token expiration")
    print("   - Better for agent-to-agent communication")


async def example_3_access_request_workflow() -> None:
    """
    Example 3: Access Request Workflow
    
    This shows how a company agent requests access to a user's profile.
    The user must approve the request before the agent can access the profile.
    """
    print("\n" + "=" * 70)
    print("Example 3: Access Request Workflow")
    print("=" * 70)
    print()
    
    # You need a connection token (from OAuth or service account)
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    
    if not connection_token:
        print("This example requires a connection token.")
        print("Set GAUGID_CONNECTION_TOKEN environment variable.\n")
        print("Workflow:")
        print("1. Agent requests access with specific scopes")
        print("2. User receives notification (via dashboard or email)")
        print("3. User reviews and approves/denies the request")
        print("4. Agent can then access profile with granted scopes\n")
        return
    
    client = GaugidClient(
        connection_token=connection_token,
        api_url=API_URL,
        namespace=COMPANY_NAMESPACE,
    )
    
    try:
        # Step 1: Request access
        print("Step 1: Request access to user profile")
        user_did = os.getenv("GAUGID_USER_DID", "did:a2p:user:gaugid:NxWndPCpXvNW")
        
        scopes = [
            "a2p:preferences",  # User preferences
            "a2p:memories",     # User memories
        ]
        
        purpose = {
            "type": "travel_assistance",
            "description": "Access user preferences and memories to provide personalized travel recommendations",
            "legalBasis": "user_consent",
        }
        
        print(f"   Requesting scopes: {scopes}")
        print(f"   Purpose: {purpose['description']}\n")
        
        try:
            result = await client.request_access(
                user_did=user_did,
                scopes=scopes,
                purpose=purpose,
            )
            
            receipt_id = result.get("receiptId")
            granted_scopes = result.get("grantedScopes", [])
            denied_scopes = result.get("deniedScopes", [])
            
            print(f"   ✓ Access request submitted")
            print(f"   Receipt ID: {receipt_id}")
            print(f"   Granted scopes: {granted_scopes}")
            if denied_scopes:
                print(f"   Denied scopes: {denied_scopes}")
            print()
            
            # Step 2: Check if access is granted
            print("Step 2: Check if access is granted")
            print("   (In production, you'd poll or wait for user approval)\n")
            
            # Step 3: Access profile (if granted)
            if granted_scopes:
                print("Step 3: Access user profile with granted scopes")
                try:
                    profile = await client.get_profile(
                        user_did=user_did,
                        scopes=granted_scopes,
                    )
                    print(f"   ✓ Profile accessed successfully")
                    print(f"   Profile ID: {profile.get('id', 'N/A')}")
                    print(f"   Available scopes: {list(profile.get('scopes', {}).keys())}\n")
                except Exception as e:
                    print(f"   ⚠️  Access denied or pending: {e}\n")
            else:
                print("Step 3: Waiting for user approval...")
                print("   User must approve the access request via Gaugid dashboard\n")
        except Exception as e:
            print(f"   ⚠️  Access request failed: {e}\n")
    
    finally:
        await client.close()


async def example_4_multi_user_agent() -> None:
    """
    Example 4: Multi-User Agent Pattern
    
    How a single company agent serves multiple users, each with their own
    connection token or DID-based access.
    """
    print("\n" + "=" * 70)
    print("Example 4: Multi-User Agent Pattern")
    print("=" * 70)
    print()
    
    print("Pattern 1: Connection Token per User (Recommended)")
    print("-" * 70)
    print("Each user authorizes your service via OAuth")
    print("You store one connection token per user")
    print("When serving a user, use their connection token:\n")
    print("   # User 1")
    print("   client1 = GaugidClient(connection_token=user1_token)")
    print("   profile1 = await client1.get_profile(scopes=[...])")
    print()
    print("   # User 2")
    print("   client2 = GaugidClient(connection_token=user2_token)")
    print("   profile2 = await client2.get_profile(scopes=[...])\n")
    
    print("Pattern 2: DID-Based with A2P-Signature")
    print("-" * 70)
    print("Single agent with one keypair")
    print("Each user grants access to your agent DID")
    print("Use same agent credentials, different user DIDs:\n")
    print("   # Same agent, different users")
    print("   agent_did = 'did:a2p:agent:gaugid:my-agent'")
    print("   private_key = load_agent_private_key()")
    print()
    print("   # User 1")
    print("   header1 = generate_a2p_signature_header(")
    print("       agent_did, private_key, 'GET',")
    print("       f'/a2p/v1/profile/{user1_did}'")
    print("   )")
    print("   # Make request with header1")
    print()
    print("   # User 2")
    print("   header2 = generate_a2p_signature_header(")
    print("       agent_did, private_key, 'GET',")
    print("       f'/a2p/v1/profile/{user2_did}'")
    print("   )")
    print("   # Make request with header2\n")
    
    print("✅ Recommendation:")
    print("   Use Pattern 1 (Connection Token per User) for:")
    print("   - Better user experience")
    print("   - Easier token management")
    print("   - User can revoke access easily")
    print()
    print("   Use Pattern 2 (DID-Based) for:")
    print("   - Protocol compliance")
    print("   - Agent-to-agent communication")
    print("   - Cross-provider interoperability")


async def main() -> None:
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Company Agent Authentication Guide")
    print("=" * 70)
    print()
    print("This guide shows how a company's AI agent authenticates")
    print("and accesses user profiles with proper consent.\n")
    
    # Run examples
    await example_1_oauth_flow()
    await example_2_a2p_signature_flow()
    await example_3_access_request_workflow()
    await example_4_multi_user_agent()
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("For most company agents, use OAuth Flow (Example 1):")
    print("  1. User authorizes via OAuth")
    print("  2. You get a connection token")
    print("  3. Access user profile with granted scopes")
    print()
    print("For protocol-compliant agents, use A2P-Signature (Example 2):")
    print("  1. Register agent with public key")
    print("  2. User grants access via access request")
    print("  3. Sign requests with A2P-Signature header")
    print()
    print("Key Points:")
    print("  ✅ Users must grant access (consent is required)")
    print("  ✅ Access is scope-based (granular permissions)")
    print("  ✅ Users can revoke access anytime")
    print("  ✅ Both methods require user consent")
    print()


if __name__ == "__main__":
    asyncio.run(main())
