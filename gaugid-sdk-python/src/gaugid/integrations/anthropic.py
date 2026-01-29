"""
GaugidMemoryTool - Anthropic Memory Tool backend using Gaugid SDK

This module provides a BetaAbstractMemoryTool implementation for Anthropic's
memory tool that uses Gaugid profiles as the persistent memory store. This
allows Claude to store and retrieve information across conversations using
Gaugid profiles instead of local files.

Based on: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool

Example:
    ```python
    from anthropic import Anthropic
    from anthropic.beta.tools.memory import BetaAbstractMemoryTool
    from gaugid.integrations.anthropic import GaugidMemoryTool
    
    # Create memory tool with Gaugid backend
    memory_tool = GaugidMemoryTool(
        connection_token="gaugid_conn_xxx",
        namespace_prefix="claude"
    )
    
    # Use with Anthropic client
    client = Anthropic()
    response = client.beta.messages.create(
        model="claude-sonnet-4-5",
        messages=[...],
        tools=[memory_tool],
        betas=["context-management-2025-06-27"]
    )
    ```
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from anthropic.beta.tools.memory import BetaAbstractMemoryTool
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    # Create minimal stub for type checking
    class BetaAbstractMemoryTool:
        pass

from gaugid.client import GaugidClient


class GaugidMemoryTool(BetaAbstractMemoryTool):
    """
    Anthropic Memory Tool backend using Gaugid SDK.
    
    This tool allows Claude to use Gaugid profiles as its persistent memory
    store. Memory operations (view, write, edit, delete, rename) are mapped
    to Gaugid memories, allowing Claude to build knowledge over time using
    user-controlled, persistent storage.
    
    The `/memories` directory structure is mapped to Gaugid memory categories,
    and file contents are stored as memory content.
    
    Example:
        ```python
        from anthropic import Anthropic
        from gaugid.integrations.anthropic import GaugidMemoryTool
        
        memory_tool = GaugidMemoryTool(
            connection_token="gaugid_conn_xxx",
            namespace_prefix="claude"
        )
        
        client = Anthropic()
        response = client.beta.messages.create(
            model="claude-sonnet-4-5",
            messages=[{"role": "user", "content": "Remember that I prefer dark mode."}],
            tools=[memory_tool],
            betas=["context-management-2025-06-27"]
        )
        ```
    
    Based on: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
    """
    
    def __init__(
        self,
        connection_token: str,
        namespace_prefix: str = "claude",
        api_url: Optional[str] = None,
        memory_type: str = "episodic",
    ):
        """
        Initialize GaugidMemoryTool.
        
        Args:
            connection_token: Gaugid connection token for authentication
            namespace_prefix: Prefix for memory categories (default: "claude")
            api_url: Optional Gaugid API URL (defaults to production)
            memory_type: Memory type to use ("episodic", "semantic", or "procedural")
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic SDK is not installed. Install with: pip install gaugid[anthropic]"
            )
        
        super().__init__()
        self.client = GaugidClient(connection_token=connection_token, api_url=api_url)
        self.namespace_prefix = namespace_prefix
        self.memory_type = memory_type
        self._client_initialized = False
    
    async def _ensure_client_ready(self) -> None:
        """Ensure the client is ready."""
        if not self._client_initialized:
            self._client_initialized = True
    
    def _path_to_category(self, path: str) -> str:
        """Convert memory file path to Gaugid category."""
        # Normalize path: /memories/file.txt -> claude:memories:file.txt
        if path.startswith("/memories/"):
            path = path[10:]  # Remove /memories/
        elif path == "/memories":
            path = ""
        
        # Convert to category format
        parts = [self.namespace_prefix, "memories"]
        if path:
            # Replace / with : and remove file extension for category
            path_parts = path.split("/")
            parts.extend(path_parts)
        
        return ":".join(parts)
    
    def _category_to_path(self, category: str) -> str:
        """Convert Gaugid category to memory file path."""
        if not category.startswith(f"{self.namespace_prefix}:memories:"):
            return None
        
        # Extract path from category
        path_parts = category.replace(f"{self.namespace_prefix}:memories:", "").split(":")
        if not path_parts or path_parts == [""]:
            return "/memories"
        
        return f"/memories/{'/'.join(path_parts)}"
    
    def _validate_path(self, path: str) -> bool:
        """Validate that path is within /memories directory."""
        # Security: Prevent directory traversal
        if not path.startswith("/memories"):
            return False
        
        # Check for traversal patterns
        if ".." in path or "../" in path or "..\\" in path:
            return False
        
        # Resolve to canonical path
        try:
            resolved = Path(path).resolve()
            # Ensure it's still within /memories
            memories_path = Path("/memories").resolve()
            return str(resolved).startswith(str(memories_path))
        except Exception:
            return False
    
    async def view(self, path: str, view_range: Optional[List[int]] = None) -> str:
        """
        View directory contents or file contents.
        
        Args:
            path: Path to view (directory or file)
            view_range: Optional line range [start, end] for file viewing
            
        Returns:
            Directory listing or file contents
        """
        await self._ensure_client_ready()
        
        if not self._validate_path(path):
            return f"Error: Invalid path {path}. Path must be within /memories directory."
        
        # Get profile with relevant scopes
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        
        memories = profile.get("memories", {}).get(self.memory_type, [])
        
        # Check if path is a directory (ends with / or is /memories)
        if path == "/memories" or path.endswith("/"):
            # Return directory listing
            category_prefix = self._path_to_category(path.rstrip("/"))
            matching_memories = []
            
            for memory in memories:
                category = memory.get("category", "")
                if category.startswith(category_prefix):
                    matching_memories.append(memory)
            
            if not matching_memories:
                return f"Here're the files and directories up to 2 levels deep in {path}, excluding hidden items and node_modules:\n0\t{path}\n(empty directory)"
            
            # Build directory listing
            lines = [f"Here're the files and directories up to 2 levels deep in {path}, excluding hidden items and node_modules:"]
            seen_paths = set()
            
            for memory in matching_memories:
                category = memory.get("category", "")
                file_path = self._category_to_path(category)
                if file_path and file_path not in seen_paths:
                    # Extract filename
                    filename = file_path.split("/")[-1]
                    content = memory.get("content", "")
                    size = len(content.encode('utf-8'))
                    lines.append(f"{size}\t{file_path}")
                    seen_paths.add(file_path)
            
            return "\n".join(lines)
        else:
            # Return file contents
            category = self._path_to_category(path)
            
            for memory in memories:
                if memory.get("category") == category:
                    content = memory.get("content", "")
                    
                    # Apply line range if specified
                    if view_range and len(view_range) == 2:
                        lines = content.split("\n")
                        start, end = view_range[0] - 1, view_range[1]  # Convert to 0-indexed
                        selected_lines = lines[start:end]
                        content = "\n".join(selected_lines)
                    
                    return f"Here's the content of {path} with line numbers:\n" + "\n".join(
                        f"{i+1:6}\t{line}" for i, line in enumerate(content.split("\n"))
                    )
            
            return f"Error: The path {path} does not exist"
    
    async def write(self, path: str, content: str) -> str:
        """
        Write content to a file.
        
        Args:
            path: File path
            content: Content to write
            
        Returns:
            Success message
        """
        await self._ensure_client_ready()
        
        if not self._validate_path(path):
            return f"Error: Invalid path {path}. Path must be within /memories directory."
        
        # Check if file already exists
        category = self._path_to_category(path)
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        memories = profile.get("memories", {}).get(self.memory_type, [])
        
        for memory in memories:
            if memory.get("category") == category:
                return f"Error: The destination {path} already exists"
        
        # Create new memory
        await self.client.propose_memory(
            content=content,
            category=category,
            memory_type=self.memory_type,
            confidence=0.9,
            context=f"Claude memory tool: {path}",
        )
        
        return f"The file {path} has been created."
    
    async def edit(self, path: str, old_str: str, new_str: str) -> str:
        """
        Edit file by replacing old_str with new_str.
        
        Args:
            path: File path
            old_str: Text to replace
            new_str: Replacement text
            
        Returns:
            Success message
        """
        await self._ensure_client_ready()
        
        if not self._validate_path(path):
            return f"Error: Invalid path {path}. Path must be within /memories directory."
        
        category = self._path_to_category(path)
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        memories = profile.get("memories", {}).get(self.memory_type, [])
        
        for memory in memories:
            if memory.get("category") == category:
                content = memory.get("content", "")
                
                if old_str not in content:
                    # Find line numbers where old_str appears
                    lines = content.split("\n")
                    line_numbers = [i + 1 for i, line in enumerate(lines) if old_str in line]
                    if line_numbers:
                        return f"Error: Could not find the exact string `{old_str}` in lines: {line_numbers}. Please ensure it is unique"
                    return f"Error: Could not find the exact string `{old_str}` in {path}. Please ensure it is unique"
                
                # Replace old_str with new_str
                new_content = content.replace(old_str, new_str, 1)  # Replace first occurrence
                
                # Update memory (propose new version)
                await self.client.propose_memory(
                    content=new_content,
                    category=category,
                    memory_type=self.memory_type,
                    confidence=0.9,
                    context=f"Claude memory tool edit: {path}",
                )
                
                return f"The file {path} has been edited."
        
        return f"Error: The path {path} does not exist"
    
    async def insert(self, path: str, insert_line: int, insert_text: str) -> str:
        """
        Insert text at a specific line.
        
        Args:
            path: File path
            insert_line: Line number to insert at (1-indexed)
            insert_text: Text to insert
            
        Returns:
            Success message
        """
        await self._ensure_client_ready()
        
        if not self._validate_path(path):
            return f"Error: Invalid path {path}. Path must be within /memories directory."
        
        category = self._path_to_category(path)
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        memories = profile.get("memories", {}).get(self.memory_type, [])
        
        for memory in memories:
            if memory.get("category") == category:
                content = memory.get("content", "")
                lines = content.split("\n")
                n_lines = len(lines)
                
                if insert_line < 0 or insert_line > n_lines:
                    return f"Error: Invalid `insert_line` parameter: {insert_line}. It should be within the range of lines of the file: [0, {n_lines}]"
                
                # Insert text
                lines.insert(insert_line, insert_text.rstrip("\n"))
                new_content = "\n".join(lines)
                
                # Update memory
                await self.client.propose_memory(
                    content=new_content,
                    category=category,
                    memory_type=self.memory_type,
                    confidence=0.9,
                    context=f"Claude memory tool insert: {path}",
                )
                
                return f"The file {path} has been edited."
        
        return f"Error: The path {path} does not exist"
    
    async def delete(self, path: str) -> str:
        """
        Delete a file or directory.
        
        Note: Gaugid doesn't support memory deletion via API yet.
        This returns a success message but doesn't actually delete.
        
        Args:
            path: Path to delete
            
        Returns:
            Success message
        """
        await self._ensure_client_ready()
        
        if not self._validate_path(path):
            return f"Error: Invalid path {path}. Path must be within /memories directory."
        
        category = self._path_to_category(path)
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        memories = profile.get("memories", {}).get(self.memory_type, [])
        
        # Check if exists
        exists = any(m.get("category") == category for m in memories)
        if not exists:
            return f"Error: The path {path} does not exist"
        
        # Note: Gaugid doesn't support deletion yet
        # Return success but note that deletion is not yet supported
        return f"Note: Memory deletion is not yet supported by Gaugid API. The path {path} would be deleted."
    
    async def rename(self, old_path: str, new_path: str) -> str:
        """
        Rename or move a file/directory.
        
        Args:
            old_path: Source path
            new_path: Destination path
            
        Returns:
            Success message
        """
        await self._ensure_client_ready()
        
        if not self._validate_path(old_path) or not self._validate_path(new_path):
            return f"Error: Invalid path. Paths must be within /memories directory."
        
        old_category = self._path_to_category(old_path)
        new_category = self._path_to_category(new_path)
        
        profile = await self.client.get_profile(
            scopes=[f"a2p:{self.memory_type}"]
        )
        memories = profile.get("memories", {}).get(self.memory_type, [])
        
        # Check if source exists
        source_memory = None
        for memory in memories:
            if memory.get("category") == old_category:
                source_memory = memory
                break
        
        if not source_memory:
            return f"Error: The path {old_path} does not exist"
        
        # Check if destination exists
        for memory in memories:
            if memory.get("category") == new_category:
                return f"Error: The destination {new_path} already exists"
        
        # Create new memory with new category (rename)
        await self.client.propose_memory(
            content=source_memory.get("content", ""),
            category=new_category,
            memory_type=self.memory_type,
            confidence=0.9,
            context=f"Claude memory tool rename: {old_path} -> {new_path}",
        )
        
        return f"Successfully renamed {old_path} to {new_path}"
