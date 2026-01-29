"""
GaugidMemoryBlock - LlamaIndex BaseMemoryBlock implementation using Gaugid SDK

This module provides a BaseMemoryBlock implementation for LlamaIndex that uses
Gaugid profiles as the persistent memory store. This allows LlamaIndex agents to
store and retrieve long-term memories using Gaugid profiles.

Based on: https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/memory/memory.py

Example:
    ```python
    from llama_index.core.memory import Memory
    from llama_index.core.memory.memory import BaseMemoryBlock
    from gaugid.integrations.llama_index import GaugidMemoryBlock
    
    # Create memory block with Gaugid backend
    memory_block = GaugidMemoryBlock(
        name="user_preferences",
        connection_token="gaugid_conn_xxx",
        memory_type="semantic"
    )
    
    # Use with LlamaIndex Memory
    memory = Memory(
        memory_blocks=[memory_block],
        session_id="user-123"
    )
    ```
"""

from __future__ import annotations

from typing import Optional, List, Any, Union
from datetime import datetime
import json

try:
    from llama_index.core.memory.memory import BaseMemoryBlock
    from llama_index.core.base.llms.types import ChatMessage
    LLAMA_INDEX_AVAILABLE = True
except ImportError:
    LLAMA_INDEX_AVAILABLE = False
    # Create minimal stubs for type checking
    # Use a generic base class that supports subscripting
    from typing import Generic, TypeVar
    T = TypeVar('T')
    class BaseMemoryBlock(Generic[T]):
        pass
    class ChatMessage:
        pass

from gaugid.client import GaugidClient


class GaugidMemoryBlock(BaseMemoryBlock[str]):
    """
    LlamaIndex BaseMemoryBlock implementation using Gaugid SDK.
    
    This memory block allows LlamaIndex agents to use Gaugid profiles as their
    persistent memory store. Memory blocks store long-term knowledge that persists
    across conversations and can be retrieved when needed.
    
    Example:
        ```python
        from llama_index.core.memory import Memory
        from gaugid.integrations.llama_index import GaugidMemoryBlock
        
        memory_block = GaugidMemoryBlock(
            name="user_preferences",
            connection_token="gaugid_conn_xxx",
            memory_type="semantic"
        )
        
        memory = Memory(
            memory_blocks=[memory_block],
            session_id="user-123"
        )
        ```
    
    Based on: https://github.com/run-llama/llama_index/blob/main/llama-index-core/llama_index/core/memory/memory.py
    """
    
    def __init__(
        self,
        name: str,
        connection_token: str,
        description: Optional[str] = None,
        priority: int = 0,
        accept_short_term_memory: bool = True,
        api_url: Optional[str] = None,
        memory_type: str = "semantic",
    ):
        """
        Initialize GaugidMemoryBlock.
        
        Args:
            name: Name/identifier of the memory block
            connection_token: Gaugid connection token for authentication
            description: Optional description of the memory block
            priority: Priority of this memory block (0 = never truncate, 1 = highest priority)
            accept_short_term_memory: Whether to accept messages from short-term memory
            api_url: Optional Gaugid API URL (defaults to production)
            memory_type: Memory type to use ("episodic", "semantic", or "procedural")
        """
        if not LLAMA_INDEX_AVAILABLE:
            raise ImportError(
                "LlamaIndex is not installed. Install with: pip install gaugid[llama-index]"
            )
        
        super().__init__(
            name=name,
            description=description or f"Gaugid memory block: {name}",
            priority=priority,
            accept_short_term_memory=accept_short_term_memory,
        )
        
        self.client = GaugidClient(connection_token=connection_token, api_url=api_url)
        self.memory_type = memory_type
        self._client_initialized = False
    
    async def _ensure_client_ready(self) -> None:
        """Ensure the client is ready."""
        if not self._client_initialized:
            self._client_initialized = True
    
    def _name_to_category(self) -> str:
        """Convert memory block name to Gaugid category."""
        return f"a2p:llama_index:memory_block:{self.name}"
    
    async def _aget(
        self,
        messages: Optional[List[ChatMessage]] = None,
        **block_kwargs: Any,
    ) -> str:
        """
        Pull the memory block content.
        
        Args:
            messages: Optional list of chat messages (for context)
            **block_kwargs: Additional keyword arguments
            
        Returns:
            Memory block content as a string
        """
        await self._ensure_client_ready()
        
        # Get profile with relevant scopes
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        
        # Find memory for this block
        memories = profile.get("memories", {}).get(self.memory_type, [])
        category = self._name_to_category()
        
        for memory in memories:
            if memory.get("category") == category:
                return memory.get("content", "")
        
        # Return empty string if no memory found
        return ""
    
    async def _aput(self, messages: List[ChatMessage]) -> None:
        """
        Push messages to the memory block.
        
        Args:
            messages: List of chat messages to store
        """
        await self._ensure_client_ready()
        
        if not messages:
            return
        
        # Convert messages to text content
        # Format: role: content for each message
        content_parts = []
        for message in messages:
            role = getattr(message, 'role', 'unknown')
            content = getattr(message, 'content', '')
            
            # Handle different content types
            if isinstance(content, str):
                text_content = content
            elif isinstance(content, list):
                # Extract text from content blocks
                text_parts = []
                for block in content:
                    if hasattr(block, 'text'):
                        text_parts.append(block.text)
                    elif isinstance(block, dict) and 'text' in block:
                        text_parts.append(block['text'])
                text_content = " ".join(text_parts)
            else:
                text_content = str(content)
            
            content_parts.append(f"{role}: {text_content}")
        
        # Combine all messages
        combined_content = "\n".join(content_parts)
        
        # Get existing content
        existing_content = await self._aget()
        
        # Append or replace based on block configuration
        if existing_content:
            # Append to existing content
            new_content = f"{existing_content}\n\n{combined_content}"
        else:
            new_content = combined_content
        
        # Store in Gaugid
        category = self._name_to_category()
        await self.client.propose_memory(
            content=new_content,
            category=category,
            memory_type=self.memory_type,
            confidence=0.8,
            context=f"LlamaIndex memory block: {self.name}",
        )
    
    async def atruncate(
        self,
        content: str,
        tokens_to_truncate: int,
    ) -> Optional[str]:
        """
        Truncate the memory block content.
        
        Args:
            content: Current content of the memory block
            tokens_to_truncate: Number of tokens to truncate
            
        Returns:
            Truncated content or None if completely truncated
        """
        await self._ensure_client_ready()
        
        # Simple truncation: remove from the beginning (oldest content)
        # In production, you might want more sophisticated truncation
        if not content:
            return None
        
        # Estimate tokens (rough: 1 token ≈ 4 characters)
        estimated_tokens = len(content) // 4
        
        if estimated_tokens <= tokens_to_truncate:
            return None
        
        # Remove oldest content (from beginning)
        chars_to_remove = tokens_to_truncate * 4
        truncated = content[chars_to_remove:]
        
        # Update in Gaugid
        category = self._name_to_category()
        await self.client.propose_memory(
            content=truncated,
            category=category,
            memory_type=self.memory_type,
            confidence=0.8,
            context=f"LlamaIndex memory block truncated: {self.name}",
        )
        
        return truncated
    
    async def clear(self) -> None:
        """Clear the memory block content."""
        await self._ensure_client_ready()
        
        # Note: Gaugid doesn't support deletion yet
        # We'll create an empty memory to "clear" the block
        category = self._name_to_category()
        await self.client.propose_memory(
            content="",
            category=category,
            memory_type=self.memory_type,
            confidence=0.9,
            context=f"LlamaIndex memory block cleared: {self.name}",
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
