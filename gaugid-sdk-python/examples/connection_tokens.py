"""
Connection token management example.

This example demonstrates how to manage connection tokens using
the ConnectionManager.
"""

import asyncio
from gaugid.connection import ConnectionManager, TokenStorage
from gaugid.types import ConnectionTokenInfo


async def main() -> None:
    """Example: Managing connection tokens."""
    # Initialize connection manager
    # Uses default storage at ~/.gaugid/tokens.json
    manager = ConnectionManager()

    # Example: Save a connection token
    connection_id = "my-service-connection"
    token_info = ConnectionTokenInfo(
        token="gaugid_conn_xxx",
        expires_at=1234567890,  # Unix timestamp
        scopes=["a2p:preferences", "a2p:interests"],
        connection_id="conn_123",
        user_did="did:a2p:user:gaugid:alice",
    )

    print(f"Saving connection: {connection_id}")
    manager.save_connection(connection_id, token_info)

    # Retrieve connection token
    token = manager.get_connection_token(connection_id)
    if token:
        print(f"Retrieved token: {token[:20]}...")
    else:
        print("Token not found or expired")

    # Get full connection info
    info = manager.get_connection_info(connection_id)
    if info:
        print(f"\nConnection info:")
        print(f"  Connection ID: {info.connection_id}")
        print(f"  User DID: {info.user_did}")
        print(f"  Scopes: {', '.join(info.scopes)}")

    # List all connections
    connections = manager.list_connections()
    print(f"\nAll connections: {', '.join(connections)}")

    # Check if token is expired
    is_expired = manager.storage.is_token_expired(connection_id)
    print(f"Token expired: {is_expired}")

    # Delete connection
    # manager.delete_connection(connection_id)
    # print(f"Deleted connection: {connection_id}")


if __name__ == "__main__":
    asyncio.run(main())
