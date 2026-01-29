"""
GaugidSession - OpenAI Agents SDK Session implementation using Gaugid SDK

This module provides a Session implementation for OpenAI Agents SDK that uses
Gaugid profiles as the persistent session store. This allows OpenAI agents to
maintain conversation history across sessions using Gaugid profiles.

Based on: https://openai.github.io/openai-agents-python/ref/memory/

Example:
    ```python
    from openai import OpenAI
    from openai.agents import Agent
    from gaugid.integrations.openai import GaugidSession
    
    # Create session with Gaugid backend
    session = GaugidSession(
        session_id="user-123",
        connection_token="gaugid_conn_xxx"
    )
    
    # Use with OpenAI agent
    agent = Agent(
        model="gpt-4o",
        session=session
    )
    ```
"""

from typing import Optional, List, Any, Dict
from datetime import datetime
import json

try:
    from openai.agents.memory.session import Session
    from openai.agents.memory.items import TResponseInputItem
    OPENAI_AGENTS_AVAILABLE = True
except ImportError:
    OPENAI_AGENTS_AVAILABLE = False
    # Create minimal stubs for type checking
    class Session:
        session_id: str
        async def get_items(self, limit: Optional[int] = None) -> List[Any]:
            pass
        async def add_items(self, items: List[Any]) -> None:
            pass
        async def pop_item(self) -> Any:
            pass
        async def clear_session(self) -> None:
            pass
    TResponseInputItem = Dict[str, Any]

from gaugid.client import GaugidClient


class GaugidSession(Session):
    """
    OpenAI Agents SDK Session implementation using Gaugid SDK.
    
    This session allows OpenAI agents to use Gaugid profiles as their
    persistent session store. Conversation history is stored as memories
    in the user's Gaugid profile, allowing agents to maintain context
    across sessions.
    
    Example:
        ```python
        from openai.agents import Agent
        from gaugid.integrations.openai import GaugidSession
        
        session = GaugidSession(
            session_id="user-123",
            connection_token="gaugid_conn_xxx"
        )
        
        agent = Agent(
            model="gpt-4o",
            session=session
        )
        ```
    
    Based on: https://openai.github.io/openai-agents-python/ref/memory/
    """
    
    def __init__(
        self,
        session_id: str,
        connection_token: str,
        api_url: Optional[str] = None,
        memory_type: str = "episodic",
    ):
        """
        Initialize GaugidSession.
        
        Args:
            session_id: Unique session identifier
            connection_token: Gaugid connection token for authentication
            api_url: Optional Gaugid API URL (defaults to production)
            memory_type: Memory type to use ("episodic", "semantic", or "procedural")
        """
        if not OPENAI_AGENTS_AVAILABLE:
            raise ImportError(
                "OpenAI Agents SDK is not installed. Install with: pip install gaugid[openai]"
            )
        
        self.session_id = session_id
        self.client = GaugidClient(connection_token=connection_token, api_url=api_url)
        self.memory_type = memory_type
        self._client_initialized = False
    
    async def _ensure_client_ready(self) -> None:
        """Ensure the client is ready."""
        if not self._client_initialized:
            self._client_initialized = True
    
    def _session_to_category(self) -> str:
        """Convert session ID to Gaugid category."""
        return f"a2p:openai:session:{self.session_id}"
    
    async def get_items(self, limit: Optional[int] = None) -> List[TResponseInputItem]:
        """
        Retrieve conversation history for this session.
        
        Args:
            limit: Maximum number of items to retrieve. If None, retrieves all items.
                  When specified, returns the latest N items in chronological order.
        
        Returns:
            List of input items representing the conversation history
        """
        await self._ensure_client_ready()
        
        # Get profile with relevant scopes
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        
        # Find memories for this session
        memories = profile.get("memories", {}).get(self.memory_type, [])
        category = self._session_to_category()
        
        session_memories = []
        for memory in memories:
            if memory.get("category") == category:
                # Extract items from memory content
                content = memory.get("content", "")
                try:
                    # Try to parse as JSON (stored as JSON array)
                    items = json.loads(content)
                    if isinstance(items, list):
                        session_memories = items  # Use the stored list
                        break  # Should only be one memory per session
                    else:
                        # Single item stored as object
                        session_memories = [items]
                        break
                except json.JSONDecodeError:
                    # Fallback: treat as single item
                    if content and content != "[]":
                        session_memories = [{"content": content}]
                    break
        
        # Sort by timestamp if available (oldest first for chronological order)
        if session_memories and isinstance(session_memories[0], dict):
            # Try to sort by timestamp
            try:
                session_memories.sort(
                    key=lambda x: x.get("timestamp", 0) if isinstance(x, dict) else 0
                )
            except Exception:
                pass
        
        # Apply limit (return latest N items in chronological order)
        if limit is not None and len(session_memories) > limit:
            # Get the last N items (most recent)
            session_memories = session_memories[-limit:]
        
        return session_memories  # type: ignore
    
    async def add_items(self, items: List[TResponseInputItem]) -> None:
        """
        Add new items to the conversation history.
        
        Args:
            items: List of input items to add to the history
        """
        await self._ensure_client_ready()
        
        if not items:
            return
        
        # Get existing items
        existing_items = await self.get_items()
        
        # Add new items
        all_items = existing_items + items
        
        # Store as JSON in memory
        category = self._session_to_category()
        content = json.dumps(all_items, default=str)
        
        # Propose memory (this will create or update)
        await self.client.propose_memory(
            content=content,
            category=category,
            memory_type=self.memory_type,
            confidence=0.9,
            context=f"OpenAI Agents SDK session: {self.session_id}",
        )
    
    async def pop_item(self) -> TResponseInputItem | None:
        """
        Remove and return the most recent item from the session.
        
        Returns:
            The most recent item if it exists, None if the session is empty
        """
        await self._ensure_client_ready()
        
        items = await self.get_items(limit=1)
        if not items:
            return None
        
        # Get the last item
        last_item = items[-1]
        
        # Remove it from the list
        all_items = await self.get_items()
        if all_items:
            all_items.pop()
            
            # Update memory
            category = self._session_to_category()
            content = json.dumps(all_items, default=str)
            
            await self.client.propose_memory(
                content=content,
                category=category,
                memory_type=self.memory_type,
                confidence=0.9,
                context=f"OpenAI Agents SDK session: {self.session_id}",
            )
        
        return last_item  # type: ignore
    
    async def clear_session(self) -> None:
        """Clear all items for this session."""
        await self._ensure_client_ready()
        
        # Note: Gaugid doesn't support memory deletion yet
        # We'll create an empty memory to "clear" the session
        category = self._session_to_category()
        
        await self.client.propose_memory(
            content="[]",  # Empty JSON array
            category=category,
            memory_type=self.memory_type,
            confidence=0.9,
            context=f"OpenAI Agents SDK session cleared: {self.session_id}",
        )
    
    async def close(self) -> None:
        """Close the Gaugid client and cleanup resources."""
        if self._client_initialized:
            await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client_ready()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
