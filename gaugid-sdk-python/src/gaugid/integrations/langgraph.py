"""
GaugidStore - LangGraph BaseStore implementation using Gaugid SDK

This module provides a BaseStore implementation for LangGraph that uses
Gaugid profiles as the persistent key-value store. This allows LangGraph
agents to use Gaugid for long-term memory that persists across threads
and conversations.

Based on: https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint/langgraph/store/base/__init__.py

Example:
    ```python
    from langgraph.graph import StateGraph
    from langgraph.checkpoint import MemorySaver
    from gaugid.integrations.langgraph import GaugidStore
    
    # Create store
    store = GaugidStore(
        connection_token="gaugid_conn_xxx",
        namespace_prefix=("langgraph", "my-app")
    )
    
    # Use with LangGraph
    graph = StateGraph(...)
    app = graph.compile(checkpointer=store)
    ```
"""

from datetime import datetime
from typing import Any, Optional, Literal

try:
    from langgraph.store.base import (
        BaseStore,
        Item,
        SearchItem,
        GetOp,
        PutOp,
        SearchOp,
        ListNamespacesOp,
        Op,
        NOT_PROVIDED,
    )
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Create minimal stubs for type checking
    class BaseStore:
        pass
    class Item:
        pass
    class SearchItem:
        pass
    class GetOp:
        pass
    class PutOp:
        pass
    class SearchOp:
        pass
    class ListNamespacesOp:
        pass
    class Op:
        pass
    NOT_PROVIDED = None

from gaugid.client import GaugidClient


