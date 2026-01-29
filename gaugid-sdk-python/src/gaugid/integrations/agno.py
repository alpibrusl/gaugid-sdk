"""
GaugidDb - Agno MemoryManager database implementation using Gaugid SDK

This module provides a database implementation for Agno's MemoryManager that uses
Gaugid profiles as the persistent memory store. This allows Agno agents to store
and retrieve user memories using Gaugid profiles.

Based on: https://github.com/agno-agi/agno/blob/main/libs/agno/agno/memory/manager.py

Example:
    ```python
    from agno.memory.manager import MemoryManager
    from agno.models.openai import OpenAIChat
    from gaugid.integrations.agno import GaugidDb
    
    # Create database with Gaugid backend
    db = GaugidDb(
        connection_token="gaugid_conn_xxx",
        user_id="user-123"
    )
    
    # Use with Agno MemoryManager
    memory_manager = MemoryManager(
        model=OpenAIChat(id="gpt-4o"),
        db=db
    )
    ```
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import json

try:
    from agno.db.base import AsyncBaseDb, UserMemory
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    # Create minimal stubs for type checking
    class AsyncBaseDb:
        pass
    class UserMemory:
        def __init__(self, **kwargs):
            self.memory_id = kwargs.get("memory_id")
            self.user_id = kwargs.get("user_id")
            self.agent_id = kwargs.get("agent_id")
            self.team_id = kwargs.get("team_id")
            self.memory = kwargs.get("memory")
            self.topics = kwargs.get("topics", [])
            self.input = kwargs.get("input")
            self.updated_at = kwargs.get("updated_at")

from gaugid.client import GaugidClient


class GaugidDb(AsyncBaseDb):
    """
    Agno AsyncBaseDb implementation using Gaugid SDK.
    
    This database allows Agno MemoryManager to use Gaugid profiles as the
    persistent memory store. User memories are stored in Gaugid profiles
    and can be retrieved, updated, and deleted.
    
    Example:
        ```python
        from agno.memory.manager import MemoryManager
        from gaugid.integrations.agno import GaugidDb
        
        db = GaugidDb(
            connection_token="gaugid_conn_xxx",
            user_id="user-123"
        )
        
        memory_manager = MemoryManager(
            model=OpenAIChat(id="gpt-4o"),
            db=db
        )
        ```
    
    Based on: https://github.com/agno-agi/agno/blob/main/libs/agno/agno/memory/manager.py
    """
    
    def __init__(
        self,
        connection_token: str,
        user_id: Optional[str] = None,
        api_url: Optional[str] = None,
        memory_type: str = "semantic",
    ):
        """
        Initialize GaugidDb.
        
        Args:
            connection_token: Gaugid connection token for authentication
            user_id: Optional user ID (if not provided, uses token context)
            api_url: Optional Gaugid API URL (defaults to production)
            memory_type: Memory type to use ("episodic", "semantic", or "procedural")
        """
        if not AGNO_AVAILABLE:
            raise ImportError(
                "Agno is not installed. Install with: pip install gaugid[agno]"
            )
        
        super().__init__()
        self.client = GaugidClient(connection_token=connection_token, api_url=api_url)
        self.user_id = user_id or "default"
        self.memory_type = memory_type
        self._client_initialized = False
    
    async def _ensure_client_ready(self) -> None:
        """Ensure the client is ready."""
        if not self._client_initialized:
            self._client_initialized = True
    
    def _memory_id_to_category(self, memory_id: str) -> str:
        """Convert memory ID to Gaugid category."""
        return f"a2p:agno:memory:{self.user_id}:{memory_id}"
    
    def _category_to_memory_id(self, category: str) -> Optional[str]:
        """Extract memory ID from Gaugid category."""
        if not category.startswith(f"a2p:agno:memory:{self.user_id}:"):
            return None
        return category.split(":")[-1]
    
    def _topics_to_category_suffix(self, topics: Optional[List[str]]) -> str:
        """Convert topics to category suffix."""
        if not topics:
            return "general"
        return ".".join(topics)
    
    async def get_user_memories(
        self,
        user_id: Optional[str] = None,
    ) -> List[UserMemory]:
        """
        Get all user memories for a given user ID.
        
        Args:
            user_id: User ID (if not provided, uses self.user_id)
            
        Returns:
            List of UserMemory objects
        """
        await self._ensure_client_ready()
        
        user_id = user_id or self.user_id
        
        # Get profile with relevant scopes
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        
        # Find memories for this user
        memories = profile.get("memories", {}).get(self.memory_type, [])
        user_memories = []
        
        for memory in memories:
            category = memory.get("category", "")
            if category.startswith(f"a2p:agno:memory:{user_id}:"):
                memory_id = self._category_to_memory_id(category)
                if memory_id:
                    # Extract topics from category or metadata
                    topics = memory.get("metadata", {}).get("topics", [])
                    if not topics:
                        # Try to extract from category
                        parts = category.split(":")
                        if len(parts) > 5:
                            topics = parts[5].split(".")
                    
                    user_memory = UserMemory(
                        memory_id=memory_id,
                        user_id=user_id,
                        agent_id=memory.get("metadata", {}).get("agent_id"),
                        team_id=memory.get("metadata", {}).get("team_id"),
                        memory=memory.get("content", ""),
                        topics=topics if topics else [],
                        input=memory.get("context", ""),
                        updated_at=int(datetime.fromisoformat(
                            memory.get("updated_at", datetime.now().isoformat()).replace("Z", "+00:00")
                        ).timestamp()) if memory.get("updated_at") else None,
                    )
                    user_memories.append(user_memory)
        
        return user_memories
    
    async def upsert_user_memory(self, memory: UserMemory) -> None:
        """
        Upsert (insert or update) a user memory.
        
        Args:
            memory: UserMemory object to store
        """
        await self._ensure_client_ready()
        
        user_id = memory.user_id or self.user_id
        memory_id = memory.memory_id
        
        if not memory_id:
            from uuid import uuid4
            memory_id = str(uuid4())
            memory.memory_id = memory_id
        
        # Convert topics to category suffix
        category_base = f"a2p:agno:memory:{user_id}:{memory_id}"
        if memory.topics:
            category = f"{category_base}:{self._topics_to_category_suffix(memory.topics)}"
        else:
            category = category_base
        
        # Store in Gaugid
        await self.client.propose_memory(
            content=memory.memory,
            category=category,
            memory_type=self.memory_type,
            confidence=0.9,
            context=memory.input or f"Agno memory: {memory_id}",
        )
    
    async def delete_user_memory(
        self,
        memory_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Delete a user memory.
        
        Note: Gaugid doesn't support memory deletion via API yet.
        This is a no-op for now, but logs a warning.
        
        Args:
            memory_id: Memory ID to delete
            user_id: User ID (if not provided, uses self.user_id)
        """
        await self._ensure_client_ready()
        
        user_id = user_id or self.user_id
        
        # Note: Gaugid doesn't support deletion yet
        # In the future, this could mark the memory as deleted or remove it
        # For now, this is a no-op
        pass
    
    async def clear_memories(self, user_id: Optional[str] = None) -> None:
        """
        Clear all memories for a user.
        
        Note: Gaugid doesn't support bulk deletion yet.
        This is a no-op for now.
        
        Args:
            user_id: User ID (if not provided, uses self.user_id)
        """
        await self._ensure_client_ready()
        
        user_id = user_id or self.user_id
        
        # Note: Gaugid doesn't support bulk deletion yet
        # This is a no-op
        pass
    
    async def search_memories(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[UserMemory]:
        """
        Search for memories by query.
        
        Args:
            query: Search query string
            user_id: User ID (if not provided, uses self.user_id)
            limit: Maximum number of results
            
        Returns:
            List of matching UserMemory objects
        """
        await self._ensure_client_ready()
        
        user_id = user_id or self.user_id
        
        # Get all user memories
        all_memories = await self.get_user_memories(user_id=user_id)
        
        # Simple keyword matching (in production, use semantic search)
        matching_memories = []
        query_lower = query.lower()
        
        for memory in all_memories:
            memory_text = memory.memory.lower()
            topics_text = " ".join(memory.topics or []).lower()
            
            # Check if query matches memory content or topics
            if query_lower in memory_text or query_lower in topics_text:
                matching_memories.append(memory)
        
        # Sort by relevance (simple: count matches)
        matching_memories.sort(
            key=lambda m: (
                query_lower in m.memory.lower(),
                sum(1 for word in query_lower.split() if word in m.memory.lower()),
            ),
            reverse=True
        )
        
        return matching_memories[:limit]
    
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
