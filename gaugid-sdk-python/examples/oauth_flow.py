"""
OAuth flow example for Gaugid SDK.

This example demonstrates how to implement the OAuth 2.0 authorization
code flow to obtain a connection token.
"""

import asyncio
from gaugid.auth import OAuthFlow


async def main() -> None:
    """Example: OAuth flow for obtaining connection token."""
    # Initialize OAuth flow
    flow = OAuthFlow(
        client_id="my-service",
        client_secret="my-secret",
        redirect_uri="https://myapp.com/callback",
        api_url="https://api.gaugid.com",  # Optional, defaults to production
    )

    try:
        # Step 1: Get authorization URL
        scopes = ["a2p:preferences", "a2p:interests", "a2p:memories"]
        auth_url, state = flow.get_authorization_url(scopes=scopes)

        print("Step 1: Redirect user to authorization URL")
        print(f"URL: {auth_url}")
        print(f"State: {state}")
        print("\nUser will authorize and be redirected back to your callback URL")
        print("with a 'code' parameter.\n")

        # Step 2: In a real application, you would receive the redirect
        # For this example, we'll simulate it
        print("Step 2: Parse the redirect URL")
        redirect_url = input(
            "Enter the redirect URL (or press Enter to skip): "
        ).strip()

        if not redirect_url:
            print("Skipping token exchange...")
            return

        # Parse the authorization code from the redirect URL
        code = flow.parse_authorization_response(redirect_url, expected_state=state)
        print(f"Authorization code: {code}\n")

        # Step 3: Exchange code for token
        print("Step 3: Exchange authorization code for connection token")
        token_response = await flow.exchange_code(code=code, state=state)

        print("Token exchange successful!")
        print(f"  Connection Token: {token_response.access_token[:20]}...")
        print(f"  Expires in: {token_response.expires_in} seconds")
        print(f"  Scopes: {token_response.scope}")
        if token_response.user_did:
            print(f"  User DID: {token_response.user_did}")
        if token_response.profiles:
            print(f"  Profiles: {len(token_response.profiles)}")

        # Now you can use this token with GaugidClient
        print("\nYou can now use this connection token with GaugidClient:")
        print(f"  client = GaugidClient(connection_token='{token_response.access_token}')")

    finally:
        await flow.close()


if __name__ == "__main__":
    asyncio.run(main())