class GaugidStore(BaseStore):
    """
    LangGraph BaseStore implementation using Gaugid SDK.
    
    This store allows LangGraph agents to use Gaugid profiles as their
    persistent key-value store. It implements the BaseStore interface
    and integrates seamlessly with LangGraph's checkpoint system.
    
    Namespaces are mapped to Gaugid memory categories, and items are
    stored as memories with appropriate metadata.
    
    Example:
        ```python
        from langgraph.graph import StateGraph
        from gaugid.integrations.langgraph import GaugidStore
        
        store = GaugidStore(
            connection_token="gaugid_conn_xxx",
            namespace_prefix=("langgraph", "my-app")
        )
        
        graph = StateGraph(...)
        app = graph.compile(checkpointer=store)
        ```
    
    Based on: https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint/langgraph/store/base/__init__.py
    """
    
    def __init__(
        self,
        connection_token: str,
        namespace_prefix: tuple[str, ...] = ("langgraph",),
        api_url: Optional[str] = None,
        memory_type: str = "episodic",
    ):
        """
        Initialize GaugidStore.
        
        Args:
            connection_token: Gaugid connection token for authentication
            namespace_prefix: Prefix for all namespaces (default: ("langgraph",))
            api_url: Optional Gaugid API URL (defaults to production)
            memory_type: Memory type to use for storage ("episodic", "semantic", or "procedural")
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraph is not installed. Install with: pip install gaugid[langgraph]"
            )
        
        self.client = GaugidClient(connection_token=connection_token, api_url=api_url)
        self.namespace_prefix = namespace_prefix
        self.memory_type = memory_type
        self._client_initialized = False
    
    async def _ensure_client_ready(self) -> None:
        """Ensure the client is ready."""
        if not self._client_initialized:
            self._client_initialized = True
    
    def _namespace_to_category(self, namespace: tuple[str, ...]) -> str:
        """Convert namespace tuple to Gaugid category string."""
        full_namespace = self.namespace_prefix + namespace
        return "a2p:store:" + ".".join(full_namespace)
    
    def _category_to_namespace(self, category: str) -> tuple[str, ...]:
        """Convert Gaugid category string to namespace tuple."""
        if not category.startswith("a2p:store:"):
            return tuple()
        parts = category.replace("a2p:store:", "").split(".")
        # Remove namespace_prefix parts
        prefix_parts = list(self.namespace_prefix)
        if parts[:len(prefix_parts)] == prefix_parts:
            return tuple(parts[len(prefix_parts):])
        return tuple(parts)
    
    def _key_to_memory_key(self, namespace: tuple[str, ...], key: str) -> str:
        """Convert namespace and key to a unique memory identifier."""
        category = self._namespace_to_category(namespace)
        return f"{category}:{key}"
    
    async def abatch(self, ops: list[Op]) -> list[Any]:
        """
        Execute a batch of operations.
        
        Args:
            ops: List of operations (GetOp, PutOp, SearchOp, ListNamespacesOp)
            
        Returns:
            List of results corresponding to each operation
        """
        await self._ensure_client_ready()
        
        results = []
        for op in ops:
            if isinstance(op, GetOp):
                result = await self.aget(op.namespace, op.key, op.refresh_ttl)
                results.append(result)
            elif isinstance(op, PutOp):
                ttl_value = getattr(op, 'ttl', NOT_PROVIDED)
                await self.aput(
                    op.namespace,
                    op.key,
                    op.value,
                    op.index,
                    ttl=ttl_value,
                )
                results.append(None)
            elif isinstance(op, SearchOp):
                result = await self.asearch(
                    op.namespace_prefix,
                    op.filter,
                    op.limit,
                    op.offset,
                    op.query,
                    op.refresh_ttl,
                )
                results.append(result)
            elif isinstance(op, ListNamespacesOp):
                result = await self.alist_namespaces(
                    prefix=op.match_conditions[0].path if op.match_conditions else None,
                    max_depth=op.max_depth,
                    limit=op.limit,
                    offset=op.offset,
                )
                results.append(result)
            else:
                raise ValueError(f"Unsupported operation type: {type(op)}")
        
        return results
    
    async def aget(
        self,
        namespace: tuple[str, ...],
        key: str,
        refresh_ttl: bool = True,
    ) -> Optional[Item]:
        """
        Retrieve an item by namespace and key.
        
        Args:
            namespace: Hierarchical path for the item
            key: Unique identifier within the namespace
            refresh_ttl: Whether to refresh TTL (ignored for Gaugid)
            
        Returns:
            Item if found, None otherwise
        """
        await self._ensure_client_ready()
        
        # Get profile with relevant scopes
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        
        # Search for memory with matching key
        memories = profile.get("memories", {}).get(self.memory_type, [])
        memory_key = self._key_to_memory_key(namespace, key)
        
        for memory in memories:
            # Check if this memory matches our key
            memory_id = memory.get("id") or memory.get("proposal_id", "")
            category = memory.get("category", "")
            
            # Match by category and key in content or metadata
            if category == self._namespace_to_category(namespace):
                # Check if key is in content or stored as metadata
                content = memory.get("content", "")
                if key in content or memory_id.endswith(key):
                    # Reconstruct Item from memory
                    value = {
                        "content": content,
                        "category": category,
                        "memory_type": self.memory_type,
                        **memory.get("metadata", {}),
                    }
                    
                    created_at = memory.get("created_at")
                    updated_at = memory.get("updated_at", created_at)
                    
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    
                    return Item(
                        value=value,
                        key=key,
                        namespace=namespace,
                        created_at=created_at or datetime.now(),
                        updated_at=updated_at or datetime.now(),
                    )
        
        return None
    
    async def asearch(
        self,
        namespace_prefix: tuple[str, ...],
        filter: Optional[dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        query: Optional[str] = None,
        refresh_ttl: bool = True,
    ) -> list[SearchItem]:
        """
        Search for items within a namespace prefix.
        
        Args:
            namespace_prefix: Prefix to search within
            filter: Key-value filters (not fully supported yet)
            limit: Maximum number of results
            offset: Number of results to skip
            query: Natural language search query (not supported yet)
            refresh_ttl: Whether to refresh TTL (ignored)
            
        Returns:
            List of SearchItem objects
        """
        await self._ensure_client_ready()
        
        # Get profile
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        
        # Filter memories by namespace
        memories = profile.get("memories", {}).get(self.memory_type, [])
        target_category = self._namespace_to_category(namespace_prefix)
        
        matching_memories = []
        for memory in memories:
            category = memory.get("category", "")
            if category.startswith(target_category):
                matching_memories.append(memory)
        
        # Apply filters if provided
        if filter:
            filtered = []
            for memory in matching_memories:
                matches = True
                for key, value in filter.items():
                    if key in memory.get("metadata", {}):
                        if memory["metadata"][key] != value:
                            matches = False
                            break
                if matches:
                    filtered.append(memory)
            matching_memories = filtered
        
        # Apply pagination
        matching_memories = matching_memories[offset:offset + limit]
        
        # Convert to SearchItem
        results = []
        for memory in matching_memories:
            category = memory.get("category", "")
            namespace = self._category_to_namespace(category)
            
            # Extract key from memory
            memory_id = memory.get("id") or memory.get("proposal_id", "")
            key = memory_id.split(":")[-1] if ":" in memory_id else memory_id
            
            value = {
                "content": memory.get("content", ""),
                "category": category,
                "memory_type": self.memory_type,
                **memory.get("metadata", {}),
            }
            
            created_at = memory.get("created_at")
            updated_at = memory.get("updated_at", created_at)
            
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            
            results.append(
                SearchItem(
                    namespace=namespace,
                    key=key,
                    value=value,
                    created_at=created_at or datetime.now(),
                    updated_at=updated_at or datetime.now(),
                    score=None,  # Gaugid doesn't provide relevance scores yet
                )
            )
        
        return results
    
    async def aput(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict[str, Any],
        index: Literal[False] | list[str] | None = None,
        *,
        ttl: float | None | Any = NOT_PROVIDED,
    ) -> None:
        """
        Store or update an item.
        
        Args:
            namespace: Hierarchical path for the item
            key: Unique identifier within the namespace
            value: Dictionary containing the item's data
            index: Indexing configuration (ignored for Gaugid)
            ttl: Time to live in minutes (not supported by Gaugid)
        """
        await self._ensure_client_ready()
        
        if ttl not in (NOT_PROVIDED, None):
            # TTL not supported by Gaugid, but we'll proceed
            pass
        
        # Convert value to memory content
        content = value.get("content", str(value))
        category = self._namespace_to_category(namespace)
        
        # Store as memory proposal
        await self.client.propose_memory(
            content=content,
            category=category,
            memory_type=self.memory_type,
            confidence=0.8,
            context=f"LangGraph store item: {key}",
        )
    
    async def adelete(self, namespace: tuple[str, ...], key: str) -> None:
        """
        Delete an item.
        
        Note: Gaugid doesn't support direct deletion of memories.
        This is a no-op for now.
        
        Args:
            namespace: Hierarchical path for the item
            key: Unique identifier within the namespace
        """
        await self._ensure_client_ready()
        # Gaugid doesn't support memory deletion via API
        # This is a no-op
        pass
    
    async def alist_namespaces(
        self,
        *,
        prefix: Optional[tuple[str, ...]] = None,
        suffix: Optional[tuple[str, ...]] = None,
        max_depth: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[tuple[str, ...]]:
        """
        List namespaces in the store.
        
        Args:
            prefix: Filter namespaces that start with this path
            suffix: Filter namespaces that end with this path
            max_depth: Return namespaces up to this depth
            limit: Maximum number of namespaces to return
            offset: Number of namespaces to skip
            
        Returns:
            List of namespace tuples
        """
        await self._ensure_client_ready()
        
        # Get profile
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        
        # Extract unique namespaces from memories
        memories = profile.get("memories", {}).get(self.memory_type, [])
        namespaces = set()
        
        for memory in memories:
            category = memory.get("category", "")
            if category.startswith("a2p:store:"):
                namespace = self._category_to_namespace(category)
                if namespace:
                    # Apply prefix filter
                    if prefix:
                        if not namespace[:len(prefix)] == prefix:
                            continue
                    # Apply suffix filter
                    if suffix:
                        if not namespace[-len(suffix):] == suffix:
                            continue
                    # Apply max_depth
                    if max_depth:
                        namespace = namespace[:max_depth]
                    namespaces.add(namespace)
        
        # Sort and paginate
        sorted_namespaces = sorted(list(namespaces))
        return sorted_namespaces[offset:offset + limit]
    
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
